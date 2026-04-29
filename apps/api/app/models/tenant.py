from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Tenant(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    schema_name: Mapped[str] = mapped_column(String(63), nullable=False, unique=True)
    industry: Mapped[str | None] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
