"""Loading, activating and reading rule sets (SPEC section 7)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.rule_set import RuleSet
from app.rules.schema import RuleSetConfig
from app.security import audit


class RuleSetNotFoundError(LookupError):
    """No active rule set exists for the requested academic year."""


def load_config_file(path: Path) -> RuleSetConfig:
    """Parse and validate one rules JSON file."""
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    return RuleSetConfig.model_validate(raw)


def discover_config_files(rules_dir: Path | None = None) -> list[Path]:
    """Every `rules_<year>.json` in the rules directory, oldest year first."""
    directory = rules_dir or Path(get_settings().rules_dir)
    return sorted(directory.glob("rules_*.json"))


def upsert_rule_set(
    db: Session,
    config: RuleSetConfig,
    *,
    activate: bool = False,
    created_by: uuid.UUID | None = None,
) -> RuleSet:
    """Store a validated config as a new version for its academic year.

    Rule sets are append-only: editing a year's rules creates version N+1 rather
    than overwriting, so a flag raised last month can still be explained by the
    rules that were active then.
    """
    latest_version = db.execute(
        select(RuleSet.version)
        .where(RuleSet.academic_year == config.academic_year)
        .order_by(RuleSet.version.desc())
        .limit(1)
    ).scalar_one_or_none()

    payload = config.model_dump(mode="json")
    rule_set = RuleSet(
        academic_year=config.academic_year,
        version=(latest_version or 0) + 1,
        json=payload,
        created_by=created_by,
        active=False,
    )
    db.add(rule_set)
    db.flush()

    audit.append(
        db,
        action="RULE_SET_CREATED",
        actor_id=created_by,
        entity="rule_set",
        entity_id=str(rule_set.id),
        after={"academic_year": rule_set.academic_year, "version": rule_set.version},
    )

    if activate:
        activate_rule_set(db, rule_set, actor_id=created_by)

    return rule_set


def activate_rule_set(
    db: Session, rule_set: RuleSet, *, actor_id: uuid.UUID | None = None
) -> RuleSet:
    """Make this the active set for its year, deactivating any predecessor.

    A partial unique index allows only one active set per year, so the
    deactivation must happen in the same transaction as the activation.
    """
    db.execute(
        update(RuleSet)
        .where(
            RuleSet.academic_year == rule_set.academic_year,
            RuleSet.id != rule_set.id,
            RuleSet.active.is_(True),
        )
        .values(active=False)
    )
    db.flush()

    rule_set.active = True
    db.flush()

    audit.append(
        db,
        action="RULE_SET_ACTIVATED",
        actor_id=actor_id,
        entity="rule_set",
        entity_id=str(rule_set.id),
        after={"academic_year": rule_set.academic_year, "version": rule_set.version},
    )
    return rule_set


def get_active_rule_set(db: Session, academic_year: str) -> RuleSet:
    """The active rule set row for a year, or raise."""
    rule_set = db.execute(
        select(RuleSet).where(
            RuleSet.academic_year == academic_year, RuleSet.active.is_(True)
        )
    ).scalar_one_or_none()
    if rule_set is None:
        raise RuleSetNotFoundError(f"no active rule set for academic year {academic_year}")
    return rule_set


def get_active_config(db: Session, academic_year: str) -> RuleSetConfig:
    """The active config for a year, re-validated on the way out.

    Re-validating rather than trusting the stored JSON means a row edited
    directly in the database cannot feed the validation engine a cap it would
    accept blindly.
    """
    return RuleSetConfig.model_validate(get_active_rule_set(db, academic_year).json)


def load_all_from_disk(
    db: Session,
    *,
    activate_year: str | None = None,
    rules_dir: Path | None = None,
    created_by: uuid.UUID | None = None,
) -> list[RuleSet]:
    """Load every rules file on disk, activating one year.

    Used by `make seed`. Without `activate_year`, the latest year found wins.
    """
    paths = discover_config_files(rules_dir)
    if not paths:
        directory = rules_dir or Path(get_settings().rules_dir)
        raise FileNotFoundError(f"no rules_*.json files found in {directory}")

    configs = [load_config_file(path) for path in paths]
    target_year = activate_year or max(config.academic_year for config in configs)

    loaded: list[RuleSet] = []
    for config in configs:
        loaded.append(
            upsert_rule_set(
                db,
                config,
                activate=config.academic_year == target_year,
                created_by=created_by,
            )
        )
    return loaded
