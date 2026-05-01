from fastapi import APIRouter

from app.api.v1.endpoints import (
    api_keys,
    auth,
    billing,
    brands,
    content,
    departments,
    health,
    integrations,
    knowledge,
    notifications,
    onboarding,
    posts,
    roles,
    social,
    tasks,
    tenant,
    twofa,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(tenant.router, prefix="/tenant", tags=["tenant"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(twofa.router, prefix="/2fa", tags=["2fa"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(brands.router, prefix="/brands", tags=["smm"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["smm"])
api_router.include_router(social.router, prefix="/social", tags=["smm"])
api_router.include_router(content.router, prefix="/ai", tags=["smm"])
api_router.include_router(posts.router, prefix="/posts", tags=["smm"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
