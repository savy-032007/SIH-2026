"""Students, enrolments, enrolment version history and supporting documents.

Every direct identifier is stored twice: AES-256-GCM ciphertext for retrieval and
an HMAC-SHA256 hash for equality lookups and uniqueness. Aadhaar is never
collected or stored (SPEC section 8).
"""

import uuid
from datetime import date

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pg_enum, uuid_pk
from app.models.enums import (
    ApaarStatus,
    DocumentKind,
    EnrolmentCategory,
    EnrolmentStatus,
    SeatType,
)


class Student(Base, TimestampMixin):
    __tablename__ = "student"
    __table_args__ = (
        Index("ix_student_phone_hash", "phone_hash"),
        Index("ix_student_email_hash", "email_hash"),
        Index("ix_student_address_hash", "address_hash"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()

    # APAAR ID — the platform's unique student key (SPEC R1).
    apaar_id_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    apaar_id_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    apaar_last4: Mapped[str | None] = mapped_column(String(4))

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)

    phone_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    phone_hash: Mapped[str | None] = mapped_column(String(64))
    email_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    email_hash: Mapped[str | None] = mapped_column(String(64))

    guardian_name: Mapped[str | None] = mapped_column(String(255))
    #: Hash of the normalized address — powers the ghost-student graph (SPEC 6.2)
    #: without keeping the address itself.
    address_hash: Mapped[str | None] = mapped_column(String(64))

    nationality: Mapped[str] = mapped_column(String(64), nullable=False, default="Indian")
    qualifying_board: Mapped[str | None] = mapped_column(String(64))
    #: FN and OCI students only.
    passport_no_enc: Mapped[bytes | None] = mapped_column(LargeBinary)

    enrolments: Mapped[list["Enrolment"]] = relationship(back_populates="student")

    def __repr__(self) -> str:
        return f"<Student {self.name!r} apaar=****{self.apaar_last4}>"


class Enrolment(Base, TimestampMixin):
    __tablename__ = "enrolment"
    __table_args__ = (
        Index("ix_enrolment_academic_year_status", "academic_year", "status"),
        Index("ix_enrolment_institution_id_course_id", "institution_id", "course_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("student.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institution.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("course.id", ondelete="CASCADE"), nullable=False
    )
    academic_year: Mapped[str] = mapped_column(String(7), nullable=False)
    admission_date: Mapped[date] = mapped_column(Date, nullable=False)

    #: The institution's own roll/enrolment number. Not listed in SPEC section 5,
    #: but R10 and SPEC 10.1.7 require the certificate to print the APAAR ID and
    #: the institution student ID together, which is impossible without storing
    #: it. Added for that requirement only.
    institution_student_id: Mapped[str | None] = mapped_column(String(64))

    category: Mapped[EnrolmentCategory] = mapped_column(
        pg_enum(EnrolmentCategory, "enrolment_category"), nullable=False
    )
    #: Derived from `category` via models.enums.derive_seat_type — never user-entered.
    seat_type: Mapped[SeatType] = mapped_column(pg_enum(SeatType, "seat_type"), nullable=False)

    oci_card_issue_date: Mapped[date | None] = mapped_column(Date)
    nri_sponsor_doc_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document.id", ondelete="SET NULL", use_alter=True)
    )

    status: Mapped[EnrolmentStatus] = mapped_column(
        pg_enum(EnrolmentStatus, "enrolment_status"),
        nullable=False,
        default=EnrolmentStatus.ACTIVE,
    )
    apaar_status: Mapped[ApaarStatus] = mapped_column(
        pg_enum(ApaarStatus, "apaar_status"),
        nullable=False,
        default=ApaarStatus.PENDING_CONSENT,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    student: Mapped[Student] = relationship(back_populates="enrolments")
    versions: Mapped[list["EnrolmentVersion"]] = relationship(back_populates="enrolment")

    def __repr__(self) -> str:
        return f"<Enrolment {self.id} {self.category} v{self.version}>"


class EnrolmentVersion(Base, TimestampMixin):
    """Full snapshot of an enrolment after every change (SPEC R1 update history)."""

    __tablename__ = "enrolment_version"
    __table_args__ = (
        UniqueConstraint("enrolment_id", "version", name="uq_enrolment_version_enrolment_version"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    enrolment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("enrolment.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
    change_reason: Mapped[str | None] = mapped_column(Text)

    enrolment: Mapped[Enrolment] = relationship(back_populates="versions")


class Document(Base, TimestampMixin):
    __tablename__ = "document"

    id: Mapped[uuid.UUID] = uuid_pk()
    enrolment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("enrolment.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[DocumentKind] = mapped_column(pg_enum(DocumentKind, "document_kind"), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
