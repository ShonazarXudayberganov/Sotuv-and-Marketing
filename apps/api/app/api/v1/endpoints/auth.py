from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import CurrentUser, get_current_user, get_tenant_session
from app.models.tenant_scoped import UserSession
from app.schemas.auth import (
    AuthBundle,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleOAuthRequest,
    LoginRequest,
    OAuthBundle,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TelegramOAuthRequest,
    VerifyPhoneRequest,
)
from app.schemas.tenant import UserSessionOut
from app.services import auth_service, oauth_service, session_service

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    verification_id, masked = await auth_service.start_registration(session, payload)
    return RegisterResponse(verification_id=verification_id, phone_masked=masked)


@router.post("/verify-phone", response_model=AuthBundle)
async def verify_phone(
    payload: VerifyPhoneRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AuthBundle:
    return await auth_service.verify_phone_and_register(
        session, payload.verification_id, payload.code, request=request
    )


@router.post("/login", response_model=AuthBundle)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AuthBundle:
    return await auth_service.login(
        session,
        payload.email_or_phone,
        payload.password.get_secret_value(),
        request=request,
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
    verification_id, masked = await auth_service.start_password_reset(
        session, payload.email_or_phone
    )
    return ForgotPasswordResponse(verification_id=verification_id, phone_masked=masked)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db),
) -> None:
    await auth_service.reset_password(
        session,
        payload.verification_id,
        payload.code,
        payload.new_password.get_secret_value(),
    )
    return None


@router.post("/refresh")
async def refresh(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    access_token = await auth_service.refresh(session, payload.refresh_token)
    return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> None:
    """Revoke the session row backing the supplied refresh token."""
    await auth_service.revoke_refresh(session, payload.refresh_token)
    return None


@router.post("/google", response_model=OAuthBundle)
async def google_oauth(
    payload: GoogleOAuthRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> OAuthBundle:
    identity = await oauth_service.verify_google(payload.id_token)
    bundle, is_new = await auth_service.login_or_create_via_oauth(
        session,
        email=identity.email,
        full_name=identity.full_name,
        request=request,
    )
    return OAuthBundle(**bundle.model_dump(), is_new_user=is_new)


@router.post("/telegram", response_model=OAuthBundle)
async def telegram_oauth(
    payload: TelegramOAuthRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> OAuthBundle:
    identity = await oauth_service.verify_telegram(payload.model_dump(exclude_none=False))
    bundle, is_new = await auth_service.login_or_create_via_oauth(
        session,
        email=identity.email,
        full_name=identity.full_name,
        request=request,
    )
    return OAuthBundle(**bundle.model_dump(), is_new_user=is_new)


@router.get("/sessions", response_model=list[UserSessionOut])
async def list_sessions(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> list[UserSessionOut]:
    rows = await session_service.list_active_for_user(db, user_id=current.id)
    return [UserSessionOut.model_validate(r) for r in rows]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> None:
    record = await db.get(UserSession, session_id)
    if record is None or record.user_id != current.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if record.revoked_at is None:
        await session_service.revoke_jti(db, record.jti)
        await db.commit()
    return None
