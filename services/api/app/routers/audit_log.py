"""Audit log reading and chain verification (SPEC sections 8, 10.2.8)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.audit import AuditLog
from app.models.enums import Role
from app.security import audit
from app.security.rbac import CurrentUser, require_roles

router = APIRouter(prefix="/audit", tags=["audit"])

#: Reading the audit trail is itself privileged. Analysts are excluded: the log
#: records which actor revealed whose PII, which is exactly the kind of data a
#: read-only, PII-masked role should not be able to mine.
_AUDIT_READERS = (Role.AICTE_SUPER_ADMIN, Role.AICTE_REGIONAL_OFFICER)


class ChainVerificationResponse(BaseModel):
    """Result of walking the hash chain."""

    ok: bool
    checked: int
    first_broken_entry_id: int | None = None
    reason: str | None = None


class AuditEntryResponse(BaseModel):
    id: int
    ts: datetime
    actor_id: uuid.UUID | None
    actor_role: Role | None
    action: str
    entity: str | None
    entity_id: str | None
    before_hash: str | None
    after_hash: str | None
    ip: str | None
    prev_hash: str
    entry_hash: str


@router.get(
    "/verify",
    response_model=ChainVerificationResponse,
    summary="Verify the audit hash chain",
)
def verify_chain(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_roles(*_AUDIT_READERS)),
) -> ChainVerificationResponse:
    """Walk the whole chain and report the first broken entry, if any.

    This is the check behind the AICTE portal's "Verify chain" button: `ok` means
    no row has been altered or removed since it was written, and
    `first_broken_entry_id` points at the exact row that no longer matches its
    own hash.
    """
    result = audit.verify_chain(db)
    return ChainVerificationResponse(**result.as_dict())


@router.get("", response_model=list[AuditEntryResponse], summary="Search the audit log")
def list_entries(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_roles(*_AUDIT_READERS)),
    action: Annotated[str | None, Query(description="Exact action name")] = None,
    entity: Annotated[str | None, Query(description="Exact entity name")] = None,
    entity_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Any]:
    """Most recent entries first, filterable by action and entity."""
    statement = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit).offset(offset)
    if action:
        statement = statement.where(AuditLog.action == action)
    if entity:
        statement = statement.where(AuditLog.entity == entity)
    if entity_id:
        statement = statement.where(AuditLog.entity_id == entity_id)

    return list(db.execute(statement).scalars())
