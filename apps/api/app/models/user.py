from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(30), default="owner", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)


class VerificationCode(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "verification_codes"
    __table_args__ = {"schema": "public"}

    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    payload: Mapped[str | None] = mapped_column(String(2000))
    consumed: Mapped[bool] = mapped_column(default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
