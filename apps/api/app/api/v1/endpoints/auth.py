from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.auth import (
    AuthBundle,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    VerifyPhoneRequest,
)
from app.services import auth_service

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
    session: AsyncSession = Depends(get_db),
) -> AuthBundle:
    return await auth_service.verify_phone_and_register(
        session, payload.verification_id, payload.code
    )


@router.post("/login", response_model=AuthBundle)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> AuthBundle:
    return await auth_service.login(
        session, payload.email_or_phone, payload.password.get_secret_value()
    )


@router.post("/refresh")
async def refresh(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    access_token = await auth_service.refresh(session, payload.refresh_token)
    return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    """Stateless JWT logout — client discards tokens. Refresh-token revocation
    via DB blacklist is added in Sprint 3 alongside `api_keys`."""
    return None
