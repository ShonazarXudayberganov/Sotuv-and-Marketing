from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_tenant_session, require_permission
from app.schemas.inbox import (
    AutoReplyConfigOut,
    AutoReplyConfigPatch,
    AutoReplyDraft,
    ConversationOut,
    InboxStats,
    IngestInboundRequest,
    MessageOut,
    SeedResult,
    SendMessageRequest,
    StatusUpdate,
)
from app.services import audit_service, auto_reply_service, inbox_ingest, inbox_service

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    status: str | None = None,
    channel: str | None = None,
    contact_id: UUID | None = None,
    limit: int = 50,
    _: CurrentUser = Depends(require_permission("inbox.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[ConversationOut]:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    rows = await inbox_service.list_conversations(
        db,
        status=status,
        channel=channel,
        contact_id=contact_id,
        limit=limit,
    )
    return [ConversationOut.model_validate(r) for r in rows]


@router.get("/stats", response_model=InboxStats)
async def inbox_stats(
    _: CurrentUser = Depends(require_permission("inbox.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> InboxStats:
    return InboxStats.model_validate(await inbox_service.stats(db))


@router.get("/conversations/{cid}", response_model=ConversationOut)
async def get_conversation(
    cid: UUID,
    _: CurrentUser = Depends(require_permission("inbox.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ConversationOut:
    rec = await inbox_service.get_conversation(db, cid)
    if rec is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut.model_validate(rec)


@router.get("/conversations/{cid}/messages", response_model=list[MessageOut])
async def list_messages(
    cid: UUID,
    limit: int = 100,
    _: CurrentUser = Depends(require_permission("inbox.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[MessageOut]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    rows = await inbox_service.list_messages(db, cid, limit=limit)
    return [MessageOut.model_validate(r) for r in rows]


@router.post(
    "/conversations/{cid}/messages",
    response_model=MessageOut,
    status_code=201,
)
async def send_message(
    cid: UUID,
    payload: SendMessageRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("inbox.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageOut:
    conv = await inbox_service.get_conversation(db, cid)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        msg = await inbox_service.send_outbound(
            db,
            conversation=conv,
            body=payload.body,
            sent_by_user_id=current.id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await audit_service.record(
        db,
        user_id=current.id,
        action="inbox.send",
        resource_type="conversation",
        resource_id=str(cid),
        request=request,
    )
    response = MessageOut.model_validate(msg)
    await db.commit()
    return response


@router.post("/conversations/{cid}/read", response_model=ConversationOut)
async def mark_read(
    cid: UUID,
    _: CurrentUser = Depends(require_permission("inbox.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ConversationOut:
    rec = await inbox_service.mark_read(db, cid)
    if rec is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    response = ConversationOut.model_validate(rec)
    await db.commit()
    return response


@router.post("/conversations/{cid}/status", response_model=ConversationOut)
async def update_status(
    cid: UUID,
    payload: StatusUpdate,
    request: Request,
    current: CurrentUser = Depends(require_permission("inbox.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> ConversationOut:
    try:
        rec = await inbox_service.set_status(db, cid, status=payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if rec is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await audit_service.record(
        db,
        user_id=current.id,
        action="inbox.status",
        resource_type="conversation",
        resource_id=str(cid),
        metadata={"status": payload.status},
        request=request,
    )
    response = ConversationOut.model_validate(rec)
    await db.commit()
    return response


@router.post("/conversations/{cid}/draft-reply", response_model=AutoReplyDraft)
async def draft_reply(
    cid: UUID,
    _: CurrentUser = Depends(require_permission("inbox.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AutoReplyDraft:
    """Generate (but DON'T send) an AI auto-reply draft for the latest inbound msg."""
    conv = await inbox_service.get_conversation(db, cid)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await inbox_service.list_messages(db, cid, limit=20)
    last_inbound = next(
        (m for m in reversed(messages) if m.direction == "in"), None
    )
    if last_inbound is None:
        raise HTTPException(status_code=400, detail="No inbound message to reply to")
    draft = await auto_reply_service.draft_reply(
        db, conversation=conv, incoming=last_inbound
    )
    return AutoReplyDraft(
        reply=draft.reply, confidence=draft.confidence, mocked=draft.mocked
    )


@router.post("/ingest", response_model=MessageOut, status_code=201)
async def ingest_inbound(
    payload: IngestInboundRequest,
    request: Request,
    current: CurrentUser = Depends(require_permission("inbox.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> MessageOut:
    """Manual ingestion endpoint — used by webhooks once they're wired."""
    if payload.channel not in {"telegram", "instagram", "facebook", "email", "web_widget"}:
        raise HTTPException(status_code=400, detail="Unsupported channel")
    _, msg, _auto = await inbox_ingest.ingest_inbound(
        db,
        channel=payload.channel,
        external_id=payload.external_id,
        body=payload.body,
        title=payload.title,
        contact_id=payload.contact_id,
        brand_id=payload.brand_id,
        metadata=payload.metadata,
        auto_reply=payload.auto_reply,
    )
    await audit_service.record(
        db,
        user_id=current.id,
        action="inbox.ingest",
        resource_type="conversation",
        resource_id=str(msg.conversation_id),
        metadata={"channel": payload.channel},
        request=request,
    )
    response = MessageOut.model_validate(msg)
    await db.commit()
    return response


@router.post("/seed-mock", response_model=SeedResult)
async def seed_mock(
    request: Request,
    brand_id: UUID | None = None,
    current: CurrentUser = Depends(require_permission("inbox.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> SeedResult:
    inserted = await inbox_ingest.seed_mock_conversations(db, brand_id=brand_id)
    await audit_service.record(
        db,
        user_id=current.id,
        action="inbox.seed_mock",
        resource_type="inbox",
        metadata={"inserted": inserted},
        request=request,
    )
    await db.commit()
    return SeedResult(inserted=inserted)


# ─────────── Auto-reply config ───────────


@router.get("/auto-reply", response_model=AutoReplyConfigOut)
async def get_auto_reply(
    _: CurrentUser = Depends(require_permission("inbox.read")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AutoReplyConfigOut:
    cfg = await inbox_service.get_auto_reply_config(db)
    response = AutoReplyConfigOut.model_validate(cfg)
    await db.commit()
    return response


@router.patch("/auto-reply", response_model=AutoReplyConfigOut)
async def update_auto_reply(
    payload: AutoReplyConfigPatch,
    request: Request,
    current: CurrentUser = Depends(require_permission("inbox.write")),
    db: AsyncSession = Depends(get_tenant_session),
) -> AutoReplyConfigOut:
    cfg = await inbox_service.update_auto_reply_config(
        db, payload=payload.model_dump(exclude_unset=True)
    )
    await audit_service.record(
        db,
        user_id=current.id,
        action="inbox.auto_reply.update",
        resource_type="inbox",
        metadata=payload.model_dump(exclude_unset=True),
        request=request,
    )
    response = AutoReplyConfigOut.model_validate(cfg)
    await db.commit()
    return response
