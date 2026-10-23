"""Rule set reading (SPEC section 7).

Read-only in Phase 1. The editable Rules Manager with year-over-year diffing and
activation is Phase 4 (SPEC 10.2.6) — until then the committed JSON files and
`make seed` are the only way rules change, which keeps the Phase 2 validation
engine aimed at a fixed target.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.rule_set import RuleSet
from app.rules import RuleSetNotFoundError, get_active_config, get_active_rule_set
from app.rules.schema import RuleSetConfig
from app.security.rbac import CurrentUser, get_current_user

router = APIRouter(prefix="/rules", tags=["rules"])


class RuleSetSummary(BaseModel):
    id: uuid.UUID
    academic_year: str
    version: int
    active: bool
    created_at: datetime


class RuleSetDetail(RuleSetSummary):
    config: RuleSetConfig


@router.get("", response_model=list[RuleSetSummary], summary="List all rule sets")
def list_rule_sets(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
) -> list[Any]:
    """Every rule set version, newest year first.

    Readable by all authenticated roles: institutions need to know the caps their
    data will be judged against.
    """
    statement = select(RuleSet).order_by(RuleSet.academic_year.desc(), RuleSet.version.desc())
    return [
        RuleSetSummary(
            id=row.id,
            academic_year=row.academic_year,
            version=row.version,
            active=row.active,
            created_at=row.created_at,
        )
        for row in db.execute(statement).scalars()
    ]


@router.get(
    "/{academic_year}",
    response_model=RuleSetDetail,
    responses={404: {"description": "No active rule set for that academic year"}},
    summary="Get the active rule set for an academic year",
)
def get_rule_set(
    academic_year: str,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
) -> RuleSetDetail:
    """The active, re-validated configuration for one year."""
    try:
        row = get_active_rule_set(db, academic_year)
        config = get_active_config(db, academic_year)
    except RuleSetNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return RuleSetDetail(
        id=row.id,
        academic_year=row.academic_year,
        version=row.version,
        active=row.active,
        created_at=row.created_at,
        config=config,
    )
