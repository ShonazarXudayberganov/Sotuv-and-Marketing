"""Tenant lifecycle: create the schema and run tenant-scoped migrations."""

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenancy import slugify_schema, validate_schema_name
from app.models.tenant import Tenant


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
    """Create a fresh PostgreSQL schema for the tenant.

    Tenant tables are added in Phase 0 Sprint 3 (departments, roles, etc.) — for
    now the schema is empty but reserved.
    """
    schema = validate_schema_name(tenant.schema_name)
    await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    await session.commit()


async def drop_tenant_schema(session: AsyncSession, schema_name: str) -> None:
    schema = validate_schema_name(schema_name)
    await session.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    await session.commit()


def tenant_migration_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "alembic" / "tenant_versions"
