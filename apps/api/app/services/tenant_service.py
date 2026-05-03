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
    """
    CREATE TABLE IF NOT EXISTS content_drafts (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        brand_id        uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        platform        varchar(30) NOT NULL,
        title           varchar(200),
        body            text NOT NULL,
        user_goal       varchar(2000),
        language        varchar(10) NOT NULL DEFAULT 'uz',
        provider        varchar(30),
        model           varchar(80),
        tokens_used     integer NOT NULL DEFAULT 0,
        rag_chunk_ids   jsonb,
        is_starred      boolean NOT NULL DEFAULT false,
        cache_key       varchar(80),
        created_by      uuid NOT NULL,
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_content_drafts_brand
        ON content_drafts(brand_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_content_drafts_cache_key
        ON content_drafts(cache_key)
    """,
    """
    CREATE TABLE IF NOT EXISTS posts (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        brand_id        uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        draft_id        uuid REFERENCES content_drafts(id) ON DELETE SET NULL,
        title           varchar(200),
        body            text NOT NULL,
        media_urls      jsonb,
        status          varchar(20) NOT NULL DEFAULT 'draft',
        scheduled_at    timestamptz,
        published_at    timestamptz,
        last_error      varchar(1000),
        created_by      uuid NOT NULL,
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_posts_brand ON posts(brand_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_posts_status ON posts(status)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_posts_scheduled_at
        ON posts(scheduled_at) WHERE status = 'scheduled'
    """,
    """
    CREATE TABLE IF NOT EXISTS post_publications (
        id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        post_id             uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        social_account_id   uuid NOT NULL REFERENCES brand_social_accounts(id)
                                ON DELETE CASCADE,
        provider            varchar(30) NOT NULL,
        status              varchar(20) NOT NULL DEFAULT 'pending',
        attempts            integer NOT NULL DEFAULT 0,
        next_retry_at       timestamptz,
        external_post_id    varchar(120),
        last_error          varchar(1000),
        completed_at        timestamptz,
        created_at          timestamptz NOT NULL DEFAULT now(),
        updated_at          timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_post_publications_post
        ON post_publications(post_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_post_publications_account
        ON post_publications(social_account_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_post_publications_status
        ON post_publications(status)
    """,
    """
    CREATE TABLE IF NOT EXISTS post_metrics (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        publication_id  uuid NOT NULL REFERENCES post_publications(id) ON DELETE CASCADE,
        brand_id        uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        provider        varchar(30) NOT NULL,
        sampled_at      timestamptz NOT NULL,
        views           integer NOT NULL DEFAULT 0,
        likes           integer NOT NULL DEFAULT 0,
        comments        integer NOT NULL DEFAULT 0,
        shares          integer NOT NULL DEFAULT 0,
        reach           integer NOT NULL DEFAULT 0,
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_post_metrics_publication
        ON post_metrics(publication_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_post_metrics_brand
        ON post_metrics(brand_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_post_metrics_sampled
        ON post_metrics(sampled_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS contacts (
        id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        full_name             varchar(200) NOT NULL,
        company_name          varchar(200),
        phone                 varchar(30),
        email                 varchar(160),
        telegram_username     varchar(80),
        instagram_username    varchar(80),
        industry              varchar(50),
        source                varchar(50),
        status                varchar(30) NOT NULL DEFAULT 'lead',
        department_id         uuid REFERENCES departments(id) ON DELETE SET NULL,
        assignee_id           uuid,
        ai_score              integer NOT NULL DEFAULT 0,
        ai_score_reason       varchar(500),
        ai_score_updated_at   timestamptz,
        notes                 text,
        custom_fields         jsonb,
        tags                  jsonb,
        is_active             boolean NOT NULL DEFAULT true,
        created_by            uuid NOT NULL,
        created_at            timestamptz NOT NULL DEFAULT now(),
        updated_at            timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_contacts_phone ON contacts(phone)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_contacts_email ON contacts(email)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_contacts_status ON contacts(status)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_contacts_score ON contacts(ai_score)
    """,
    """
    CREATE TABLE IF NOT EXISTS contact_activities (
        id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        contact_id        uuid NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
        kind              varchar(30) NOT NULL,
        title             varchar(200),
        body              text,
        direction         varchar(10),
        channel           varchar(30),
        duration_seconds  integer,
        metadata          jsonb,
        occurred_at       timestamptz NOT NULL,
        created_by        uuid,
        created_at        timestamptz NOT NULL DEFAULT now(),
        updated_at        timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_contact_activities_contact
        ON contact_activities(contact_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_contact_activities_occurred
        ON contact_activities(occurred_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS pipelines (
        id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name        varchar(100) NOT NULL,
        slug        varchar(80) NOT NULL UNIQUE,
        description varchar(500),
        is_default  boolean NOT NULL DEFAULT false,
        is_active   boolean NOT NULL DEFAULT true,
        sort_order  integer NOT NULL DEFAULT 0,
        created_by  uuid,
        created_at  timestamptz NOT NULL DEFAULT now(),
        updated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pipeline_stages (
        id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        pipeline_id           uuid NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
        name                  varchar(80) NOT NULL,
        slug                  varchar(80) NOT NULL,
        sort_order            integer NOT NULL DEFAULT 0,
        default_probability   integer NOT NULL DEFAULT 0,
        is_won                boolean NOT NULL DEFAULT false,
        is_lost               boolean NOT NULL DEFAULT false,
        color                 varchar(20),
        created_at            timestamptz NOT NULL DEFAULT now(),
        updated_at            timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_pipeline_stage_slug UNIQUE (pipeline_id, slug)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_pipeline_stages_pipeline
        ON pipeline_stages(pipeline_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS deals (
        id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        title               varchar(200) NOT NULL,
        contact_id          uuid REFERENCES contacts(id) ON DELETE SET NULL,
        pipeline_id         uuid NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
        stage_id            uuid NOT NULL REFERENCES pipeline_stages(id) ON DELETE RESTRICT,
        amount              integer NOT NULL DEFAULT 0,
        currency            varchar(3) NOT NULL DEFAULT 'UZS',
        probability         integer NOT NULL DEFAULT 0,
        status              varchar(20) NOT NULL DEFAULT 'open',
        is_won              boolean NOT NULL DEFAULT false,
        expected_close_at   timestamptz,
        closed_at           timestamptz,
        department_id       uuid REFERENCES departments(id) ON DELETE SET NULL,
        assignee_id         uuid,
        notes               text,
        tags                jsonb,
        sort_order          integer NOT NULL DEFAULT 0,
        created_by          uuid NOT NULL,
        created_at          timestamptz NOT NULL DEFAULT now(),
        updated_at          timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_deals_contact ON deals(contact_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_deals_pipeline ON deals(pipeline_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_deals_stage ON deals(stage_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_deals_status ON deals(status)
    """,
    """
    CREATE TABLE IF NOT EXISTS conversations (
        id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        channel             varchar(30) NOT NULL,
        external_id         varchar(120) NOT NULL,
        contact_id          uuid REFERENCES contacts(id) ON DELETE SET NULL,
        brand_id            uuid REFERENCES brands(id) ON DELETE SET NULL,
        title               varchar(200),
        snippet             varchar(500),
        status              varchar(20) NOT NULL DEFAULT 'open',
        assignee_id         uuid,
        unread_count        integer NOT NULL DEFAULT 0,
        last_message_at     timestamptz,
        last_inbound_at     timestamptz,
        last_outbound_at    timestamptz,
        metadata            jsonb,
        tags                jsonb,
        is_active           boolean NOT NULL DEFAULT true,
        created_at          timestamptz NOT NULL DEFAULT now(),
        updated_at          timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_conversation_channel_external UNIQUE (channel, external_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_conversations_channel ON conversations(channel)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_conversations_status ON conversations(status)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_conversations_last_msg
        ON conversations(last_message_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id     uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        direction           varchar(10) NOT NULL,
        body                text NOT NULL,
        channel             varchar(30) NOT NULL,
        external_id         varchar(120),
        sent_by             varchar(20) NOT NULL DEFAULT 'user',
        sent_by_user_id     uuid,
        is_auto_reply       boolean NOT NULL DEFAULT false,
        confidence          integer,
        occurred_at         timestamptz NOT NULL,
        metadata            jsonb,
        created_at          timestamptz NOT NULL DEFAULT now(),
        updated_at          timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_messages_conversation
        ON messages(conversation_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_messages_occurred
        ON messages(occurred_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS auto_reply_configs (
        id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        is_enabled              boolean NOT NULL DEFAULT false,
        confidence_threshold    integer NOT NULL DEFAULT 90,
        quiet_hours_start       integer,
        quiet_hours_end         integer,
        default_brand_id        uuid REFERENCES brands(id) ON DELETE SET NULL,
        fallback_text           varchar(500),
        channels_enabled        jsonb,
        created_at              timestamptz NOT NULL DEFAULT now(),
        updated_at              timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ad_accounts (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        network         varchar(20) NOT NULL,
        external_id     varchar(120) NOT NULL,
        name            varchar(200) NOT NULL,
        currency        varchar(3) NOT NULL DEFAULT 'UZS',
        status          varchar(20) NOT NULL DEFAULT 'active',
        brand_id        uuid REFERENCES brands(id) ON DELETE SET NULL,
        is_default      boolean NOT NULL DEFAULT false,
        metadata        jsonb,
        last_synced_at  timestamptz,
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_ad_account_network_external UNIQUE (network, external_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_ad_accounts_network ON ad_accounts(network)
    """,
    """
    CREATE TABLE IF NOT EXISTS campaigns (
        id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        account_id          uuid NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
        network             varchar(20) NOT NULL,
        external_id         varchar(120),
        name                varchar(200) NOT NULL,
        objective           varchar(40) NOT NULL DEFAULT 'traffic',
        status              varchar(20) NOT NULL DEFAULT 'draft',
        daily_budget        bigint NOT NULL DEFAULT 0,
        lifetime_budget     bigint,
        currency            varchar(3) NOT NULL DEFAULT 'UZS',
        starts_at           timestamptz,
        ends_at             timestamptz,
        audience            jsonb,
        creative            jsonb,
        notes               text,
        last_synced_at      timestamptz,
        created_by          uuid NOT NULL,
        created_at          timestamptz NOT NULL DEFAULT now(),
        updated_at          timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_campaigns_account ON campaigns(account_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_campaigns_network ON campaigns(network)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_campaigns_status ON campaigns(status)
    """,
    """
    CREATE TABLE IF NOT EXISTS ad_metric_snapshots (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        campaign_id     uuid NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        network         varchar(20) NOT NULL,
        sampled_at      timestamptz NOT NULL,
        impressions     integer NOT NULL DEFAULT 0,
        clicks          integer NOT NULL DEFAULT 0,
        conversions     integer NOT NULL DEFAULT 0,
        spend           bigint NOT NULL DEFAULT 0,
        revenue         bigint NOT NULL DEFAULT 0,
        ctr             integer NOT NULL DEFAULT 0,
        cpc             bigint NOT NULL DEFAULT 0,
        cpa             bigint NOT NULL DEFAULT 0,
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_ad_metric_snapshots_campaign
        ON ad_metric_snapshots(campaign_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_ad_metric_snapshots_sampled
        ON ad_metric_snapshots(sampled_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS saved_reports (
        id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name            varchar(200) NOT NULL,
        description     text,
        definition      jsonb NOT NULL,
        is_pinned       boolean NOT NULL DEFAULT false,
        is_default      boolean NOT NULL DEFAULT false,
        department_id   uuid REFERENCES departments(id) ON DELETE SET NULL,
        created_by      uuid NOT NULL,
        created_at      timestamptz NOT NULL DEFAULT now(),
        updated_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_saved_reports_pinned ON saved_reports(is_pinned)
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

    # Seed default CRM pipeline + 7 standard stages
    await _seed_default_pipeline(session)

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


DEFAULT_PIPELINE_STAGES: tuple[dict[str, object], ...] = (
    {"slug": "new", "name": "Yangi lead", "probability": 10, "color": "#94a3b8"},
    {"slug": "contacted", "name": "Bog'lanildi", "probability": 25, "color": "#60a5fa"},
    {"slug": "negotiation", "name": "Muzokara", "probability": 40, "color": "#a78bfa"},
    {"slug": "proposal", "name": "Taklif yuborildi", "probability": 60, "color": "#f59e0b"},
    {"slug": "agreed", "name": "Kelishildi", "probability": 80, "color": "#fb923c"},
    {"slug": "won", "name": "Sotildi", "probability": 100, "color": "#22c55e", "is_won": True},
    {"slug": "lost", "name": "Yo'qotildi", "probability": 0, "color": "#ef4444", "is_lost": True},
)


async def _seed_default_pipeline(session: AsyncSession) -> None:
    """Insert the default CRM pipeline + 7 stages once per tenant."""
    existing = await session.execute(text("SELECT id FROM pipelines LIMIT 1"))
    if existing.first() is not None:
        return
    pipeline_row = await session.execute(
        text(
            """
            INSERT INTO pipelines (name, slug, description, is_default, sort_order)
            VALUES ('Asosiy sotuv', 'main', 'Standart sotuv voronkasi', true, 0)
            RETURNING id
            """
        )
    )
    pipeline_id = pipeline_row.scalar_one()
    for idx, stage in enumerate(DEFAULT_PIPELINE_STAGES):
        await session.execute(
            text(
                """
                INSERT INTO pipeline_stages
                  (pipeline_id, name, slug, sort_order, default_probability,
                   is_won, is_lost, color)
                VALUES (:pid, :name, :slug, :sort, :prob, :won, :lost, :color)
                """
            ),
            {
                "pid": pipeline_id,
                "name": stage["name"],
                "slug": stage["slug"],
                "sort": idx,
                "prob": stage["probability"],
                "won": bool(stage.get("is_won")),
                "lost": bool(stage.get("is_lost")),
                "color": stage["color"],
            },
        )


async def drop_tenant_schema(session: AsyncSession, schema_name: str) -> None:
    schema = validate_schema_name(schema_name)
    await session.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    await session.commit()


def tenant_migration_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "alembic" / "tenant_versions"
