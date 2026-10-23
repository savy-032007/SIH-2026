"""SQLAlchemy models for the APAAR platform (SPEC section 5).

Importing this package registers every table on `Base.metadata`, which is what
Alembic autogenerate reads.
"""

from app.models.audit import GENESIS_HASH, AuditLog
from app.models.base import Base
from app.models.certificate import Certificate
from app.models.consent import Consent
from app.models.enums import (
    AICTE_ROLES,
    INSTITUTION_ROLES,
    MFA_REQUIRED_ROLES,
    SUPERNUMERARY_CATEGORIES,
    WITHIN_INTAKE_CATEGORIES,
    ApaarStatus,
    BatchStatus,
    ConsentChannel,
    ConsentPurpose,
    CourseLevel,
    DocumentKind,
    EnrolmentCategory,
    EnrolmentStatus,
    FlagSeverity,
    FlagStatus,
    InstitutionType,
    IssueSeverity,
    Program,
    Region,
    Role,
    SeatType,
    derive_seat_type,
)
from app.models.flag import Flag
from app.models.institution import Course, Institution
from app.models.rule_set import RuleSet
from app.models.student import Document, Enrolment, EnrolmentVersion, Student
from app.models.upload import UploadBatch, ValidationIssue
from app.models.user import ApiKey, User

__all__ = [
    "AICTE_ROLES",
    "GENESIS_HASH",
    "INSTITUTION_ROLES",
    "MFA_REQUIRED_ROLES",
    "SUPERNUMERARY_CATEGORIES",
    "WITHIN_INTAKE_CATEGORIES",
    "ApaarStatus",
    "ApiKey",
    "AuditLog",
    "Base",
    "BatchStatus",
    "Certificate",
    "Consent",
    "ConsentChannel",
    "ConsentPurpose",
    "Course",
    "CourseLevel",
    "Document",
    "DocumentKind",
    "Enrolment",
    "EnrolmentCategory",
    "EnrolmentStatus",
    "EnrolmentVersion",
    "Flag",
    "FlagSeverity",
    "FlagStatus",
    "Institution",
    "InstitutionType",
    "IssueSeverity",
    "Program",
    "Region",
    "Role",
    "RuleSet",
    "SeatType",
    "Student",
    "UploadBatch",
    "User",
    "ValidationIssue",
    "derive_seat_type",
]
