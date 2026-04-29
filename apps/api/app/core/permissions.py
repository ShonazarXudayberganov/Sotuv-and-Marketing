"""Permission registry + role templates.

A permission is a string `<resource>.<action>` (e.g. `contacts.create`).
The 5 standard roles below are seeded into every new tenant. Custom roles can
override the permission list, but the slug `owner` is always immutable.
"""

from __future__ import annotations

from typing import Final

# ─────────── All known permissions ───────────
PERMISSIONS: Final[list[str]] = [
    # Tenant / company
    "tenant.read",
    "tenant.update",
    # Users / roles
    "users.read",
    "users.invite",
    "users.update",
    "users.remove",
    "roles.read",
    "roles.create",
    "roles.update",
    "roles.delete",
    # Departments
    "departments.read",
    "departments.create",
    "departments.update",
    "departments.delete",
    # Tasks (Sprint 4)
    "tasks.read",
    "tasks.create",
    "tasks.update",
    "tasks.delete",
    # Notifications
    "notifications.read",
    "notifications.send",
    # Audit log
    "audit.read",
    # API keys
    "api_keys.read",
    "api_keys.create",
    "api_keys.revoke",
    # Billing (Sprint 5)
    "billing.read",
    "billing.update",
    # Phase 1+ modules — placeholders so role templates know they exist
    "crm.read",
    "crm.write",
    "smm.read",
    "smm.write",
    "ads.read",
    "ads.write",
    "inbox.read",
    "inbox.write",
    "reports.read",
    "integrations.read",
    "integrations.write",
    # AI
    "ai.use",
]


def _every() -> list[str]:
    return list(PERMISSIONS)


# ─────────── 5 standard roles ───────────
STANDARD_ROLES: Final[list[dict[str, object]]] = [
    {
        "slug": "owner",
        "name": "Owner",
        "description": "Kompaniya egasi — to'liq imtiyozlar, billing kiradi",
        "is_system": True,
        "permissions": _every(),
    },
    {
        "slug": "admin",
        "name": "Admin",
        "description": "Boshqaruvchi — billing'dan tashqari hammasi",
        "is_system": True,
        "permissions": [p for p in _every() if not p.startswith("billing.update")],
    },
    {
        "slug": "manager",
        "name": "Manager",
        "description": "Bo'lim boshlig'i — o'z bo'limi kontekstida ishlaydi",
        "is_system": True,
        "permissions": [
            "tenant.read",
            "users.read",
            "departments.read",
            "tasks.read",
            "tasks.create",
            "tasks.update",
            "notifications.read",
            "crm.read",
            "crm.write",
            "smm.read",
            "smm.write",
            "inbox.read",
            "inbox.write",
            "reports.read",
            "ai.use",
        ],
    },
    {
        "slug": "operator",
        "name": "Operator",
        "description": "Xodim — o'ziga biriktirilgan ma'lumotlar bilan ishlaydi",
        "is_system": True,
        "permissions": [
            "tenant.read",
            "users.read",
            "departments.read",
            "tasks.read",
            "tasks.create",
            "tasks.update",
            "notifications.read",
            "crm.read",
            "crm.write",
            "inbox.read",
            "inbox.write",
            "ai.use",
        ],
    },
    {
        "slug": "viewer",
        "name": "Viewer",
        "description": "Faqat ko'rish — hech narsani o'zgartira olmaydi",
        "is_system": True,
        "permissions": [
            "tenant.read",
            "users.read",
            "departments.read",
            "tasks.read",
            "crm.read",
            "smm.read",
            "ads.read",
            "reports.read",
        ],
    },
]


def role_template(slug: str) -> dict[str, object] | None:
    return next((r for r in STANDARD_ROLES if r["slug"] == slug), None)
