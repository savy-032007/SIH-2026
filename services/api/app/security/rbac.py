"""Authentication and role-based access control dependencies (SPEC section 8).

Authorisation is enforced in three layers, because any one of them alone leaks:

1. `require_roles(...)` — can this role call this route at all?
2. `scope_conditions(...)` — which *rows* may it see? A regional officer calling a
   legitimate route must still not read another region's institutions, so the
   filter is applied at query level rather than trusted to a query parameter.
3. `should_mask_pii(...)` — AICTE_ANALYST is read-only with PII masked, so even
   permitted rows come back redacted.

Next.js middleware mirrors layer 1 for navigation, but the server is the only
place that decides.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.enums import AICTE_ROLES, Region, Role
from app.models.institution import Institution
from app.models.user import User
from app.security.tokens import TokenError, decode_token, subject_uuid

_bearer = HTTPBearer(auto_error=False, description="Access token from /auth/login")


@dataclass(frozen=True)
class CurrentUser:
    """The authenticated caller, resolved once per request."""

    id: uuid.UUID
    email: str
    role: Role
    institution_id: uuid.UUID | None
    region: Region | None

    @property
    def is_aicte(self) -> bool:
        return self.role in AICTE_ROLES

    @property
    def is_institution(self) -> bool:
        return self.institution_id is not None


def _unauthenticated(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """Resolve the Bearer access token to a live, active user.

    The database is consulted on every request rather than trusting the token's
    claims, so deactivating a user takes effect immediately instead of when their
    15-minute access token happens to expire.
    """
    if credentials is None or not credentials.credentials:
        raise _unauthenticated("Not authenticated")

    try:
        payload = decode_token(credentials.credentials, "access")
        user_id = subject_uuid(payload)
    except TokenError as exc:
        raise _unauthenticated(str(exc)) from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthenticated("User is no longer active")

    return CurrentUser(
        id=user.id,
        email=user.email,
        role=user.role,
        institution_id=user.institution_id,
        region=user.region,
    )


def require_roles(*allowed: Role):
    """Dependency factory restricting a route to the given roles."""
    allowed_set = frozenset(allowed)
    if not allowed_set:
        raise ValueError("require_roles needs at least one role")

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_set:
            # Deliberately does not name the roles that would be accepted.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This role may not perform that action",
            )
        return user

    return dependency


# --------------------------------------------------------------------------- #
# Row-level scoping
# --------------------------------------------------------------------------- #


def scope_conditions(user: CurrentUser, institution_id_column: ColumnElement) -> list:
    """Row filters for any query whose rows hang off an institution.

    * institution roles -> their own institution only
    * regional officer  -> institutions in their region only
    * super admin / analyst -> national

    Returns a list of conditions to splat into `.where(*conditions)`. An empty
    list means national scope.
    """
    if user.institution_id is not None:
        return [institution_id_column == user.institution_id]

    if user.role is Role.AICTE_REGIONAL_OFFICER:
        if user.region is None:
            # A regional officer with no region must see nothing, not everything.
            return [institution_id_column.is_(None)]
        return [
            institution_id_column.in_(
                select(Institution.id).where(Institution.region == user.region)
            )
        ]

    return []


def assert_can_access_institution(user: CurrentUser, institution: Institution) -> None:
    """Guard for single-record routes, where a query filter has nothing to bite on."""
    if user.institution_id is not None:
        if institution.id != user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This institution is outside your scope",
            )
        return

    if user.role is Role.AICTE_REGIONAL_OFFICER and institution.region != user.region:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This institution is outside your region",
        )


def should_mask_pii(user: CurrentUser) -> bool:
    """AICTE_ANALYST sees aggregates and masked identifiers only (SPEC section 8)."""
    return user.role is Role.AICTE_ANALYST


def client_ip(request: Request) -> str | None:
    """Caller IP for audit entries, honouring one proxy hop.

    `X-Forwarded-For` is client-controlled, so this is only trustworthy behind a
    proxy that overwrites it. Phase 5 pins the trusted-proxy configuration.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def roles_except(*excluded: Role) -> Sequence[Role]:
    """Every role but the listed ones — keeps route decorators readable."""
    return tuple(role for role in Role if role not in frozenset(excluded))
