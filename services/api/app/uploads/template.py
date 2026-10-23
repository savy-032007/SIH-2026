"""The student-upload column contract (SPEC 10.1.3).

Single source of truth for the Excel/CSV upload format. The synthetic generator
writes files against it in Phase 1; the template-download endpoint and the parser
read it in Phase 2. One definition means the generated fixtures cannot drift away
from the format the parser accepts.

Header rows (SPEC section 11): row 1 is the label in the institution's chosen
language, row 2 is the English machine key. The parser keys off row 2, so a Hindi
or Marathi template uploads exactly like an English one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.models.enums import CourseLevel, EnrolmentCategory, Program

FieldKind = Literal["text", "date", "int", "enum", "digits"]


@dataclass(frozen=True)
class UploadColumn:
    """One column of the upload template."""

    #: Machine key written to header row 2 and used by the parser.
    key: str
    #: i18n key for the human label in header row 1.
    label_key: str
    kind: FieldKind
    required: bool
    #: Allowed values for `kind="enum"`, offered as an Excel dropdown.
    choices: tuple[str, ...] | None = None
    #: Shown in the template's notes row and in validation fix hints.
    hint_key: str | None = None
    width: int = 18


#: Boards seen in Indian admissions, plus FOREIGN for students with an overseas
#: qualification. V4.FN_INDIAN_BOARD keys off which of these is Indian, so the
#: list is not cosmetic.
QUALIFYING_BOARDS: tuple[str, ...] = (
    "CBSE",
    "CISCE",
    "NIOS",
    "MSBSHSE",
    "KSEEB",
    "TNBSE",
    "UPMSP",
    "IB",
    "CAIE",
    "FOREIGN",
)

#: Boards that are Indian. Anything outside this set is treated as non-Indian.
INDIAN_BOARDS: frozenset[str] = frozenset(
    {"CBSE", "CISCE", "NIOS", "MSBSHSE", "KSEEB", "TNBSE", "UPMSP"}
)

GENDERS: tuple[str, ...] = ("MALE", "FEMALE", "TRANSGENDER")

NATIONALITIES: tuple[str, ...] = (
    "Indian",
    "Nepalese",
    "Bhutanese",
    "Sri Lankan",
    "Bangladeshi",
    "Afghan",
    "Nigerian",
    "Kenyan",
    "Emirati",
    "Omani",
    "Malaysian",
    "Other",
)


COLUMNS: tuple[UploadColumn, ...] = (
    UploadColumn(
        key="apaar_id",
        label_key="upload.column.apaar_id",
        kind="digits",
        required=False,  # blank is allowed only for FN; V2.MISSING decides
        hint_key="upload.hint.apaar_id",
        width=16,
    ),
    UploadColumn(
        key="institution_student_id",
        label_key="upload.column.institution_student_id",
        kind="text",
        required=True,
        hint_key="upload.hint.institution_student_id",
    ),
    UploadColumn(key="name", label_key="upload.column.name", kind="text", required=True, width=28),
    UploadColumn(
        key="dob",
        label_key="upload.column.dob",
        kind="date",
        required=True,
        hint_key="upload.hint.date_format",
    ),
    UploadColumn(
        key="gender",
        label_key="upload.column.gender",
        kind="enum",
        required=True,
        choices=GENDERS,
        width=14,
    ),
    UploadColumn(key="phone", label_key="upload.column.phone", kind="digits", required=False),
    UploadColumn(key="email", label_key="upload.column.email", kind="text", required=False, width=28),
    UploadColumn(
        key="guardian_name",
        label_key="upload.column.guardian_name",
        kind="text",
        required=False,
        width=28,
    ),
    UploadColumn(
        key="address",
        label_key="upload.column.address",
        kind="text",
        required=False,
        hint_key="upload.hint.address",
        width=36,
    ),
    UploadColumn(
        key="nationality",
        label_key="upload.column.nationality",
        kind="enum",
        required=True,
        choices=NATIONALITIES,
        width=16,
    ),
    UploadColumn(
        key="qualifying_board",
        label_key="upload.column.qualifying_board",
        kind="enum",
        required=True,
        choices=QUALIFYING_BOARDS,
        width=18,
    ),
    UploadColumn(
        key="passport_no",
        label_key="upload.column.passport_no",
        kind="text",
        required=False,
        hint_key="upload.hint.passport_no",
    ),
    UploadColumn(
        key="course_name",
        label_key="upload.column.course_name",
        kind="text",
        required=True,
        width=36,
    ),
    UploadColumn(
        key="course_level",
        label_key="upload.column.course_level",
        kind="enum",
        required=True,
        choices=tuple(level.value for level in CourseLevel),
        width=14,
    ),
    UploadColumn(
        key="program",
        label_key="upload.column.program",
        kind="enum",
        required=True,
        choices=tuple(program.value for program in Program),
        width=16,
    ),
    UploadColumn(
        key="academic_year",
        label_key="upload.column.academic_year",
        kind="text",
        required=True,
        hint_key="upload.hint.academic_year",
        width=14,
    ),
    UploadColumn(
        key="admission_date",
        label_key="upload.column.admission_date",
        kind="date",
        required=True,
        hint_key="upload.hint.date_format",
    ),
    UploadColumn(
        key="category",
        label_key="upload.column.category",
        kind="enum",
        required=True,
        choices=tuple(category.value for category in EnrolmentCategory),
        hint_key="upload.hint.category",
        width=14,
    ),
    UploadColumn(
        key="oci_card_issue_date",
        label_key="upload.column.oci_card_issue_date",
        kind="date",
        required=False,
        hint_key="upload.hint.oci_card_issue_date",
    ),
    UploadColumn(
        key="nri_sponsor_doc_ref",
        label_key="upload.column.nri_sponsor_doc_ref",
        kind="text",
        required=False,
        hint_key="upload.hint.nri_sponsor_doc_ref",
        width=22,
    ),
)

#: Machine keys in template order.
COLUMN_KEYS: tuple[str, ...] = tuple(column.key for column in COLUMNS)

#: Lookup by machine key.
COLUMNS_BY_KEY: dict[str, UploadColumn] = {column.key: column for column in COLUMNS}

#: Name of the hidden sheet holding dropdown sources (SPEC 10.1.3).
LISTS_SHEET_NAME = "lists"
DATA_SHEET_NAME = "students"

#: Row indices in the generated workbook (1-based, as openpyxl counts).
HEADER_LABEL_ROW = 1
HEADER_KEY_ROW = 2
FIRST_DATA_ROW = 3

#: Seat type is derived from category and never uploaded (SPEC section 5), and
#: approved intake is AICTE-owned. Columns for either would invite institutions to
#: submit values the platform must then ignore, so neither exists.
EXCLUDED_BY_DESIGN: tuple[str, ...] = ("seat_type", "approved_intake", "apaar_status")


def english_labels() -> dict[str, str]:
    """Fallback English labels, used until the i18n message files land in Phase 4."""
    return {column.key: column.key.replace("_", " ").title() for column in COLUMNS}
