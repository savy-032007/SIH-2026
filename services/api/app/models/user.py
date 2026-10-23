"""Platform users and per-institution API keys (SPEC sections 5, 8).

The table is `app_user`, not `user`: `user` is reserved in PostgreSQL and every
query would need quoting.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pg_enum, uuid_pk
from app.models.enums import Region, Role


class User(Base, TimestampMixin):
    __tablename__ = "app_user"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(pg_enum(Role, "user_role"), nullable=False)
    #: Set for INST_* roles; scopes every query to that institution.
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("institution.id", ondelete="CASCADE"), index=True
    )
    #: Set for AICTE_REGIONAL_OFFICER; scopes every query to that region.
    region: Mapped[Region | None] = mapped_column(pg_enum(Region, "region"))
    totp_secret_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<User {self.email} {self.role}>"


class ApiKey(Base, TimestampMixin):
    """Per-institution API key for machine-to-machine upload (SPEC R7).

    Only the hash is stored; the plaintext key is shown once at creation.
    """

    __tablename__ = "api_key"

    id: Mapped[uuid.UUID] = uuid_pk()
    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institution.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None
