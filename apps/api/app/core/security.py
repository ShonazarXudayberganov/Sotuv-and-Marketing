from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

TokenType = Literal["access", "refresh"]

# bcrypt has a 72-byte hard limit; longer passwords are truncated by the hashing
# function, so we truncate explicitly to keep verify() deterministic across
# library versions.
_BCRYPT_MAX_BYTES = 72


def _truncate_password(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    rounds = settings.BCRYPT_ROUNDS
    return bcrypt.hashpw(_truncate_password(password), bcrypt.gensalt(rounds=rounds)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate_password(plain), hashed.encode())
    except ValueError:
        return False


def create_token(
    subject: str,
    token_type: TokenType,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    if token_type == "access":
        expires = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_TTL_MINUTES)
    else:
        expires = now + timedelta(days=settings.JWT_REFRESH_TOKEN_TTL_DAYS)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.JWT_SECRET.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc


class InvalidTokenError(Exception):
    """Raised when a JWT cannot be decoded or has invalid claims."""
