import pytest

from app.core.security import (
    InvalidTokenError,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip():
    h = hash_password("MySecret123")
    assert h != "MySecret123"
    assert verify_password("MySecret123", h) is True
    assert verify_password("wrong", h) is False


def test_create_and_decode_access_token():
    token = create_token("user-1", "access", extra_claims={"role": "owner"})
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"
    assert payload["role"] == "owner"


def test_decode_invalid_token_raises():
    with pytest.raises(InvalidTokenError):
        decode_token("not.a.token")
