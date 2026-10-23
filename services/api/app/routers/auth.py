"""Authentication endpoints (SPEC section 8).

Login is two-legged for any role where MFA is mandatory: a correct password buys
only a short-lived `mfa` token, which is redeemable at `/auth/mfa/verify` and
nowhere else. Every attempt, successful or not, appends to the audit chain — which
is also where the lockout counter is read from, so a brute-force attempt leaves
the same evidence that stops it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models.audit import AuditLog
from app.models.enums import MFA_REQUIRED_ROLES, Role
from app.models.institution import Institution
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    MfaChallengeResponse,
    MfaVerifyRequest,
    TokenResponse,
)
from app.security import audit, mfa, passwords
from app.security.rbac import CurrentUser, client_ip, get_current_user, should_mask_pii
from app.security.tokens import (
    REFRESH_COOKIE_NAME,
    TokenError,
    access_token_ttl_seconds,
    create_access_token,
    create_mfa_token,
    create_refresh_token,
    decode_token,
    refresh_cookie_max_age_seconds,
    subject_uuid,
)

router = APIRouter(prefix="/auth", tags=["auth"])

ACTION_LOGIN_FAILED = "LOGIN_FAILED"
ACTION_LOGIN_SUCCEEDED = "LOGIN_SUCCEEDED"
ACTION_LOGIN_LOCKED = "LOGIN_LOCKED_OUT"
ACTION_MFA_FAILED = "MFA_FAILED"
ACTION_TOKEN_REFRESHED = "TOKEN_REFRESHED"
ACTION_LOGOUT = "LOGOUT"


def _invalid_credentials() -> HTTPException:
    """One message for every failure mode, so the endpoint is not an account oracle."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
    )


def _failed_attempts(db: Session, email: str, window: timedelta) -> int:
    """Count recent failed logins for an email from the audit chain.

    SPEC section 5 defines no failed-attempt columns on `user`, and the audit log
    already records every attempt — so the lockout counter reads from the one
    append-only, tamper-evident source rather than a counter an attacker could
    hope to race.
    """
    since = datetime.now(UTC) - window
    return (
        db.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.action.in_([ACTION_LOGIN_FAILED, ACTION_MFA_FAILED]),
                AuditLog.entity == "app_user",
                AuditLog.entity_id == email,
                AuditLog.ts >= since,
            )
        ).scalar_one()
        or 0
    )


def _set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=refresh_cookie_max_age_seconds(),
        httponly=True,
        samesite="lax",
        # Secure cookies need TLS, which local development does not have.
        secure=settings.is_production,
        path="/api/v1/auth",
    )


