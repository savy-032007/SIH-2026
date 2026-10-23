"""JWT issuing and verification (SPEC section 8).

Three token kinds, each with its own purpose claim so one can never be replayed
as another:

* ``access``  — 15 minutes, sent as a Bearer header.
* ``refresh`` — 7 days, httpOnly cookie, rotated on every use.
* ``mfa``     — 5 minutes, issued after a correct password, redeemable only at
  the TOTP step. It carries no authorisation of its own.

Refresh tokens are stateless and therefore not individually revocable before
expiry; SPEC section 5 defines no token table. Logout clears the cookie, and the
short access-token lifetime bounds the damage. A revocation table is the natural
Phase 5 hardening step.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt

from app.config import get_settings

TokenPurpose = Literal["access", "refresh", "mfa"]

_ALGORITHM = "HS256"


class TokenError(Exception):
    """Raised when a token is missing, expired, malformed or of the wrong purpose."""


def _encode(subject: str, purpose: TokenPurpose, ttl: timedelta, **extra: Any) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "purpose": purpose,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "jti": uuid.uuid4().hex,
        **extra,
    }
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=_ALGORITHM)


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    settings = get_settings()
    return _encode(
        str(user_id),
        "access",
        timedelta(minutes=settings.access_token_ttl_minutes),
        role=role,
    )


def create_refresh_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    return _encode(
        str(user_id), "refresh", timedelta(days=settings.refresh_token_ttl_days)
    )


def create_mfa_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    return _encode(str(user_id), "mfa", timedelta(minutes=settings.mfa_token_ttl_minutes))


def decode_token(token: str, expected_purpose: TokenPurpose) -> dict[str, Any]:
    """Decode and verify, rejecting anything issued for a different purpose."""
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("token is invalid") from exc

    if payload.get("purpose") != expected_purpose:
        raise TokenError(
            f"expected a {expected_purpose} token, got {payload.get('purpose')!r}"
        )
    return payload


def subject_uuid(payload: dict[str, Any]) -> uuid.UUID:
    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise TokenError("token subject is not a valid user id") from exc


def access_token_ttl_seconds() -> int:
    return get_settings().access_token_ttl_minutes * 60


REFRESH_COOKIE_NAME = "apaar_refresh"


def refresh_cookie_max_age_seconds() -> int:
    return get_settings().refresh_token_ttl_days * 24 * 3600
