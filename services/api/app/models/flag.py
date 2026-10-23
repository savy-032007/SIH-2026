"""AICTE-side anomaly flags and their resolution workflow (SPEC sections 5, 10.2.2)."""

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.models.base import Base, TimestampMixin, pg_enum, uuid_pk
from app.models.enums import FlagSeverity, FlagStatus


class Flag(Base, TimestampMixin):
    __tablename__ = "flag"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institution.id", ondelete="CASCADE"), nullable=False, index=True
    )
    #: The enrolments this flag is about. Plain array rather than a join table:
    #: flags are read as whole evidence bundles, never joined through.
    enrolment_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=False, default=list
    )
    #: See app.models.enums FLAG_TYPE_* constants. Plain text because SPEC
    #: section 5 gives no vocabulary and Phase 3 owns the taxonomy.
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[FlagSeverity] = mapped_column(
        pg_enum(FlagSeverity, "flag_severity"), nullable=False, index=True
    )
    reason_key: Mapped[str] = mapped_column(String(128), nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[FlagStatus] = mapped_column(
        pg_enum(FlagStatus, "flag_status"), nullable=False, default=FlagStatus.OPEN, index=True
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
    institution_response: Mapped[str | None] = mapped_column(Text)
    response_docs: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(Uuid(as_uuid=True)))

    def __repr__(self) -> str:
        return f"<Flag {self.type} {self.severity} {self.status}>"
