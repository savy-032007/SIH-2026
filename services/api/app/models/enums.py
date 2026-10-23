"""Controlled vocabularies from SPEC section 5.

Everything the SPEC enumerates explicitly becomes a native PostgreSQL enum, so
bad values fail at the database rather than silently becoming rows nobody
notices. The trade-off is that adding a value needs an Alembic migration.

`flag.type` is the deliberate exception and stays a plain string: SPEC section 5
gives it no vocabulary and Phase 3 owns that taxonomy.
"""

from enum import StrEnum


class Region(StrEnum):
    NORTHERN = "NORTHERN"
    SOUTHERN = "SOUTHERN"
    EASTERN = "EASTERN"
    WESTERN = "WESTERN"
    CENTRAL = "CENTRAL"
    NORTH_EASTERN = "NORTH_EASTERN"
    SOUTH_WESTERN = "SOUTH_WESTERN"


class InstitutionType(StrEnum):
    GOVT = "GOVT"
    PRIVATE = "PRIVATE"
    DEEMED = "DEEMED"


class CourseLevel(StrEnum):
    DIPLOMA = "DIPLOMA"
    UG = "UG"
    PG = "PG"


class Program(StrEnum):
    ENGINEERING = "ENGINEERING"
    MANAGEMENT = "MANAGEMENT"
    DESIGN = "DESIGN"
    OTHER_TECH = "OTHER_TECH"


class EnrolmentCategory(StrEnum):
    REGULAR = "REGULAR"
    NRI = "NRI"
    FN = "FN"
    OCI = "OCI"
    PIO = "PIO"
    CIWGC = "CIWGC"


class SeatType(StrEnum):
    WITHIN_INTAKE = "WITHIN_INTAKE"
    SUPERNUMERARY = "SUPERNUMERARY"


class EnrolmentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"
    COMPLETED = "COMPLETED"


class ApaarStatus(StrEnum):
    VERIFIED = "VERIFIED"
    PENDING_CONSENT = "PENDING_CONSENT"
    MISMATCH = "MISMATCH"
    NOT_FOUND = "NOT_FOUND"
    EXEMPT = "EXEMPT"


class DocumentKind(StrEnum):
    NRI_SPONSOR = "NRI_SPONSOR"
    PASSPORT = "PASSPORT"
    OCI_CARD = "OCI_CARD"
    VISA = "VISA"
    OTHER = "OTHER"


class BatchStatus(StrEnum):
    VALIDATING = "VALIDATING"
    HAS_ERRORS = "HAS_ERRORS"
    READY = "READY"
    SUBMITTED = "SUBMITTED"


class IssueSeverity(StrEnum):
    """Severity of a validation issue.

    SPEC 6.1 uses ERROR and WARNING for blocking/non-blocking issues, plus INFO
    for classification-only rules such as V4.OCI_CLASSIFICATION.
    """

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class FlagSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FlagStatus(StrEnum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    SENT_TO_INSTITUTION = "SENT_TO_INSTITUTION"
    INSTITUTION_RESPONDED = "INSTITUTION_RESPONDED"
    CONFIRMED_VIOLATION = "CONFIRMED_VIOLATION"
    CLEARED = "CLEARED"


class Role(StrEnum):
    AICTE_SUPER_ADMIN = "AICTE_SUPER_ADMIN"
    AICTE_REGIONAL_OFFICER = "AICTE_REGIONAL_OFFICER"
    AICTE_ANALYST = "AICTE_ANALYST"
    INST_ADMIN = "INST_ADMIN"
    INST_OPERATOR = "INST_OPERATOR"


class ConsentPurpose(StrEnum):
    APAAR_VERIFICATION = "APAAR_VERIFICATION"


class ConsentChannel(StrEnum):
    OTP = "OTP"
    DIGILOCKER = "DIGILOCKER"


#: Roles that act inside the AICTE portal.
AICTE_ROLES: frozenset[Role] = frozenset(
    {Role.AICTE_SUPER_ADMIN, Role.AICTE_REGIONAL_OFFICER, Role.AICTE_ANALYST}
)

#: Roles that act inside an institution portal.
INSTITUTION_ROLES: frozenset[Role] = frozenset({Role.INST_ADMIN, Role.INST_OPERATOR})

#: TOTP MFA is mandatory for these roles (SPEC section 8).
MFA_REQUIRED_ROLES: frozenset[Role] = frozenset(
    {
        Role.AICTE_SUPER_ADMIN,
        Role.AICTE_REGIONAL_OFFICER,
        Role.AICTE_ANALYST,
        Role.INST_ADMIN,
    }
)

#: Categories that occupy seats within the approved intake (SPEC 6.1 V3).
WITHIN_INTAKE_CATEGORIES: frozenset[EnrolmentCategory] = frozenset(
    {EnrolmentCategory.REGULAR, EnrolmentCategory.NRI}
)

#: Categories that occupy supernumerary seats (SPEC 6.1 V3).
SUPERNUMERARY_CATEGORIES: frozenset[EnrolmentCategory] = frozenset(
    {
        EnrolmentCategory.FN,
        EnrolmentCategory.OCI,
        EnrolmentCategory.PIO,
        EnrolmentCategory.CIWGC,
    }
)


def derive_seat_type(category: EnrolmentCategory) -> SeatType:
    """Map an admission category to its seat type.

    SPEC section 5: seat_type is derived from category and is never user-entered,
    so institutions cannot reclassify a within-intake admission as supernumerary
    to dodge the V3 intake caps.
    """
    if category in SUPERNUMERARY_CATEGORIES:
        return SeatType.SUPERNUMERARY
    if category in WITHIN_INTAKE_CATEGORIES:
        return SeatType.WITHIN_INTAKE
    raise ValueError(f"no seat type mapping for category {category!r}")


#: Known anomaly flag types. Phase 3 owns this taxonomy; stored as plain text so
#: new detectors do not each need a migration.
FLAG_TYPE_INSTITUTION_OUTLIER = "INSTITUTION_OUTLIER"
FLAG_TYPE_GHOST_CLUSTER = "GHOST_CLUSTER"
FLAG_TYPE_CROSS_INSTITUTION_DUPLICATE = "CROSS_INSTITUTION_DUPLICATE"
FLAG_TYPE_OVER_INTAKE = "OVER_INTAKE"
FLAG_TYPE_RULE_VIOLATION = "RULE_VIOLATION"
