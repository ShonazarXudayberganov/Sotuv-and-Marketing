from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.permissions import PERMISSIONS

NOTIFICATION_CATEGORIES = {"tasks", "billing", "ai", "inbox", "social", "system"}
NOTIFICATION_CHANNELS = {"in_app", "email", "telegram"}


class TenantOut(BaseModel):
    id: UUID
    name: str
    schema_name: str
    industry: str | None
    phone: str

    model_config = {"from_attributes": True}


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    industry: str | None = None


class DepartmentOut(BaseModel):
    id: UUID
    name: str
    parent_id: UUID | None
    head_user_id: str | None
    description: str | None
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    parent_id: UUID | None = None
    head_user_id: str | None = None
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = 0


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    parent_id: UUID | None = None
    head_user_id: str | None = None
    description: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None
    is_active: bool | None = None


class RoleOut(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    is_system: bool
    permissions: list[str]

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    slug: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str] = Field(default_factory=list)

    @field_validator("permissions")
    @classmethod
    def known_permissions(cls, v: list[str]) -> list[str]:
        unknown = sorted(set(v) - set(PERMISSIONS))
        if unknown:
            raise ValueError(f"Unknown permissions: {', '.join(unknown)}")
        return sorted(set(v))


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str] | None = None

    @field_validator("permissions")
    @classmethod
    def known_permissions(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        unknown = sorted(set(v) - set(PERMISSIONS))
        if unknown:
            raise ValueError(f"Unknown permissions: {', '.join(unknown)}")
        return sorted(set(v))


class MembershipOut(BaseModel):
    id: UUID
    user_id: UUID
    department_id: UUID | None
    role_id: UUID
    is_primary: bool

    model_config = {"from_attributes": True}


class InviteUserRequest(BaseModel):
    email: EmailStr
    phone: str = Field(min_length=12, max_length=20)
    full_name: str | None = None
    role_slug: str
    department_id: UUID | None = None

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned


class UpdateUserRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    role_slug: str | None = None
    department_id: UUID | None = None


class InvitedUserOut(BaseModel):
    id: UUID
    email: EmailStr
    phone: str
    full_name: str | None
    role: str
    temporary_password: str

    model_config = {"from_attributes": True}


class OnboardingState(BaseModel):
    step: int = Field(ge=1, le=7)
    completed: bool = False
    company: dict[str, object] | None = None
    departments: list[str] | None = None
    invited_users: list[str] | None = None
    selected_modules: list[str] | None = None
    selected_plan: str | None = None


class AuditLogOut(BaseModel):
    id: UUID
    user_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    metadata: dict[str, Any] | None = Field(default=None, validation_alias="metadata_")
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class NotificationPreferencesOut(BaseModel):
    channels: dict[str, list[str]]
    quiet_hours_start: int | None
    quiet_hours_end: int | None
    telegram_chat_id: str | None

    model_config = {"from_attributes": True}


class NotificationPreferencesUpdate(BaseModel):
    channels: dict[str, list[str]] | None = None
    quiet_hours_start: int | None = Field(default=None, ge=0, le=23)
    quiet_hours_end: int | None = Field(default=None, ge=0, le=23)
    telegram_chat_id: str | None = Field(default=None, max_length=64)

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, v: dict[str, list[str]] | None) -> dict[str, list[str]] | None:
        if v is None:
            return None
        bad_cats = sorted(set(v.keys()) - NOTIFICATION_CATEGORIES)
        if bad_cats:
            raise ValueError(f"Unknown categories: {', '.join(bad_cats)}")
        for category, channels in v.items():
            bad_chans = sorted(set(channels) - NOTIFICATION_CHANNELS)
            if bad_chans:
                raise ValueError(f"Unknown channels for {category}: {', '.join(bad_chans)}")
        return v


class UserSessionOut(BaseModel):
    id: UUID
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    last_active_at: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}
