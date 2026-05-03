from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    InvalidTokenError,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.tenant import Tenant
from app.models.user import User, VerificationCode
from app.schemas.auth import AuthBundle, RegisterRequest, TenantOut, UserOut
from app.services.sms import generate_verification_code, get_sms_provider
from app.services.tenant_service import (
    attach_owner_membership,
    create_tenant_schema,
    generate_unique_schema_name,
)

VERIFICATION_TTL_MINUTES = 5
MAX_VERIFICATION_ATTEMPTS = 5


def _mask_phone(phone: str) -> str:
    return phone[:4] + "***" + phone[-2:] if len(phone) >= 6 else phone


async def start_registration(session: AsyncSession, payload: RegisterRequest) -> tuple[UUID, str]:
    existing = await session.execute(
        select(User).where(or_(User.email == payload.email, User.phone == payload.phone))
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or phone already exists",
        )

    code = generate_verification_code()

    import json

    verification_payload = json.dumps(
        {
            "company_name": payload.company_name,
            "industry": payload.industry,
            "phone": payload.phone,
            "email": payload.email,
            "password_hash": hash_password(payload.password.get_secret_value()),
        }
    )

    record = VerificationCode(
        phone=payload.phone,
        code_hash=hash_password(code),
        purpose="register",
        payload=verification_payload,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    sms = get_sms_provider()
    await sms.send(payload.phone, f"NEXUS AI tasdiq kodi: {code}")

    return record.id, _mask_phone(payload.phone)


async def verify_phone_and_register(
    session: AsyncSession, verification_id: UUID, code: str
) -> AuthBundle:
    record = await session.get(VerificationCode, verification_id)
    if record is None or record.consumed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification request",
        )

    age = datetime.now(UTC) - record.created_at
    if age > timedelta(minutes=VERIFICATION_TTL_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired"
        )

    if record.attempts >= MAX_VERIFICATION_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts — request a new code",
        )

    if not verify_password(code, record.code_hash):
        record.attempts += 1
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code"
        )

    import json

    data = json.loads(record.payload or "{}")
    schema_name = await generate_unique_schema_name(session, data["company_name"])

    tenant = Tenant(
        name=data["company_name"],
        schema_name=schema_name,
        industry=data["industry"],
        phone=data["phone"],
    )
    session.add(tenant)
    await session.flush()

    user = User(
        tenant_id=tenant.id,
        email=data["email"],
        phone=data["phone"],
        password_hash=data["password_hash"],
        role="owner",
        is_verified=True,
    )
    session.add(user)

    record.consumed = True
    await session.commit()
    await session.refresh(tenant)
    await session.refresh(user)

    await create_tenant_schema(session, tenant)
    await attach_owner_membership(session, tenant, user.id)

    return _issue_auth_bundle(user, tenant)


async def login(session: AsyncSession, email_or_phone: str, password: str) -> AuthBundle:
    result = await session.execute(
        select(User).where(or_(User.email == email_or_phone, User.phone == email_or_phone))
    )
    user = result.scalars().first()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Phone not verified")

    tenant = await session.get(Tenant, user.tenant_id)
    if tenant is None or not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant disabled")

    return _issue_auth_bundle(user, tenant)


def _normalize_login_identifier(value: str) -> str:
    value = value.strip()
    if "@" in value:
        return value.lower()
    cleaned = "".join(c for c in value if c.isdigit() or c == "+")
    if cleaned and not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned or value


async def start_password_reset(session: AsyncSession, email_or_phone: str) -> tuple[UUID, str]:
    identifier = _normalize_login_identifier(email_or_phone)
    result = await session.execute(
        select(User).where(or_(User.email == identifier, User.phone == identifier))
    )
    user = result.scalars().first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    code = generate_verification_code()

    import json

    record = VerificationCode(
        phone=user.phone,
        code_hash=hash_password(code),
        purpose="password_reset",
        payload=json.dumps({"user_id": str(user.id)}),
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    sms = get_sms_provider()
    await sms.send(user.phone, f"NEXUS AI parol tiklash kodi: {code}")

    return record.id, _mask_phone(user.phone)


async def reset_password(
    session: AsyncSession,
    verification_id: UUID,
    code: str,
    new_password: str,
) -> None:
    record = await session.get(VerificationCode, verification_id)
    if record is None or record.consumed or record.purpose != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset request",
        )

    age = datetime.now(UTC) - record.created_at
    if age > timedelta(minutes=VERIFICATION_TTL_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset code expired"
        )

    if record.attempts >= MAX_VERIFICATION_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts — request a new code",
        )

    if not verify_password(code, record.code_hash):
        record.attempts += 1
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password reset code"
        )

    import json

    data = json.loads(record.payload or "{}")
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset payload",
        )

    user = await session.get(User, UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(new_password)
    record.consumed = True
    await session.commit()


async def refresh(session: AsyncSession, refresh_token: str) -> str:
    try:
        payload = decode_token(refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )

    user = await session.get(User, UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )

    tenant = await session.get(Tenant, user.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant not found")

    return create_token(
        str(user.id),
        "access",
        extra_claims={
            "tenant_id": str(tenant.id),
            "tenant_schema": tenant.schema_name,
            "role": user.role,
        },
    )


def _issue_auth_bundle(user: User, tenant: Tenant) -> AuthBundle:
    extra = {
        "tenant_id": str(tenant.id),
        "tenant_schema": tenant.schema_name,
        "role": user.role,
    }
    access = create_token(str(user.id), "access", extra_claims=extra)
    refresh_token = create_token(str(user.id), "refresh", extra_claims=extra)
    return AuthBundle(
        access_token=access,
        refresh_token=refresh_token,
        user=UserOut.model_validate(user),
        tenant=TenantOut.model_validate(tenant),
    )
