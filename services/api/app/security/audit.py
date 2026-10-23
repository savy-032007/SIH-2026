"""Tamper-evident audit trail (SPEC section 8).

    entry_hash = SHA256(prev_hash || canonical_json(entry))

Every write and every PII reveal appends one entry. Because each hash commits to
the one before it, changing or deleting any historical row invalidates every entry
after it — which is what makes the demo's `tamper_demo.py` detectable rather than
a matter of trust.

Two details that decide whether the chain actually holds:

* **Serialisation.** Two concurrent appends that both read the same tail would
  fork the chain. Every append therefore takes a transaction-scoped advisory lock
  first, so tail-read and insert are atomic with respect to other appenders.
* **Timestamps are set in Python, not by the database.** The hash covers `ts`, so
  the value hashed must be exactly the value stored — a `server_default` would be
  assigned after hashing and never verify.

`id` is excluded from the hashed payload: it is assigned by the sequence on
insert, and ordering is already pinned by the `prev_hash` links.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.audit import GENESIS_HASH, AuditLog
from app.models.enums import Role

#: Constant key for the advisory lock that serialises appends.
_AUDIT_LOCK_KEY = 8_742_119_004_512_337


def canonical_json(payload: dict[str, Any]) -> str:
    """Stable JSON for hashing: sorted keys, no incidental whitespace.

    Also used for certificate payloads in Phase 4 — a signature is only
    reproducible if the bytes are.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def _hashed_payload(entry: AuditLog) -> dict[str, Any]:
    """The fields the entry hash commits to."""
    return {
        "ts": entry.ts.astimezone(UTC).isoformat(),
        "actor_id": str(entry.actor_id) if entry.actor_id else None,
        "actor_role": str(entry.actor_role) if entry.actor_role else None,
        "action": entry.action,
        "entity": entry.entity,
        "entity_id": entry.entity_id,
        "before_hash": entry.before_hash,
        "after_hash": entry.after_hash,
        "ip": entry.ip,
        "prev_hash": entry.prev_hash,
    }


def compute_entry_hash(entry: AuditLog) -> str:
    body = f"{entry.prev_hash}{canonical_json(_hashed_payload(entry))}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def state_hash(state: dict[str, Any] | None) -> str | None:
    """Hash of a before/after state snapshot.

    The log records these hashes rather than the states themselves, so it proves
    what changed without becoming a second, unencrypted copy of the PII.
    """
    if state is None:
        return None
    return hashlib.sha256(canonical_json(state).encode("utf-8")).hexdigest()


def append(
    session: Session,
    *,
    action: str,
    actor_id: uuid.UUID | None = None,
    actor_role: Role | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditLog:
    """Append one entry, linked to the current chain tail.

    Flushed but not committed: the entry lands in the caller's transaction, so an
    audited write and its audit record commit or roll back together.
    """
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _AUDIT_LOCK_KEY})

    prev_hash = session.execute(
        select(AuditLog.entry_hash).order_by(AuditLog.id.desc()).limit(1)
    ).scalar_one_or_none()

    entry = AuditLog(
        ts=datetime.now(UTC),
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        entity=entity,
        entity_id=entity_id,
        before_hash=state_hash(before),
        after_hash=state_hash(after),
        ip=ip,
        prev_hash=prev_hash or GENESIS_HASH,
    )
    entry.entry_hash = compute_entry_hash(entry)
    session.add(entry)
    session.flush()
    return entry


def record_pii_reveal(
    session: Session,
    *,
    actor_id: uuid.UUID,
    actor_role: Role,
    entity: str,
    entity_id: str,
    fields: list[str],
    ip: str | None = None,
) -> AuditLog:
    """Audit an unmasked PII view (SPEC section 8: every reveal is audited)."""
    return append(
        session,
        action="PII_REVEAL",
        actor_id=actor_id,
        actor_role=actor_role,
        entity=entity,
        entity_id=entity_id,
        after={"fields": sorted(fields)},
        ip=ip,
    )


@dataclass(frozen=True)
class ChainVerification:
    """Outcome of walking the whole chain."""

    ok: bool
    checked: int
    first_broken_entry_id: int | None = None
    #: Which invariant failed: "entry_hash" (row edited) or "prev_hash" (row
    #: deleted or inserted out of order).
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checked": self.checked,
            "first_broken_entry_id": self.first_broken_entry_id,
            "reason": self.reason,
        }


def verify_chain(session: Session, *, batch_size: int = 1000) -> ChainVerification:
    """Walk the chain in id order and return the first break, if any.

    Streams in batches so a log with millions of entries does not have to fit in
    memory.
    """
    expected_prev = GENESIS_HASH
    checked = 0

    entries = session.execute(select(AuditLog).order_by(AuditLog.id)).scalars()
    for entry in entries.yield_per(batch_size):
        if entry.prev_hash != expected_prev:
            return ChainVerification(
                ok=False,
                checked=checked,
                first_broken_entry_id=entry.id,
                reason="prev_hash",
            )
        if compute_entry_hash(entry) != entry.entry_hash:
            return ChainVerification(
                ok=False,
                checked=checked,
                first_broken_entry_id=entry.id,
                reason="entry_hash",
            )
        expected_prev = entry.entry_hash
        checked += 1

    return ChainVerification(ok=True, checked=checked)
