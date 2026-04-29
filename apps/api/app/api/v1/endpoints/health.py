from typing import Any

from fastapi import APIRouter

from app.core.config import settings
from app.core.db import healthcheck

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, Any]:
    db_status = await healthcheck()
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        **db_status,
    }
