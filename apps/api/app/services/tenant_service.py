"""Tenant lifecycle: create schema, install per-tenant tables, seed roles."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import STANDARD_ROLES
from app.core.tenancy import slugify_schema, validate_schema_name
from app.models.tenant import Tenant
from app.models.tenant_scoped import Role, UserMembership

# Tables that live in *every* tenant schema. We use raw DDL (instead of Alembic)
# because tenant schemas are created at runtime, not at migration time.
TENANT_DDL: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS departments (
        id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name         varchar(100) NOT NULL,
        parent_id    uuid REFERENCES departments(id) ON DELETE SET NULL,
        head_user_id varchar(36),
        description  varchar(500),
        sort_order   integer NOT NULL DEFAULT 0,
        is_active    boolean NOT NULL DEFAULT true,
        created_at   timestamptz NOT NULL DEFAULT now(),
        updated_at   timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS roles (
        id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name        varchar(50) NOT NULL,
        slug        varchar(50) NOT NULL UNIQUE,
        description varchar(500),
        is_system   boolean NOT NULL DEFAULT false,
        permissions jsonb NOT NULL DEFAULT '[]'::jsonb,
        created_at  timestamptz NOT NULL DEFAULT now(),
        updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_memberships (
        id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id       uuid NOT NULL,
        department_id uuid REFERENCES departments(id) ON DELETE SET NULL,
        role_id       uuid NOT NULL REFERENCES roles(id),
        is_primary    boolean NOT NULL DEFAULT false,
        invited_by    uuid,
        created_at    timestamptz NOT NULL DEFAULT now(),
        updated_at    timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_user_dept UNIQUE (user_id, department_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_user_memberships_user_id
        ON user_memberships(user_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id    uuid NOT NULL,
        title      varchar(200) NOT NULL,
        body       text,
        category   varchar(50) NOT NULL,
        severity   varchar(20) NOT NULL DEFAULT 'info',
        payload    jsonb,
        read_at    timestamptz,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_notifications_user_id
        ON notifications(user_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_log (
        id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id       uuid,
        action        varchar(100) NOT NULL,
        resource_type varchar(50) NOT NULL,
        resource_id   varchar(64),
        metadata      jsonb,
        ip_address    varchar(45),
        user_agent    varchar(500),
        created_at    timestamptz NOT NULL DEFAULT now(),
        updated_at    timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_audit_log_user_id ON audit_log(user_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_audit_log_action ON audit_log(action)
    """,
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name                  varchar(100) NOT NULL,
        key_prefix            varchar(12) NOT NULL,
        key_hash              varchar(255) NOT NULL,
        created_by            uuid NOT NULL,
        scopes                jsonb NOT NULL DEFAULT '[]'::jsonb,
        rate_limit_per_minute integer NOT NULL DEFAULT 60,
        expires_at            timestamptz,
        last_used_at          timestamptz,
        revoked_at            timestamptz,
        created_at            timestamptz NOT NULL DEFAULT now(),
        updated_at            timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_api_keys_prefix ON api_keys(key_prefix)
    """,
)


async def schema_name_available(session: AsyncSession, schema_name: str) -> bool:
    result = await session.execute(
        text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :s"),
        {"s": schema_name},
    )
    return result.first() is None


async def generate_unique_schema_name(session: AsyncSession, company_name: str) -> str:
    base = slugify_schema(company_name)
    candidate = base
    suffix = 0
    while not await schema_name_available(session, candidate):
        suffix += 1
        candidate = f"{base}_{suffix}"
    return candidate


async def create_tenant_schema(session: AsyncSession, tenant: Tenant) -> None:
    """Create the tenant's schema, install standard tables, and seed default roles.

    Idempotent: safe to re-run for self-healing on dev resets.
    """
    schema = validate_schema_name(tenant.schema_name)
    await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    await session.execute(text(f"SET search_path TO {schema}, public"))

    for ddl in TENANT_DDL:
        await session.execute(text(ddl))

    # Seed standard roles if absent
    existing = await session.execute(text("SELECT slug FROM roles"))
    seeded = {row[0] for row in existing.all()}
    for role in STANDARD_ROLES:
        slug = str(role["slug"])
        if slug in seeded:
            continue
        perms = role["permissions"]
        assert isinstance(perms, list)
        session.add(
            Role(
                name=str(role["name"]),
                slug=slug,
                description=str(role["description"]) if role.get("description") else None,
                is_system=bool(role["is_system"]),
                permissions=list(perms),
            )
        )

    await session.commit()
    # Reset search_path for the rest of the session (we're inside the public-DB flow)
    await session.execute(text("SET search_path TO public"))


async def attach_owner_membership(session: AsyncSession, tenant: Tenant, user_id: UUID) -> None:
    """Run inside the tenant schema. Creates the Owner UserMembership row."""
    schema = validate_schema_name(tenant.schema_name)
    await session.execute(text(f"SET search_path TO {schema}, public"))

    role = (
        await session.execute(text("SELECT id FROM roles WHERE slug = 'owner' LIMIT 1"))
    ).first()
    if role is None:
        raise RuntimeError(f"Owner role missing in {schema} — seed failed")

    existing = await session.execute(
        text("SELECT 1 FROM user_memberships WHERE user_id = :u AND department_id IS NULL"),
        {"u": str(user_id)},
    )
    if existing.first() is None:
        session.add(
            UserMembership(
                user_id=user_id,
                role_id=role[0],
                is_primary=True,
            )
        )
    await session.commit()
    await session.execute(text("SET search_path TO public"))


async def drop_tenant_schema(session: AsyncSession, schema_name: str) -> None:
    schema = validate_schema_name(schema_name)
    await session.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    await session.commit()


def tenant_migration_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "alembic" / "tenant_versions"
