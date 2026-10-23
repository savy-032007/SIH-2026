"""Student consent for APAAR verification (SPEC section 8).

No APAAR data is fetched from the registry or DigiLocker before a granted,
unrevoked consent row exists for that student and purpose.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pg_enum, uuid_pk
from app.models.enums import ConsentChannel, ConsentPurpose


class Consent(Base, TimestampMixin):
    __tablename__ = "consent"

    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("student.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purpose: Mapped[ConsentPurpose] = mapped_column(
        pg_enum(ConsentPurpose, "consent_purpose"), nullable=False
    )
    channel: Mapped[ConsentChannel] = mapped_column(
        pg_enum(ConsentChannel, "consent_channel"), nullable=False
    )
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    #: Hash of the one-time consent link token — the token itself is never stored.
    token_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    ip: Mapped[str | None] = mapped_column(String(45))

    @property
    def is_active(self) -> bool:
        return self.granted_at is not None and self.revoked_at is None
