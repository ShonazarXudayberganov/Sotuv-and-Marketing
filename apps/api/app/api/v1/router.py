from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    ads,
    analytics,
    api_keys,
    audit,
    auth,
    billing,
    brand_assets,
    brands,
    content,
    content_plan,
    crm,
    departments,
    health,
    inbox,
    integrations,
    knowledge,
    marketplace,
    notifications,
    onboarding,
    posts,
    reports,
    roles,
    social,
    tasks,
    tenant,
    twofa,
    users,
)
from app.middleware.grace import enforce_grace

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
grace_guard = [Depends(enforce_grace)]
api_router.include_router(
    tenant.router, prefix="/tenant", tags=["tenant"], dependencies=grace_guard
)
api_router.include_router(users.router, prefix="/users", tags=["users"], dependencies=grace_guard)
api_router.include_router(roles.router, prefix="/roles", tags=["roles"], dependencies=grace_guard)
api_router.include_router(
    departments.router, prefix="/departments", tags=["departments"], dependencies=grace_guard
)
api_router.include_router(
    onboarding.router, prefix="/onboarding", tags=["onboarding"], dependencies=grace_guard
)
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"], dependencies=grace_guard)
api_router.include_router(twofa.router, prefix="/2fa", tags=["2fa"])
api_router.include_router(
    api_keys.router, prefix="/api-keys", tags=["api-keys"], dependencies=grace_guard
)
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["notifications"],
    dependencies=grace_guard,
)
api_router.include_router(audit.router, prefix="/audit", tags=["audit"], dependencies=grace_guard)
api_router.include_router(brands.router, prefix="/brands", tags=["smm"], dependencies=grace_guard)
api_router.include_router(
    brand_assets.brand_router, prefix="/brands", tags=["smm"], dependencies=grace_guard
)
api_router.include_router(
    brand_assets.router, prefix="/brand-assets", tags=["smm"], dependencies=grace_guard
)
api_router.include_router(
    knowledge.router, prefix="/knowledge", tags=["smm"], dependencies=grace_guard
)
api_router.include_router(social.router, prefix="/social", tags=["smm"], dependencies=grace_guard)
api_router.include_router(content.router, prefix="/ai", tags=["smm"], dependencies=grace_guard)
api_router.include_router(
    content_plan.router, prefix="/content-plan", tags=["smm"], dependencies=grace_guard
)
api_router.include_router(posts.router, prefix="/posts", tags=["smm"], dependencies=grace_guard)
api_router.include_router(
    analytics.router, prefix="/analytics", tags=["smm"], dependencies=grace_guard
)
api_router.include_router(crm.router, prefix="/crm", tags=["crm"], dependencies=grace_guard)
api_router.include_router(inbox.router, prefix="/inbox", tags=["inbox"], dependencies=grace_guard)
api_router.include_router(ads.router, prefix="/ads", tags=["ads"], dependencies=grace_guard)
api_router.include_router(
    reports.router, prefix="/reports", tags=["reports"], dependencies=grace_guard
)
api_router.include_router(
    integrations.router,
    prefix="/integrations",
    tags=["integrations"],
    dependencies=grace_guard,
)
api_router.include_router(
    marketplace.router, prefix="/marketplace", tags=["marketplace"], dependencies=grace_guard
)
