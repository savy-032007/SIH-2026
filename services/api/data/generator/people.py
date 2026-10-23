"""Synthetic people, institutions and courses (SPEC 9.2).

Everything here is deterministic given a seed: same seed, byte-identical dataset,
which is what lets `test_generator` assert reproducibility and the demo be reset
without changing what the validation engine should find.

No real personal data. Every generated APAAR ID starts with `SYNTHETIC_APAAR_PREFIX`
so a stray record can always be told apart from a real one at a glance, and a test
asserts it.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta

from rapidfuzz import fuzz

from generator.reference import (
    COURSE_CATALOGUE,
    FIRST_NAMES_FEMALE,
    FIRST_NAMES_MALE,
    FOREIGN_BOARDS,
    FOREIGN_COUNTRIES,
    INSTITUTION_NAME_CORES,
    INSTITUTION_NAME_PREFIXES,
    INTAKE_OPTIONS,
    STATES,
    STREET_NAMES,
    SURNAMES,
    StateRef,
    email_domains,
)

#: Every synthetic APAAR ID begins with this, so synthetic data is identifiable
#: on sight. Real APAAR IDs are 12 digits with no published structure, so this
#: costs nothing in format realism — V2.FORMAT checks length and digits only.
SYNTHETIC_APAAR_PREFIX = "99"

APAAR_LENGTH = 12

ACADEMIC_YEARS: tuple[str, ...] = ("2025-26", "2026-27")

#: Indian academic year runs July-June; admissions cluster in the first months.
ADMISSION_WINDOWS: dict[str, tuple[date, date]] = {
    "2025-26": (date(2025, 6, 15), date(2025, 9, 30)),
    "2026-27": (date(2026, 6, 15), date(2026, 9, 30)),
}

#: Typical age at admission by level, used to derive a plausible date of birth.
_AGE_AT_ADMISSION: dict[str, tuple[int, int]] = {
    "DIPLOMA": (15, 19),
    "UG": (17, 22),
    "PG": (20, 28),
}


@dataclass
class InstitutionRecord:
    aicte_id: str
    name: str
    state: str
    district: str
    region: str
    type: str
    lat: float
    lng: float


@dataclass
class CourseRecord:
    institution_aicte_id: str
    level: str
    program: str
    name: str
    approved_intake: int
    academic_year: str

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (self.institution_aicte_id, self.name, self.level, self.academic_year)


@dataclass
class StudentRecord:
    """One synthetic student plus the enrolment that goes with them.

    Student and enrolment travel together because the generator always creates
    them as a pair; the seeder splits them across the two tables.
    """

    apaar_id: str | None
    name: str
    dob: date
    gender: str
    phone: str
    email: str
    guardian_name: str
    address: str
    nationality: str
    qualifying_board: str
    passport_no: str | None

    institution_aicte_id: str
    institution_student_id: str
    course_name: str
    course_level: str
    program: str
    academic_year: str
    admission_date: date
    category: str
    oci_card_issue_date: date | None
    nri_sponsor_doc_ref: str | None

    status: str = "ACTIVE"
    #: The name the registry holds, when it differs from `name` (planted
    #: V2.NAME_MISMATCH cases). None means the registry agrees.
    registry_name: str | None = None
    #: False for planted V2.NOT_FOUND cases.
    in_registry: bool = True
    #: Planted case ids this record participates in.
    planted_cases: list[str] = field(default_factory=list)

    @property
    def registry_truth_name(self) -> str:
        return self.registry_name or self.name


class Generator:
    """Seeded factory for the whole synthetic universe."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self._used_apaar: set[str] = set()
        self._used_phone: set[str] = set()
        self._used_email: set[str] = set()
        self._roll_counters: dict[tuple[str, str], int] = {}

    # --- primitives ------------------------------------------------------- #

    def apaar_id(self) -> str:
        """A unique 12-digit synthetic APAAR ID."""
        while True:
            body = "".join(
                str(self.rng.randint(0, 9))
                for _ in range(APAAR_LENGTH - len(SYNTHETIC_APAAR_PREFIX))
            )
            candidate = SYNTHETIC_APAAR_PREFIX + body
            if candidate not in self._used_apaar:
                self._used_apaar.add(candidate)
                return candidate

    def reserve_apaar(self, apaar_id: str) -> None:
        self._used_apaar.add(apaar_id)

    def phone(self) -> str:
        while True:
            candidate = str(self.rng.choice([6, 7, 8, 9])) + "".join(
                str(self.rng.randint(0, 9)) for _ in range(9)
            )
            if candidate not in self._used_phone:
                self._used_phone.add(candidate)
                return candidate

    def email_for(self, name: str) -> str:
        slug = name.lower().replace(" ", ".")
        while True:
            candidate = f"{slug}{self.rng.randint(1, 9999)}@{self.rng.choice(email_domains())}"
            if candidate not in self._used_email:
                self._used_email.add(candidate)
                return candidate

    def person_name(self, gender: str) -> str:
        pool = FIRST_NAMES_FEMALE if gender == "FEMALE" else FIRST_NAMES_MALE
        return f"{self.rng.choice(pool)} {self.rng.choice(SURNAMES)}"

    def guardian_name(self, student_name: str) -> str:
        """A guardian sharing the student's surname, as is usual."""
        surname = student_name.split()[-1]
        return f"{self.rng.choice(FIRST_NAMES_MALE)} {surname}"

    def address(self, district: str, state: str) -> str:
        return (
            f"{self.rng.randint(1, 240)}, {self.rng.choice(STREET_NAMES)}, "
            f"{district}, {state} - {self.rng.randint(110000, 699999)}"
        )

    def roll_number(self, aicte_id: str, academic_year: str) -> str:
        """Institution's own student id, sequential per institution and year."""
        key = (aicte_id, academic_year)
        self._roll_counters[key] = self._roll_counters.get(key, 0) + 1
        short = aicte_id.split("-")[-1][-4:]
        return f"{short}{academic_year[:4]}{self._roll_counters[key]:05d}"

    def dob_for(self, level: str, admission: date) -> date:
        low, high = _AGE_AT_ADMISSION[level]
        age = self.rng.randint(low, high)
        return admission - timedelta(days=age * 365 + self.rng.randint(0, 364))

    def admission_date(self, academic_year: str) -> date:
        start, end = ADMISSION_WINDOWS[academic_year]
        return start + timedelta(days=self.rng.randint(0, (end - start).days))

    # --- institutions and courses ----------------------------------------- #

    def institutions(self, count: int) -> list[InstitutionRecord]:
        """Institutions spread across the reference states.

        Maharashtra gets the largest share because the demo script walks through
        a Maharashtra institution.
        """
        weights = [4, 2, 2, 2]  # Maharashtra, Karnataka, Tamil Nadu, Uttar Pradesh
        records: list[InstitutionRecord] = []
        used_names: set[str] = set()

        for index in range(count):
            state: StateRef = self.rng.choices(STATES, weights=weights, k=1)[0]
            district = self.rng.choice(state.districts)

            while True:
                name = (
                    f"{self.rng.choice(INSTITUTION_NAME_PREFIXES)} "
                    f"{self.rng.choice(INSTITUTION_NAME_CORES)}, {district}"
                )
                if name not in used_names:
                    used_names.add(name)
                    break

            records.append(
                InstitutionRecord(
                    # AICTE permanent id shape, e.g. 1-3482910756
                    aicte_id=f"1-{self.rng.randint(1_000_000_000, 9_999_999_999)}",
                    name=name,
                    state=state.name,
                    district=district,
                    region=state.region,
                    type=self.rng.choices(
                        ["PRIVATE", "GOVT", "DEEMED"], weights=[7, 2, 1], k=1
                    )[0],
                    # Jitter around the state centroid so map pins separate.
                    lat=round(state.lat + self.rng.uniform(-1.6, 1.6), 5),
                    lng=round(state.lng + self.rng.uniform(-1.6, 1.6), 5),
                )
            )
        return records

    def courses_for(self, institution: InstitutionRecord) -> list[CourseRecord]:
        """3-6 courses per institution, offered in both academic years.

        The same course keeps its intake across years, so a year-over-year
        enrolment jump (the planted outlier case) is unambiguous.
        """
        how_many = self.rng.randint(3, 6)
        catalogue_keys = list(COURSE_CATALOGUE.keys())
        chosen: list[tuple[str, str, str, int]] = []
        seen: set[tuple[str, str]] = set()

        attempts = 0
        while len(chosen) < how_many and attempts < how_many * 12:
            attempts += 1
            level, program = self.rng.choices(
                catalogue_keys,
                weights=[
                    9 if key == ("UG", "ENGINEERING") else 2 for key in catalogue_keys
                ],
                k=1,
            )[0]
            name = self.rng.choice(COURSE_CATALOGUE[(level, program)])
            if (name, level) in seen:
                continue
            seen.add((name, level))
            chosen.append((level, program, name, self.rng.choice(INTAKE_OPTIONS)))

        return [
            CourseRecord(
                institution_aicte_id=institution.aicte_id,
                level=level,
                program=program,
                name=name,
                approved_intake=intake,
                academic_year=year,
            )
            for level, program, name, intake in chosen
            for year in ACADEMIC_YEARS
        ]

    # --- students --------------------------------------------------------- #

    def student(
        self,
        *,
        institution: InstitutionRecord,
        course: CourseRecord,
        category: str,
        academic_year: str,
        status: str = "ACTIVE",
    ) -> StudentRecord:
        """One student admitted to one course under one category.

        Fields are made mutually consistent on purpose — a REGULAR student gets an
        Indian nationality and an Indian board, an FN student gets neither and no
        APAAR. The planted-fraud layer breaks these invariants deliberately; if
        they were broken here by accident the validation engine would look like it
        was finding fraud when it was finding generator bugs.
        """
        gender = self.rng.choices(["MALE", "FEMALE", "TRANSGENDER"], weights=[54, 45, 1], k=1)[0]
        name = self.person_name(gender)
        admission = self.admission_date(academic_year)
        dob = self.dob_for(course.level, admission)
        state = next(s for s in STATES if s.name == institution.state)

        nationality = "Indian"
        board = self._indian_board(state)
        passport_no: str | None = None
        oci_card_issue_date: date | None = None
        nri_sponsor_doc_ref: str | None = None
        apaar_id: str | None = self.apaar_id()

        if category == "FN":
            nationality = self.rng.choice(FOREIGN_COUNTRIES)[0]
            board = self.rng.choice(FOREIGN_BOARDS)
            passport_no = self._passport()
            # APAAR requires Aadhaar, which a foreign national will not hold, so
            # an FN student legitimately has none (V2.MISSING exempts them).
            apaar_id = None
        elif category in {"OCI", "PIO"}:
            nationality = self.rng.choice(FOREIGN_COUNTRIES)[0]
            board = self.rng.choice((*FOREIGN_BOARDS, board))
            passport_no = self._passport()
            if category == "OCI":
                oci_card_issue_date = self._oci_date()
        elif category == "CIWGC":
            nationality = "Indian"
            board = self.rng.choice((*FOREIGN_BOARDS, board))
            passport_no = self._passport()
        elif category == "NRI":
            nationality = "Indian"
            board = self.rng.choice((board, "CBSE", *FOREIGN_BOARDS))
            nri_sponsor_doc_ref = f"NRI-SPON-{self.rng.randint(100000, 999999)}"

        return StudentRecord(
            apaar_id=apaar_id,
            name=name,
            dob=dob,
            gender=gender,
            phone=self.phone(),
            email=self.email_for(name),
            guardian_name=self.guardian_name(name),
            address=self.address(institution.district, institution.state),
            nationality=nationality,
            qualifying_board=board,
            passport_no=passport_no,
            institution_aicte_id=institution.aicte_id,
            institution_student_id=self.roll_number(institution.aicte_id, academic_year),
            course_name=course.name,
            course_level=course.level,
            program=course.program,
            academic_year=academic_year,
            admission_date=admission,
            category=category,
            oci_card_issue_date=oci_card_issue_date,
            nri_sponsor_doc_ref=nri_sponsor_doc_ref,
            status=status,
        )

    def _indian_board(self, state: StateRef) -> str:
        return self.rng.choices(
            [state.state_board, "CBSE", "CISCE", "NIOS"], weights=[60, 30, 8, 2], k=1
        )[0]

    def _passport(self) -> str:
        letter = self.rng.choice("ABCDEFGHJKLMNPRSTUVWXYZ")
        return f"{letter}{self.rng.randint(1000000, 9999999)}"

    def _oci_date(self) -> date:
        """OCI card issue date, straddling the configured foreign cutoff.

        Deliberately lands on both sides of 2021-03-04 so V4.OCI_CLASSIFICATION
        has something to classify either way.
        """
        return date(2016, 1, 1) + timedelta(days=self.rng.randint(0, 3650))

    # --- name variants for planted V2.NAME_MISMATCH cases ----------------- #

    #: Transliteration variants that a human would accept as the same name.
    _PASSING_TRANSFORMS: tuple[tuple[str, str], ...] = (
        ("i", "ee"),
        ("u", "oo"),
        ("sh", "s"),
        ("aa", "a"),
        ("ksh", "ksh"),
        ("y", "i"),
    )

    def passing_name_variant(self, name: str, *, min_score: int = 92) -> str:
        """A spelling variant of `name` that must still be accepted.

        Verified against rapidfuzz here rather than hoped for: the point of these
        40 planted records is that the engine does *not* flag them, so a variant
        that accidentally scored 78 would turn a passing test into a false alarm
        about the rule.
        """
        first, _, rest = name.partition(" ")
        candidates: list[str] = []

        for needle, replacement in self._PASSING_TRANSFORMS:
            if needle in first.lower() and needle != replacement:
                index = first.lower().index(needle)
                variant = first[:index] + replacement + first[index + len(needle) :]
                candidates.append(f"{variant.capitalize()} {rest}".strip())

        # Doubling a trailing vowel is the most common Indic transliteration
        # variant and always scores high, so it is the dependable fallback.
        candidates.append(f"{first}{first[-1]} {rest}".strip())
        candidates.append(f"{first} {rest}{rest[-1]}".strip() if rest else f"{first}{first[-1]}")

        best = max(candidates, key=lambda candidate: fuzz.token_sort_ratio(name, candidate))
        score = fuzz.token_sort_ratio(name, best)
        if score < min_score:
            raise AssertionError(
                f"could not build a passing name variant for {name!r}: best was "
                f"{best!r} at {score}, needed >= {min_score}"
            )
        return best

    def failing_name(self, name: str, *, max_score: int = 70) -> str:
        """A different person's name, which must be rejected."""
        for _ in range(64):
            gender = "FEMALE" if name.split()[0] in FIRST_NAMES_FEMALE else "MALE"
            candidate = self.person_name(gender)
            if fuzz.token_sort_ratio(name, candidate) <= max_score:
                return candidate
        raise AssertionError(f"could not build a clearly different name from {name!r}")
