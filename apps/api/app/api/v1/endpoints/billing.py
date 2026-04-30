from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.core.pricing import (
    AI_TOKEN_CAPS,
    CYCLE_DISCOUNTS,
    MODULE_PRICES,
    PACKAGES,
    ai_cap_for_tier,
    calc_subscription_price,
)
from app.models.billing import Invoice, Subscription
from app.schemas.billing import (
    BillingStatusResponse,
    CatalogModule,
    CatalogResponse,
    InvoiceOut,
    PriceQuoteRequest,
    PriceQuoteResponse,
    SubscriptionChangeRequest,
    SubscriptionOut,
)
from app.services import audit_service, billing_service, email_service, invoice_pdf
from app.services.billing_service import GraceState, evaluate_grace

router = APIRouter()

MODULE_LABELS = {
    "crm": "CRM",
    "smm": "SMM",
    "ads": "Reklama",
    "inbox": "Inbox",
    "reports": "Hisobotlar",
    "integrations": "Integratsiyalar",
}


@router.get("/catalog", response_model=CatalogResponse)
async def catalog() -> CatalogResponse:
    """Public-shape catalog used by the billing UI to render plan options."""
    return CatalogResponse(
        modules=[
            CatalogModule(key=k, label=MODULE_LABELS[k], prices=v) for k, v in MODULE_PRICES.items()
        ],
        packages={k: dict(v) for k, v in PACKAGES.items()},
        cycle_discounts=dict(CYCLE_DISCOUNTS),
        ai_token_caps=dict(AI_TOKEN_CAPS),
    )


@router.post("/quote", response_model=PriceQuoteResponse)
async def price_quote(
    payload: PriceQuoteRequest,
    _: CurrentUser = Depends(require_permission("billing.read")),
) -> PriceQuoteResponse:
    price, discount = calc_subscription_price(
        modules=list(payload.modules),
        tier=payload.tier,
        package=payload.package,
        billing_cycle_months=payload.billing_cycle_months,
    )
    return PriceQuoteResponse(
        price_total=price,
        discount_percent=discount,
        ai_token_cap_monthly=ai_cap_for_tier(payload.tier),
    )


@router.get("/status", response_model=BillingStatusResponse)
async def billing_status(
    _: CurrentUser = Depends(require_permission("billing.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> BillingStatusResponse:
    sub = await billing_service.current_subscription(db)
    state = evaluate_grace(sub)
    now = datetime.now(UTC)
    days_until = days_past = None
    if sub is not None:
        if sub.expires_at >= now:
            days_until = (sub.expires_at - now).days
        else:
            days_past = (now - sub.expires_at).days
    return BillingStatusResponse(
        subscription=SubscriptionOut.model_validate(sub) if sub else None,
        grace_state=state.value,
        days_until_expiry=days_until,
        days_past_expiry=days_past,
    )


@router.post("/start-trial", response_model=SubscriptionOut, status_code=201)
async def start_trial(
    request: Request,
    current: CurrentUser = Depends(require_permission("billing.update")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Subscription:
    existing = await billing_service.current_subscription(db)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Subscription already exists")
    sub = await billing_service.start_trial(db)
    await audit_service.record(
        db,
        user_id=current.id,
        action="billing.trial_started",
        resource_type="subscription",
        resource_id=str(sub.id),
        request=request,
    )
    await db.commit()
    return sub


@router.post("/subscribe", response_model=InvoiceOut, status_code=201)
async def subscribe(
    payload: SubscriptionChangeRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("billing.update")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Invoice:
    sub, invoice = await billing_service.change_subscription(
        db,
        modules=list(payload.modules),
        tier=payload.tier,
        package=payload.package,
        billing_cycle_months=payload.billing_cycle_months,
    )
    await audit_service.record(
        db,
        user_id=current.id,
        action="billing.subscribe",
        resource_type="subscription",
        resource_id=str(sub.id),
        metadata={
            "tier": payload.tier,
            "package": payload.package,
            "modules": list(payload.modules),
            "cycle_months": payload.billing_cycle_months,
            "amount": invoice.amount,
        },
        request=request,
    )
    await db.commit()

    await email_service.send_invoice_email(
        to=current.user.email,
        invoice_number=invoice.invoice_number,
        amount=invoice.amount,
        due_at=invoice.due_at.strftime("%Y-%m-%d"),
    )
    return invoice


@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(
    _: CurrentUser = Depends(require_permission("billing.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[Invoice]:
    rows = (await db.execute(select(Invoice).order_by(Invoice.created_at.desc()))).scalars()
    return list(rows)


@router.get("/invoices/{invoice_id}/pdf")
async def invoice_pdf_download(
    invoice_id: UUID,
    current: CurrentUser = Depends(require_permission("billing.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Response:
    invoice = await db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    sub = await db.get(Subscription, invoice.subscription_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Subscription missing")
    pdf_bytes = invoice_pdf.render_invoice_pdf(invoice=invoice, sub=sub, tenant=current.tenant)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"'},
    )


@router.post("/invoices/{invoice_id}/mark-paid", response_model=InvoiceOut)
async def mark_invoice_paid(
    invoice_id: UUID,
    request: Request,
    current: CurrentUser = Depends(require_permission("billing.update")),
    db: AsyncSession = Depends(get_tenant_session),
) -> Invoice:
    try:
        invoice = await billing_service.mark_invoice_paid(db, invoice_id, current.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    sub = await db.get(Subscription, invoice.subscription_id)
    if sub is not None:
        # Extend the active subscription past the paid invoice's due window
        from datetime import timedelta

        sub.expires_at = max(sub.expires_at, datetime.now(UTC)) + timedelta(
            days=30 * sub.billing_cycle_months
        )

    await audit_service.record(
        db,
        user_id=current.id,
        action="billing.invoice_paid",
        resource_type="invoice",
        resource_id=str(invoice.id),
        metadata={"amount": invoice.amount},
        request=request,
    )
    await db.commit()
    return invoice


@router.get("/grace-state")
async def grace_state(
    _: CurrentUser = Depends(require_permission("billing.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict[str, str]:
    sub = await billing_service.current_subscription(db)
    state = evaluate_grace(sub)
    return {"state": state.value}


# Re-export so the audit endpoint can attribute actions
__all__ = ["GraceState", "router"]
