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
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        title           varchar(200) NOT NULL,
        description     text,
        status          varchar(20) NOT NULL DEFAULT 'new',
        priority        varchar(20) NOT NULL DEFAULT 'medium',
        assignee_id     uuid,
        department_id   uuid REFERENCES departments(id) ON DELETE SET NULL,
        related_type    varchar(30),
        related_id      varchar(64),
        starts_at       timestamptz,
        due_at          timestamptz,
        estimated_hours integer,
        created_by      uuid NOT NULL,
        completed_at    timestamptz,
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_tasks_assignee_id ON tasks(assignee_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS two_factor_secrets (
        id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id            uuid NOT NULL UNIQUE,
        secret             varchar(64) NOT NULL,
        backup_codes_hash  jsonb NOT NULL DEFAULT '[]'::jsonb,
        enabled_at         timestamptz,
        created_at         timestamptz NOT NULL DEFAULT now(),
        updated_at         timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriptions (
        id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        selected_modules       jsonb NOT NULL DEFAULT '[]'::jsonb,
        tier                   varchar(20) NOT NULL DEFAULT 'start',
        package                varchar(30),
        billing_cycle_months   integer NOT NULL DEFAULT 1,
        price_total            integer NOT NULL DEFAULT 0,
        discount_percent       integer NOT NULL DEFAULT 0,
        starts_at              timestamptz NOT NULL DEFAULT now(),
        expires_at             timestamptz NOT NULL,
        is_trial               boolean NOT NULL DEFAULT true,
        is_active              boolean NOT NULL DEFAULT true,
        cancelled_at           timestamptz,
        created_at             timestamptz NOT NULL DEFAULT now(),
        updated_at             timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS invoices (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        subscription_id uuid NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
        invoice_number  varchar(30) NOT NULL UNIQUE,
        amount          integer NOT NULL,
        status          varchar(20) NOT NULL DEFAULT 'pending',
        payment_method  varchar(20) NOT NULL DEFAULT 'bank_transfer',
        paid_at         timestamptz,
        paid_by_user_id uuid,
        due_at          timestamptz NOT NULL,
        notes           varchar(1000),
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_invoices_status ON invoices(status)
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_usage (
        id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        period       varchar(7) NOT NULL UNIQUE,
        tokens_used  numeric NOT NULL DEFAULT 0,
        tokens_cap   numeric NOT NULL DEFAULT 0,
        created_at   timestamptz NOT NULL DEFAULT now(),
        updated_at   timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS brands (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name            varchar(100) NOT NULL,
        slug            varchar(80) NOT NULL UNIQUE,
        description     varchar(1000),
        industry        varchar(50),
        logo_url        varchar(500),
        primary_color   varchar(20),
        voice_tone      varchar(500),
        target_audience text,
        languages       jsonb NOT NULL DEFAULT '[]'::jsonb,
        is_default      boolean NOT NULL DEFAULT false,
        is_active       boolean NOT NULL DEFAULT true,
        created_by      uuid NOT NULL,
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_brands_slug ON brands(slug)
    """,
    """
    CREATE TABLE IF NOT EXISTS brand_memberships (
        id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        brand_id    uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        user_id     uuid NOT NULL,
        role        varchar(30) NOT NULL DEFAULT 'manager',
        created_at  timestamptz NOT NULL DEFAULT now(),
        updated_at  timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_brand_user UNIQUE (brand_id, user_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_brand_memberships_brand ON brand_memberships(brand_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_brand_memberships_user ON brand_memberships(user_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS tenant_integrations (
        id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        provider              varchar(50) NOT NULL UNIQUE,
        label                 varchar(100),
        credentials_encrypted text NOT NULL,
        is_active             boolean NOT NULL DEFAULT true,
        last_verified_at      timestamptz,
        last_error            varchar(500),
        metadata              jsonb,
        created_by            uuid NOT NULL,
        created_at            timestamptz NOT NULL DEFAULT now(),
        updated_at            timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_tenant_integrations_provider ON tenant_integrations(provider)
    """,
    """
    CREATE TABLE IF NOT EXISTS knowledge_documents (
        id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        brand_id      uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        title         varchar(200) NOT NULL,
        source_type   varchar(20) NOT NULL,
        source_url    varchar(500),
        raw_text      text NOT NULL,
        chunk_count   integer NOT NULL DEFAULT 0,
        embed_status  varchar(20) NOT NULL DEFAULT 'pending',
        embed_error   varchar(500),
        created_by    uuid NOT NULL,
        created_at    timestamptz NOT NULL DEFAULT now(),
        updated_at    timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_knowledge_documents_brand
        ON knowledge_documents(brand_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS knowledge_chunks (
        id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id  uuid NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
        brand_id     uuid NOT NULL,
        position     integer NOT NULL,
        content      text NOT NULL,
        token_count  integer NOT NULL DEFAULT 0,
        embedding    vector(1536),
        created_at   timestamptz NOT NULL DEFAULT now(),
        updated_at   timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_document
        ON knowledge_chunks(document_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_brand
        ON knowledge_chunks(brand_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding
        ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)
    """,
    """
    CREATE TABLE IF NOT EXISTS brand_social_accounts (
        id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        brand_id            uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        provider            varchar(30) NOT NULL,
        external_id         varchar(100) NOT NULL,
        external_handle     varchar(100),
        external_name       varchar(200),
        chat_type           varchar(30),
        is_active           boolean NOT NULL DEFAULT true,
        last_published_at   timestamptz,
        last_error          varchar(500),
        metadata            jsonb,
        created_by          uuid NOT NULL,
        created_at          timestamptz NOT NULL DEFAULT now(),
        updated_at          timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_brand_social UNIQUE (brand_id, provider, external_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_brand_social_accounts_brand
        ON brand_social_accounts(brand_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_brand_social_accounts_provider
        ON brand_social_accounts(provider)
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
