"""Upload batches and the validation issues they produce (SPEC sections 5–6)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pg_enum, uuid_pk
from app.models.enums import BatchStatus, IssueSeverity


class UploadBatch(Base, TimestampMixin):
    __tablename__ = "upload_batch"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institution.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[BatchStatus] = mapped_column(
        pg_enum(BatchStatus, "batch_status"), nullable=False, default=BatchStatus.VALIDATING
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    #: Written justification required to submit a batch that still has WARNINGs
    #: (SPEC 6.1). ERRORs block submission outright and cannot be justified away.
    warning_justification: Mapped[str | None] = mapped_column(Text)

    issues: Mapped[list["ValidationIssue"]] = relationship(back_populates="batch")


class ValidationIssue(Base, TimestampMixin):
    """One rule hit.

    `message_key` is an i18n key and `params` its interpolation values: the
    backend never returns English prose for user-facing messages (SPEC section 11).
    """

    __tablename__ = "validation_issue"

    id: Mapped[uuid.UUID] = uuid_pk()
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("upload_batch.id", ondelete="CASCADE"), index=True
    )
    enrolment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("enrolment.id", ondelete="CASCADE"), index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institution.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[IssueSeverity] = mapped_column(
        pg_enum(IssueSeverity, "issue_severity"), nullable=False
    )
    row_number: Mapped[int | None] = mapped_column(Integer)
    field: Mapped[str | None] = mapped_column(String(64))
    message_key: Mapped[str] = mapped_column(String(128), nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    batch: Mapped[UploadBatch | None] = relationship(back_populates="issues")
