from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

INDUSTRIES = Literal["savdo", "restoran", "salon-klinika", "talim", "xizmat", "it", "boshqa"]


class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=100)
    industry: INDUSTRIES = "boshqa"
    phone: str = Field(min_length=12, max_length=15)
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=100)
    accept_terms: bool

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: SecretStr) -> SecretStr:
        s = v.get_secret_value()
        if not any(c.isupper() for c in s):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in s):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("accept_terms")
    @classmethod
    def must_accept_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Terms must be accepted")
        return v


class RegisterResponse(BaseModel):
    verification_id: UUID
    phone_masked: str
    expires_in_seconds: int = 300


class VerifyPhoneRequest(BaseModel):
    verification_id: UUID
    code: str = Field(min_length=4, max_length=8)


class LoginRequest(BaseModel):
    email_or_phone: str = Field(min_length=3, max_length=255)
    password: SecretStr
    remember_me: bool = False


class ForgotPasswordRequest(BaseModel):
    email_or_phone: str = Field(min_length=3, max_length=255)


class ForgotPasswordResponse(BaseModel):
    verification_id: UUID
    phone_masked: str
    expires_in_seconds: int = 300


class ResetPasswordRequest(BaseModel):
    verification_id: UUID
    code: str = Field(min_length=4, max_length=8)
    new_password: SecretStr = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: SecretStr) -> SecretStr:
        s = v.get_secret_value()
        if not any(c.isupper() for c in s):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in s):
            raise ValueError("Password must contain at least one digit")
        return v


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    role: str

    model_config = {"from_attributes": True}


class TenantOut(BaseModel):
    id: UUID
    name: str
    schema_name: str
    industry: str | None

    model_config = {"from_attributes": True}


class AuthBundle(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: UserOut
    tenant: TenantOut
