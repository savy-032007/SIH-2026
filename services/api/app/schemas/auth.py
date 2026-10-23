"""Request and response shapes for authentication (SPEC section 8)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Region, Role


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    role: str | None = None


class TokenResponse(BaseModel):
    """Issued once authentication is fully complete, MFA included."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")
    role: Role
    #: The refresh token travels as an httpOnly cookie, never in this body.


class MfaChallengeResponse(BaseModel):
    """Password accepted, TOTP still required.

    `mfa_token` authorises nothing except the `/auth/mfa/verify` call.
    """

    mfa_required: bool = True
    mfa_token: str
    expires_in: int


class MfaVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mfa_token: str
    code: str = Field(min_length=6, max_length=10, examples=["123456"])


class MeResponse(BaseModel):
    """The caller's own identity and scope."""

    id: uuid.UUID
    email: EmailStr
    role: Role
    institution_id: uuid.UUID | None
    institution_name: str | None = None
    region: Region | None
    mfa_enabled: bool
    #: True for AICTE_ANALYST — the web app uses it to render masked views.
    pii_masked: bool
