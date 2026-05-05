#!/usr/bin/env python3
"""Seed a staging/demo SMM tenant for Meta reviewer flows.

Creates or updates:
- public owner user with a known email/password
- tenant schema
- default brand with richer reviewer-facing fields
- sample brand assets
- sample content drafts
- sample content-plan items
- optional `meta_app` integration with app_id/app_secret only

Run from repo root or from `apps/api` via poetry:

    cd apps/api
    poetry run python ../../scripts/seed_smm_reviewer_demo.py --help
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

DEMO_DRAFTS: tuple[dict[str, str], ...] = (
    {
        "platform": "instagram",
        "title": "Reviewer demo - Instagram feed",
        "body": (
            "Bahor mavsumida mijozlar eng ko'p so'raydigan 3 xizmatni bir joyga jamladik. "
            "Tez bron qiling, joylar cheklangan. Savol bo'lsa DM yozing."
        ),
        "user_goal": "Instagram feed uchun qisqa promo post",
    },
    {
        "platform": "facebook",
        "title": "Reviewer demo - Facebook post",
        "body": (
            "Bu demo tenant Meta App Review oqimi uchun tayyorlangan. "
            "Reviewer Facebook Page'ni ulab, shu kabi tayyor kontentni publish qilishi mumkin."
        ),
        "user_goal": "Facebook uchun product demo post",
    },
)

DEMO_PLAN_ITEMS: tuple[dict[str, str], ...] = (
    {
        "platform": "instagram",
        "title": "Reviewer Day 1 - Feed post",
        "idea": "Asosiy xizmatlar bo'yicha qisqa promo, CTA bilan.",
        "goal": "Feed publish flow'ni ko'rsatish",
        "cta": "DM yoki bron linki",
    },
    {
        "platform": "facebook",
        "title": "Reviewer Day 2 - Page post",
        "idea": "Facebook Page uchun batafsil post va sharhga undov.",
        "goal": "Page posting capability'ni ko'rsatish",
        "cta": "Izoh qoldiring",
    },
    {
        "platform": "instagram",
        "title": "Reviewer Day 3 - Reels placeholder",
        "idea": "Reels uchun future test item, hozircha publish emas.",
        "goal": "Keyingi sprint formatlari uchun planning",
        "cta": "Saqlab qo'ying",
    },
)

DEMO_ASSETS: tuple[dict[str, object], ...] = (
    {
        "asset_type": "color",
        "name": "Primary Violet",
        "file_url": None,
        "content_type": None,
        "file_size": 0,
        "metadata": {"hex": "#7c3aed", "usage": "Primary brand color"},
        "is_primary": True,
    },
    {
        "asset_type": "reference",
        "name": "Reviewer Reference Board",
        "file_url": "https://nexusai.uz",
        "content_type": "text/uri-list",
        "file_size": 0,
        "metadata": {"note": "Demo reference link for reviewer walkthrough"},
        "is_primary": True,
    },
)


@lru_cache(maxsize=1)
def _deps() -> dict[str, object]:
    from sqlalchemy import select, text

    from app.core.db import dispose_engine, get_session_factory
    from app.core.security import hash_password
    from app.core.tenancy import validate_schema_name
    from app.models.smm import BrandAsset, ContentDraft, ContentPlanItem
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.services import (
        brand_asset_service,
        brand_service,
        content_plan_service,
        integration_service,
    )
    from app.services.tenant_service import (
        attach_owner_membership,
        create_tenant_schema,
        generate_unique_schema_name,
    )

    return {
        "BrandAsset": BrandAsset,
        "ContentDraft": ContentDraft,
        "ContentPlanItem": ContentPlanItem,
        "Tenant": Tenant,
        "User": User,
        "attach_owner_membership": attach_owner_membership,
        "brand_asset_service": brand_asset_service,
        "brand_service": brand_service,
        "content_plan_service": content_plan_service,
        "create_tenant_schema": create_tenant_schema,
        "dispose_engine": dispose_engine,
        "generate_unique_schema_name": generate_unique_schema_name,
        "get_session_factory": get_session_factory,
        "hash_password": hash_password,
        "integration_service": integration_service,
        "select": select,
        "text": text,
        "validate_schema_name": validate_schema_name,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="Reviewer demo owner login email")
    parser.add_argument("--password", required=True, help="Reviewer demo owner login password")
    parser.add_argument("--full-name", default="Meta Reviewer Demo")
    parser.add_argument("--phone", default="+998900000111")
    parser.add_argument("--company-name", default="Nexus AI Reviewer Demo")
    parser.add_argument("--industry", default="marketing-agentlik")
    parser.add_argument("--brand-name", default="Nexus AI Demo Brand")
    parser.add_argument("--app-base-url", default="http://127.0.0.1:3000")
    parser.add_argument("--meta-app-id", default="")
    parser.add_argument("--meta-app-secret", default="")
    return parser.parse_args()


async def ensure_owner(
    *,
    email: str,
    password: str,
    full_name: str,
    phone: str,
    company_name: str,
    industry: str,
) -> tuple[object, object, bool]:
    deps = _deps()
    user_model = deps["User"]
    tenant_model = deps["Tenant"]
    attach_owner_membership = deps["attach_owner_membership"]
    create_tenant_schema = deps["create_tenant_schema"]
    generate_unique_schema_name = deps["generate_unique_schema_name"]
    get_session_factory = deps["get_session_factory"]
    hash_password = deps["hash_password"]
    select = deps["select"]
    text = deps["text"]
    validate_schema_name = deps["validate_schema_name"]

    factory = get_session_factory()
    async with factory() as db:
        user = (
            (await db.execute(select(user_model).where(user_model.email == email)))
            .scalars()
            .first()
        )
        created = False

        if user is None:
            schema_name = await generate_unique_schema_name(db, company_name)
            tenant = tenant_model(
                name=company_name,
                schema_name=schema_name,
                industry=industry,
                phone=phone,
            )
            db.add(tenant)
            await db.flush()

            user = user_model(
                tenant_id=tenant.id,
                email=email,
                phone=phone,
                password_hash=hash_password(password),
                full_name=full_name,
                role="owner",
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(tenant)
            await db.refresh(user)
            await create_tenant_schema(db, tenant)
            await attach_owner_membership(db, tenant, user.id)
            created = True
        else:
            tenant = await db.get(tenant_model, user.tenant_id)
            if tenant is None:
                raise RuntimeError(f"Tenant not found for existing user {email}")
            user.password_hash = hash_password(password)
            user.full_name = full_name
            user.phone = phone
            user.is_active = True
            user.is_verified = True
            if not tenant.industry:
                tenant.industry = industry
            if not tenant.phone:
                tenant.phone = phone
            await db.commit()

            schema = validate_schema_name(tenant.schema_name)
            exists = await db.execute(
                text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema"),
                {"schema": schema},
            )
            if exists.first() is None:
                await create_tenant_schema(db, tenant)
                await attach_owner_membership(db, tenant, user.id)

        return user, tenant, created


async def ensure_brand_data(
    *,
    tenant_schema: str,
    user_id: object,
    brand_name: str,
    company_name: str,
    industry: str,
    meta_app_id: str,
    meta_app_secret: str,
) -> dict[str, object]:
    deps = _deps()
    brand_asset_model = deps["BrandAsset"]
    content_draft_model = deps["ContentDraft"]
    content_plan_item_model = deps["ContentPlanItem"]
    brand_asset_service = deps["brand_asset_service"]
    brand_service = deps["brand_service"]
    content_plan_service = deps["content_plan_service"]
    get_session_factory = deps["get_session_factory"]
    integration_service = deps["integration_service"]
    select = deps["select"]
    text = deps["text"]
    validate_schema_name = deps["validate_schema_name"]

    factory = get_session_factory()
    async with factory() as db:
        schema = validate_schema_name(tenant_schema)
        await db.execute(text(f"SET search_path TO {schema}, public"))
        try:
            brand = await brand_service.ensure_default_exists(
                db,
                fallback_name=brand_name,
                user_id=user_id,
            )
            brand.name = brand_name
            brand.description = (
                "Meta App Review va reviewer demo publish oqimi uchun tayyorlangan tenant."
            )
            brand.industry = industry
            brand.primary_color = "#7c3aed"
            brand.voice_tone = "Ishbilarmon, aniq, ishonchli"
            brand.target_audience = (
                "SMM operator, marketing menejer va Meta reviewer demo flow"
            )
            brand.languages = ["uz", "ru"]
            brand.logo_url = brand.logo_url or "https://nexusai.uz"
            await brand_asset_service.ensure_table(db)
            await content_plan_service.ensure_table(db)

            assets_created = 0
            for spec in DEMO_ASSETS:
                existing_asset = (
                    await db.execute(
                        select(brand_asset_model).where(
                            brand_asset_model.brand_id == brand.id,
                            brand_asset_model.name == str(spec["name"]),
                        )
                    )
                ).scalars().first()
                if existing_asset is not None:
                    continue
                await brand_asset_service.create_asset(
                    db,
                    brand_id=brand.id,
                    asset_type=str(spec["asset_type"]),
                    name=str(spec["name"]),
                    file_url=str(spec["file_url"]) if spec["file_url"] is not None else None,
                    content_type=str(spec["content_type"])
                    if spec["content_type"] is not None
                    else None,
                    file_size=int(spec["file_size"]),
                    metadata=dict(spec["metadata"]) if spec["metadata"] else None,
                    is_primary=bool(spec["is_primary"]),
                    user_id=user_id,
                )
                assets_created += 1

            drafts_created = 0
            for spec in DEMO_DRAFTS:
                existing_draft = (
                    await db.execute(
                        select(content_draft_model).where(
                            content_draft_model.brand_id == brand.id,
                            content_draft_model.title == spec["title"],
                            content_draft_model.platform == spec["platform"],
                        )
                    )
                ).scalars().first()
                if existing_draft is not None:
                    continue
                db.add(
                    content_draft_model(
                        brand_id=brand.id,
                        platform=spec["platform"],
                        title=spec["title"],
                        body=spec["body"],
                        user_goal=spec["user_goal"],
                        language="uz",
                        provider="seed",
                        model="manual",
                        tokens_used=0,
                        created_by=user_id,
                    )
                )
                drafts_created += 1

            plan_created = 0
            base_day = date.today()
            for idx, spec in enumerate(DEMO_PLAN_ITEMS):
                existing_item = (
                    await db.execute(
                        select(content_plan_item_model).where(
                            content_plan_item_model.brand_id == brand.id,
                            content_plan_item_model.title == spec["title"],
                            content_plan_item_model.platform == spec["platform"],
                        )
                    )
                ).scalars().first()
                if existing_item is not None:
                    continue
                await content_plan_service.create_item(
                    db,
                    brand_id=brand.id,
                    platform=spec["platform"],
                    title=spec["title"],
                    idea=spec["idea"],
                    goal=spec["goal"],
                    cta=spec["cta"],
                    status="idea" if idx == 2 else "approved",
                    planned_at=datetime.combine(
                        base_day + timedelta(days=idx),
                        time(hour=10 + idx, minute=0, tzinfo=UTC),
                    ),
                    source="seed",
                    sort_order=idx,
                    metadata={"seed": "reviewer-demo", "company_name": company_name},
                    user_id=user_id,
                )
                plan_created += 1

            meta_connected = False
            if meta_app_id and meta_app_secret:
                await integration_service.upsert(
                    db,
                    provider="meta_app",
                    credentials={"app_id": meta_app_id, "app_secret": meta_app_secret},
                    user_id=user_id,
                    label="Reviewer staging",
                    metadata={"seed": "reviewer-demo"},
                )
                meta_connected = True

            await db.commit()
            return {
                "brand_id": str(brand.id),
                "brand_name": brand.name,
                "assets_created": assets_created,
                "drafts_created": drafts_created,
                "plan_created": plan_created,
                "meta_connected": meta_connected,
            }
        finally:
            await db.execute(text("SET search_path TO public"))
            await db.commit()


async def amain() -> int:
    args = parse_args()
    try:
        user, tenant, created = await ensure_owner(
            email=args.email.strip().lower(),
            password=args.password,
            full_name=args.full_name.strip(),
            phone=args.phone.strip(),
            company_name=args.company_name.strip(),
            industry=args.industry.strip(),
        )
        brand = await ensure_brand_data(
            tenant_schema=tenant.schema_name,
            user_id=user.id,
            brand_name=args.brand_name.strip(),
            company_name=args.company_name.strip(),
            industry=args.industry.strip(),
            meta_app_id=args.meta_app_id.strip(),
            meta_app_secret=args.meta_app_secret.strip(),
        )

        print("Reviewer demo tenant tayyorlandi.")
        print(f"created_user={created}")
        print(f"tenant_name={tenant.name}")
        print(f"tenant_schema={tenant.schema_name}")
        print(f"login_email={user.email}")
        print(f"login_password={args.password}")
        print(f"brand_name={brand['brand_name']}")
        print(f"brand_id={brand['brand_id']}")
        print(f"assets_created={brand['assets_created']}")
        print(f"drafts_created={brand['drafts_created']}")
        print(f"plan_created={brand['plan_created']}")
        print(f"meta_app_seeded={brand['meta_connected']}")
        print(f"web_login_url={args.app_base_url.rstrip('/')}/login")
        print(f"integrations_url={args.app_base_url.rstrip('/')}/settings/integrations")
        print(f"social_url={args.app_base_url.rstrip('/')}/smm/social")
        print(f"posts_url={args.app_base_url.rstrip('/')}/smm/posts")
        return 0
    finally:
        if _deps.cache_info().currsize > 0:
            await _deps()["dispose_engine"]()


def main() -> int:
    return asyncio.run(amain())


if __name__ == "__main__":
    raise SystemExit(main())
