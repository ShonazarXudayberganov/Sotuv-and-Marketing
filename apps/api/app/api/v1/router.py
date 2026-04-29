from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    departments,
    health,
    onboarding,
    roles,
    tenant,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenant.router, prefix="/tenant", tags=["tenant"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
