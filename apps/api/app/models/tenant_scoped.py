"""Tenant-scoped models — these tables live in each tenant's PostgreSQL schema.

When a new Tenant is created we CREATE SCHEMA + run the same DDL there. The
SQLAlchemy mappers don't know which schema they're in at query time — that's
controlled by the connection's `search_path` set in the request middleware.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Department(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL")
    )
    head_user_id: Mapped[UUID | None] = mapped_column(String(36))
    description: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    children: Mapped[list[Department]] = relationship(
        "Department",
        cascade="all, delete-orphan",
        single_parent=True,
        remote_side="Department.parent_id",
    )


class Role(Base, UUIDPKMixin, TimestampMixin):
    """Role definitions per tenant — 5 standard roles seeded on tenant creation."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class UserMembership(Base, UUIDPKMixin, TimestampMixin):
    """Per-tenant user record (linked back to public.users by user_id)."""

    __tablename__ = "user_memberships"
    __table_args__ = (UniqueConstraint("user_id", "department_id", name="uq_user_dept"),)

    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL")
    )
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    invited_by: Mapped[UUID | None] = mapped_column()


class Notification(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    payload: Mapped[dict[str, object] | None] = mapped_column(JSON)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "audit_log"

    user_id: Mapped[UUID | None] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(64))
    metadata_: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))


class ApiKey(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[UUID] = mapped_column(nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Task(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    assignee_id: Mapped[UUID | None] = mapped_column(index=True)
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL")
    )
    related_type: Mapped[str | None] = mapped_column(String(30))
    related_id: Mapped[str | None] = mapped_column(String(64))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_hours: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[UUID] = mapped_column(nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TwoFactorSecret(Base, UUIDPKMixin, TimestampMixin):
    """Per-user TOTP secret (one row per user)."""

    __tablename__ = "two_factor_secrets"

    user_id: Mapped[UUID] = mapped_column(unique=True, nullable=False)
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    backup_codes_hash: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NotificationPreference(Base, UUIDPKMixin, TimestampMixin):
    """Per-user notification routing — which categories go to which channels."""

    __tablename__ = "notification_preferences"

    user_id: Mapped[UUID] = mapped_column(unique=True, nullable=False)
    channels: Mapped[dict[str, list[str]]] = mapped_column(JSON, default=dict, nullable=False)
    quiet_hours_start: Mapped[int | None] = mapped_column(Integer)
    quiet_hours_end: Mapped[int | None] = mapped_column(Integer)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64))


class UserSession(Base, UUIDPKMixin, TimestampMixin):
    """Refresh-token-backed user session — supports revoke + active sessions UI."""

    __tablename__ = "user_sessions"

    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


__all__ = [
    "ApiKey",
    "AuditLog",
    "Department",
    "Notification",
    "NotificationPreference",
    "Role",
    "Task",
    "TwoFactorSecret",
    "UserMembership",
    "UserSession",
]
