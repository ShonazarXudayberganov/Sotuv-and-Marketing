import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    InvalidTokenError,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.tenancy import validate_schema_name
from app.models.tenant import Tenant
from app.models.user import User, VerificationCode
from app.schemas.auth import AuthBundle, RegisterRequest, TenantOut, UserOut
from app.services import session_service
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
    session: AsyncSession, verification_id: UUID, code: str, request: Request | None = None
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

    return await _issue_auth_bundle(session, user, tenant, request=request)


async def login(
    session: AsyncSession,
    email_or_phone: str,
    password: str,
    request: Request | None = None,
) -> AuthBundle:
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

    return await _issue_auth_bundle(session, user, tenant, request=request)


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

    jti = payload.get("jti")
    if jti:
        active = await session_service.is_active_jti(
            session, schema_name=tenant.schema_name, jti=jti
        )
        await session.commit()
        await session.execute(text("RESET search_path"))
        await session.commit()
        if not active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")

    return create_token(
        str(user.id),
        "access",
        extra_claims={
            "tenant_id": str(tenant.id),
            "tenant_schema": tenant.schema_name,
            "role": user.role,
        },
    )


async def login_or_create_via_oauth(
    session: AsyncSession,
    *,
    email: str,
    full_name: str | None,
    company_seed: str | None = None,
    request: Request | None = None,
) -> tuple[AuthBundle, bool]:
    """Find an existing user by email or provision a brand-new tenant for them."""
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is not None:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled")
        tenant = await session.get(Tenant, user.tenant_id)
        if tenant is None or not tenant.is_active:
            raise HTTPException(status_code=403, detail="Tenant disabled")
        bundle = await _issue_auth_bundle(session, user, tenant, request=request)
        return bundle, False

    company_name = company_seed or (full_name or email.split("@")[0])
    schema_name = await generate_unique_schema_name(session, company_name)
    tenant = Tenant(
        name=company_name,
        schema_name=schema_name,
        industry=None,
        phone="",
    )
    session.add(tenant)
    await session.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        phone="",
        password_hash=hash_password(secrets.token_urlsafe(24)),
        full_name=full_name,
        role="owner",
        is_verified=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(tenant)
    await session.refresh(user)

    await create_tenant_schema(session, tenant)
    await attach_owner_membership(session, tenant, user.id)

    bundle = await _issue_auth_bundle(session, user, tenant, request=request)
    return bundle, True


async def revoke_refresh(session: AsyncSession, refresh_token: str) -> None:
    """Revoke a refresh token's session row so subsequent /refresh calls fail."""
    try:
        payload = decode_token(refresh_token)
    except InvalidTokenError:
        return
    jti = payload.get("jti")
    schema = payload.get("tenant_schema")
    if not jti or not schema:
        return
    await session.execute(text(f"SET search_path TO {validate_schema_name(schema)}, public"))
    await session_service.revoke_jti(session, jti)
    await session.commit()
    await session.execute(text("RESET search_path"))
    await session.commit()


async def _issue_auth_bundle(
    session: AsyncSession,
    user: User,
    tenant: Tenant,
    request: Request | None = None,
) -> AuthBundle:
    extra = {
        "tenant_id": str(tenant.id),
        "tenant_schema": tenant.schema_name,
        "role": user.role,
    }
    jti = session_service.new_jti()
    access = create_token(str(user.id), "access", extra_claims=extra)
    refresh_token = create_token(str(user.id), "refresh", extra_claims=extra, jti=jti)

    schema = validate_schema_name(tenant.schema_name)
    await session.execute(text(f"SET search_path TO {schema}, public"))
    await session_service.create(
        session,
        schema_name=tenant.schema_name,
        user_id=user.id,
        jti=jti,
        request=request,
    )
    await session.commit()
    await session.execute(text("RESET search_path"))
    await session.commit()

    return AuthBundle(
        access_token=access,
        refresh_token=refresh_token,
        user=UserOut.model_validate(user),
        tenant=TenantOut.model_validate(tenant),
    )
