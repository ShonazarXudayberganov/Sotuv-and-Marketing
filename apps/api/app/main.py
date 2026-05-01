from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.db import dispose_engine, healthcheck
from app.middleware.tenant import TenantContextMiddleware
from app.services.post_worker import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    start_scheduler()
    yield
    stop_scheduler()
    await dispose_engine()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(TenantContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health() -> dict[str, Any]:
    db_status = await healthcheck()
    return {"status": "ok", **db_status}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
