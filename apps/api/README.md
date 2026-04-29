# NEXUS AI — API (Backend)

FastAPI-based multi-tenant SaaS backend.

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- PostgreSQL 15 (with pgvector) — schema-per-tenant
- Redis 7 (cache + Celery broker + WebSocket pub/sub)
- SQLAlchemy 2 (async) + Alembic
- Pydantic v2

## Local development

### Without Docker (faster iteration)
```bash
poetry install
poetry run uvicorn app.main:app --reload
```

### With Docker
```bash
cd ../../infra && docker compose up -d
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

## Running tests
```bash
poetry run pytest
```

## Linting and formatting
```bash
poetry run ruff check .
poetry run ruff format .
poetry run mypy app
```

## Database migrations
```bash
poetry run alembic upgrade head           # apply migrations
poetry run alembic revision --autogenerate -m "description"
poetry run alembic downgrade -1           # rollback one
```

See [../../docs/01-architecture.md](../../docs/01-architecture.md) for full architecture.
