"""Pytest fixtures: per-request DB session, async client, mock SMS.

We use a session-scoped engine with NullPool. The dependency override creates a
fresh session per FastAPI request — this matches production behavior and avoids
"another operation in progress" errors that come from sharing an asyncpg
connection across concurrent tasks.
"""

import os
from collections.abc import AsyncIterator

# Set test env BEFORE importing the app
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SMS_MOCK", "true")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://nexus:nexus@localhost:5434/nexus_test",
)

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app
from app.services.sms import MockSMSProvider


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(str(settings.DATABASE_URL), poolclass=NullPool)
    async with eng.begin() as conn:
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.run_sync(Base.metadata.drop_all)
        result = await conn.exec_driver_sql(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name LIKE 'tenant_%'"
        )
        for (schema,) in list(result):
            await conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="session")
async def client(
    engine: AsyncEngine, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()

    # Per-test cleanup: rows + tenant_* schemas
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
        result = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name LIKE 'tenant_%'"
            )
        )
        for (schema,) in list(result):
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Direct DB access fixture for tests that need to inspect/seed without HTTP."""
    async with session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
def reset_mock_sms() -> None:
    MockSMSProvider.sent.clear()


@pytest.fixture
def sample_register_payload() -> dict:
    return {
        "company_name": "Akme Salon",
        "industry": "salon-klinika",
        "phone": "+998901234567",
        "email": "owner@akme.uz",
        "password": "Password123",
        "accept_terms": True,
    }
