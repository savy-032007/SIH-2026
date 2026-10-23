"""Signed, publicly verifiable student records (SPEC R6, R10, section 10.3).

`payload_json` is the exact object the Ed25519 signature covers. It is never
rebuilt from live rows at verification time — verification re-signs this stored
payload, so editing any student row afterwards cannot forge a Valid result, and
editing the payload itself breaks the signature.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk


class Certificate(Base, TimestampMixin):
    __tablename__ = "certificate"

    id: Mapped[uuid.UUID] = uuid_pk()
    enrolment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("enrolment.id", ondelete="CASCADE"), nullable=False, index=True
    )
    #: Human-readable, printed on the certificate, e.g. AICTE-2026-7F3A91C2.
    cert_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    key_id: Mapped[str] = mapped_column(String(64), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoke_reason: Mapped[str | None] = mapped_column(Text)

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None
