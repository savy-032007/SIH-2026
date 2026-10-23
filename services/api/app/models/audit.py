"""Tamper-evident audit log (SPEC section 8).

Each row carries the hash of the previous row, so `entry_hash` of row N commits
to the entire history before it. Editing or deleting any earlier row breaks every
later link, which `GET /api/v1/audit/verify` detects and localises.

Append-only by contract: nothing in the application updates or deletes these rows.
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, pg_enum
from app.models.enums import Role

#: `prev_hash` of the first entry in the chain.
GENESIS_HASH = "0" * 64


class AuditLog(Base):
    __tablename__ = "audit_log"

    # bigserial, and the chain order: entries are verified in id order.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    # Deliberately not a foreign key: an audit entry must outlive the user it
    # refers to, and a cascade must never be able to erase history.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), index=True)
    actor_role: Mapped[Role | None] = mapped_column(pg_enum(Role, "user_role"))
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(64), index=True)
    #: Hashes of the before/after state rather than the state itself, so the log
    #: proves what changed without becoming a second copy of the PII.
    before_hash: Mapped[str | None] = mapped_column(String(64))
    after_hash: Mapped[str | None] = mapped_column(String(64))
    ip: Mapped[str | None] = mapped_column(String(45))
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} {self.action} {self.entry_hash[:8]}>"
