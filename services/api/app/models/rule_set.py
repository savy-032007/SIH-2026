"""Versioned validation rule configuration, one set per academic year (SPEC section 7)."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk


class RuleSet(Base, TimestampMixin):
    __tablename__ = "rule_set"
    __table_args__ = (
        UniqueConstraint("academic_year", "version", name="uq_rule_set_academic_year_version"),
        # At most one active rule set per year, enforced by the database rather
        # than by whoever remembers to deactivate the old one.
        Index(
            "uq_rule_set_active_per_year",
            "academic_year",
            unique=True,
            postgresql_where=text("active"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    academic_year: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<RuleSet {self.academic_year} v{self.version} active={self.active}>"