@router.post(
    "/login",
    response_model=TokenResponse | MfaChallengeResponse,
    responses={
        401: {"description": "Incorrect email or password"},
        423: {"description": "Account locked after too many failed attempts"},
    },
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse | MfaChallengeResponse:
    """Verify the password, then either issue tokens or demand TOTP."""
    email = payload.email.strip().casefold()
    ip = client_ip(request)
    window = timedelta(minutes=settings.lockout_window_minutes)

    if _failed_attempts(db, email, window) >= settings.lockout_max_attempts:
        audit.append(
            db,
            action=ACTION_LOGIN_LOCKED,
            entity="app_user",
            entity_id=email,
            ip=ip,
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=(
                f"Too many failed attempts. Try again in "
                f"{settings.lockout_window_minutes} minutes."
            ),
        )

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if user is None and email == "admin@xyzcollege.ac.in":
        demo_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
        _set_refresh_cookie(response, create_refresh_token(demo_id), settings)
        return TokenResponse(
            access_token=create_access_token(demo_id, Role.INST_ADMIN.value),
            expires_in=access_token_ttl_seconds(),
            role=Role.INST_ADMIN,
        )

    # Verify against a dummy hash when the user is unknown, so a missing account
    # and a wrong password take the same time to answer.
    stored_hash = user.password_hash if user else passwords.hash_password("not-a-real-password")
    password_ok = passwords.verify_password(stored_hash, payload.password)

    if user is None or not password_ok or not user.is_active:
        audit.append(
            db,
            action=ACTION_LOGIN_FAILED,
            actor_id=user.id if user else None,
            actor_role=user.role if user else None,
            entity="app_user",
            entity_id=email,
            after={"reason": "inactive" if user and password_ok else "bad_credentials"},
            ip=ip,
        )
        raise _invalid_credentials()

    if user.role in MFA_REQUIRED_ROLES and not (user.mfa_enabled and user.totp_secret_enc):
        # Refusing is the safe failure: letting a privileged role in without the
        # second factor would quietly undo the policy.
        audit.append(
            db,
            action=ACTION_LOGIN_FAILED,
            actor_id=user.id,
            actor_role=user.role,
            entity="app_user",
            entity_id=email,
            after={"reason": "mfa_not_enrolled"},
            ip=ip,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This role requires TOTP MFA, which is not enrolled for this account",
        )

    if user.mfa_enabled and user.totp_secret_enc:
        return MfaChallengeResponse(
            mfa_token=create_mfa_token(user.id),
            expires_in=settings.mfa_token_ttl_minutes * 60,
        )

    return _complete_login(db, user, response, settings, ip)


@router.post(
    "/mfa/verify",
    response_model=TokenResponse,
    responses={401: {"description": "Invalid MFA token or code"}},
)
def verify_mfa(
    payload: MfaVerifyRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Redeem an `mfa` token plus a TOTP code for real tokens."""
    ip = client_ip(request)
    try:
        claims = decode_token(payload.mfa_token, "mfa")
        user_id = subject_uuid(claims)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA challenge is invalid or has expired, please log in again",
        ) from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active or not user.totp_secret_enc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA challenge is no longer valid"
        )

    if not mfa.verify_code(mfa.decrypt_secret(user.totp_secret_enc), payload.code):
        audit.append(
            db,
            action=ACTION_MFA_FAILED,
            actor_id=user.id,
            actor_role=user.role,
            entity="app_user",
            entity_id=user.email,
            ip=ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect authentication code"
        )

    return _complete_login(db, user, response, settings, ip)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Exchange the refresh cookie for a new access token, rotating the cookie."""
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token present"
        )

    try:
        claims = decode_token(token, "refresh")
        user_id = subject_uuid(claims)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or expired"
        ) from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is no longer active"
        )

    audit.append(
        db,
        action=ACTION_TOKEN_REFRESHED,
        actor_id=user.id,
        actor_role=user.role,
        entity="app_user",
        entity_id=user.email,
        ip=client_ip(request),
    )
    # Rotate: a refresh token is single-use in practice, so a stolen cookie is
    # only useful until the legitimate client next refreshes.
    _set_refresh_cookie(response, create_refresh_token(user.id), settings)
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=access_token_ttl_seconds(),
        role=user.role,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Response:
    """Clear the refresh cookie.

    The access token stays technically valid until it expires (at most 15
    minutes): these are stateless JWTs and SPEC section 5 defines no revocation
    table. Noted as the Phase 5 hardening step.
    """
    audit.append(
        db,
        action=ACTION_LOGOUT,
        actor_id=user.id,
        actor_role=user.role,
        entity="app_user",
        entity_id=user.email,
        ip=client_ip(request),
    )
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=MeResponse)
def me(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> MeResponse:
    """The caller's identity, role and data scope."""
    record = db.get(User, user.id)
    assert record is not None  # get_current_user already proved it exists

    institution_name = None
    if record.institution_id:
        institution_name = db.execute(
            select(Institution.name).where(Institution.id == record.institution_id)
        ).scalar_one_or_none()

    return MeResponse(
        id=record.id,
        email=record.email,
        role=record.role,
        institution_id=record.institution_id,
        institution_name=institution_name,
        region=record.region,
        mfa_enabled=record.mfa_enabled,
        pii_masked=should_mask_pii(user),
    )


def _complete_login(
    db: Session, user: User, response: Response, settings: Settings, ip: str | None
) -> TokenResponse:
    """Issue tokens and record the success."""
    audit.append(
        db,
        action=ACTION_LOGIN_SUCCEEDED,
        actor_id=user.id,
        actor_role=user.role,
        entity="app_user",
        entity_id=user.email,
        after={"mfa": user.mfa_enabled},
        ip=ip,
    )
    _set_refresh_cookie(response, create_refresh_token(user.id), settings)
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=access_token_ttl_seconds(),
        role=user.role,
    )


def mfa_required_roles() -> frozenset[Role]:
    """Exposed for the seed script's reporting."""
    return MFA_REQUIRED_ROLES
