"""Institutions and their AICTE-approved courses (SPEC section 5)."""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pg_enum, uuid_pk
from app.models.enums import CourseLevel, InstitutionType, Program, Region


class Institution(Base, TimestampMixin):
    __tablename__ = "institution"

    id: Mapped[uuid.UUID] = uuid_pk()
    aicte_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[Region] = mapped_column(
        pg_enum(Region, "region"), nullable=False, index=True
    )
    type: Mapped[InstitutionType] = mapped_column(
        pg_enum(InstitutionType, "institution_type"), nullable=False
    )
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)

    courses: Mapped[list["Course"]] = relationship(back_populates="institution")

    def __repr__(self) -> str:
        return f"<Institution {self.aicte_id} {self.name!r}>"


class Course(Base, TimestampMixin):
    """An approved course offering for one academic year.

    `approved_intake` is set by AICTE. Institutions can read it but never write
    it (SPEC section 5) — enforced in the institution routers, not here.
    """

    __tablename__ = "course"
    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "name",
            "level",
            "academic_year",
            name="uq_course_institution_name_level_year",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institution.id", ondelete="CASCADE"), nullable=False, index=True
    )
    level: Mapped[CourseLevel] = mapped_column(pg_enum(CourseLevel, "course_level"), nullable=False)
    program: Mapped[Program] = mapped_column(pg_enum(Program, "program"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    approved_intake: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_year: Mapped[str] = mapped_column(String(7), nullable=False, index=True)

    institution: Mapped[Institution] = relationship(back_populates="courses")

    def __repr__(self) -> str:
        return f"<Course {self.name!r} {self.level} intake={self.approved_intake}>"
