from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


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


class MembershipOut(BaseModel):
    id: UUID
    user_id: UUID
    department_id: UUID | None
    role_id: UUID
    is_primary: bool

    model_config = {"from_attributes": True}


class InviteUserRequest(BaseModel):
    email: str
    phone: str
    full_name: str | None = None
    role_slug: str
    department_id: UUID | None = None


class OnboardingState(BaseModel):
    step: int = Field(ge=1, le=7)
    completed: bool = False
    company: dict[str, object] | None = None
    departments: list[str] | None = None
    invited_users: list[str] | None = None
    selected_modules: list[str] | None = None
    selected_plan: str | None = None
