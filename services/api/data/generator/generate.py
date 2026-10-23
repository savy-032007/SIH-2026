"""Synthetic dataset generator (SPEC 9.2).

Builds the whole demo universe from one seed: institutions, courses, the seeded
enrolment baseline, the mock registry's truth table, one Excel upload file per
institution, and the planted-fraud manifest that makes detection testable.

    python -m generator.generate --seed 20262026

Outputs land in `/data/seed` (gitignored). Same seed, identical bytes.

Two populations, and the split is the important design decision:

* the **seeded baseline** is what the repository already holds — it carries the
  cases that only exist across records (over-intake, ghost clusters, year-over-year
  outliers), because a single upload row cannot express them;
* the **upload files** are what institutions are about to submit — they carry the
  row-level cases (bad format, duplicates, name mismatches), because those are
  caught while validating a batch.

No real personal data: every APAAR ID starts with 99, every name and address is
invented, and nothing here is ever sent to a government system.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from generator.people import (
    ACADEMIC_YEARS,
    CourseRecord,
    Generator,
    InstitutionRecord,
    StudentRecord,
)
from generator.planting import (
    INDIAN_BOARDS_FOR_PLANTING,
    Manifest,
    make_invalid_apaar,
)

logger = logging.getLogger("generator")

DEFAULT_SEED = 20262026
DEFAULT_OUT = Path("/data/seed")
DEFAULT_RULES = Path("/data/rules/rules_2026_27.json")

CURRENT_YEAR = "2026-27"
PRIOR_YEAR = "2025-26"

#: Rows in each institution's upload file, before planted extras.
UPLOAD_ROWS_PER_INSTITUTION = (12, 34)

#: How full a course typically is, before scaling to the student budget.
BASE_FILL_RANGE = (0.45, 0.98)

#: Planted over-intake and cap-breach magnitudes.
OVER_INTAKE_RATIO = (1.06, 1.18)
OUTLIER_PRIOR_RATIO = 0.40
OUTLIER_CURRENT_RATIO = 1.15

GHOST_LARGE_SIZE = 40
GHOST_LARGE_INSTITUTIONS = 3
GHOST_LARGE_PHONES = 3
GHOST_SMALL_SIZES = (8, 6, 7)


# --------------------------------------------------------------------------- #
# Course fill planning
# --------------------------------------------------------------------------- #


class Plan:
    """Per-course-year admission counts, including the planted breaches."""

    def __init__(self) -> None:
        self.within_intake: dict[tuple, int] = {}
        self.nri: dict[tuple, int] = {}
        self.supernumerary: dict[tuple, int] = {}
        self.ciwgc: dict[tuple, int] = {}


def _load_rules(path: Path) -> dict[str, Any]:
    """Read the active rule set so planted breaches actually breach it.

    Hardcoding "8 NRI students" would silently stop being a breach the moment
    someone edited the cap, so the caps are read from the same JSON the
    validation engine will load.
    """
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _supernumerary_cap(rules: dict[str, Any], course: CourseRecord) -> int:
    pct = rules["supernumerary_pct"][course.level][course.program]
    return int(course.approved_intake * pct)


def _nri_cap(rules: dict[str, Any], course: CourseRecord) -> int:
    return int(course.approved_intake * rules["nri_cap_pct"])


def build_plan(
    gen: Generator,
    courses: list[CourseRecord],
    rules: dict[str, Any],
    *,
    student_budget: int,
    over_intake_institutions: set[str],
    over_intake_course_keys: set[tuple],
    nri_breach_course_keys: set[tuple],
    supernumerary_breach_course_keys: set[tuple],
    outlier_institutions: set[str],
) -> Plan:
    """Decide how many students each course-year admits.

    Normal courses get a random fill, then every normal course is scaled by a
    single factor so the dataset lands on the requested student budget. Planted
    courses are set afterwards and are never scaled, so a breach stays a breach
    whatever the budget.
    """
    plan = Plan()
    raw_fill: dict[tuple, float] = {}

    for course in courses:
        raw_fill[course.key] = gen.rng.uniform(*BASE_FILL_RANGE)

    # Outlier institutions get a deliberate year-over-year jump.
    for course in courses:
        if course.institution_aicte_id not in outlier_institutions:
            continue
        raw_fill[course.key] = (
            OUTLIER_PRIOR_RATIO if course.academic_year == PRIOR_YEAR else OUTLIER_CURRENT_RATIO
        )

    planted_keys = (
        over_intake_course_keys | nri_breach_course_keys | supernumerary_breach_course_keys
    )

    scalable = [course for course in courses if course.key not in planted_keys]
    raw_total = sum(
        course.approved_intake * raw_fill[course.key] for course in scalable
    )
    scale = (student_budget / raw_total) if raw_total else 1.0

    for course in courses:
        intake = course.approved_intake
        is_outlier = course.institution_aicte_id in outlier_institutions

        if course.key in over_intake_course_keys:
            within = int(intake * gen.rng.uniform(*OVER_INTAKE_RATIO)) + 1
        elif is_outlier:
            # Not scaled: the 0.4x -> 1.15x jump is the planted signal itself.
            within = max(1, int(intake * raw_fill[course.key]))
        else:
            within = max(1, int(intake * raw_fill[course.key] * scale))

        nri_cap = _nri_cap(rules, course)
        if course.key in nri_breach_course_keys:
            nri = nri_cap + gen.rng.randint(1, 3)
            within = max(within, nri + 1)
        else:
            nri = gen.rng.randint(0, max(0, min(nri_cap, within // 12)))

        super_cap = _supernumerary_cap(rules, course)
        if course.key in supernumerary_breach_course_keys:
            supernumerary = super_cap + gen.rng.randint(1, 4)
        else:
            supernumerary = gen.rng.randint(0, max(0, min(super_cap, 6)))

        ciwgc_cap = int(super_cap * rules["ciwgc_fraction_of_supernumerary"])
        ciwgc = min(supernumerary, gen.rng.randint(0, max(0, ciwgc_cap)))

        plan.within_intake[course.key] = within
        plan.nri[course.key] = min(nri, within)
        plan.supernumerary[course.key] = supernumerary
        plan.ciwgc[course.key] = ciwgc

    return plan


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #


def generate_seeded_students(
    gen: Generator,
    institutions_by_id: dict[str, InstitutionRecord],
    courses: list[CourseRecord],
    plan: Plan,
) -> list[StudentRecord]:
    """Build the enrolment baseline that `make seed` loads into Postgres."""
    records: list[StudentRecord] = []

    for course in courses:
        institution = institutions_by_id[course.institution_aicte_id]
        within = plan.within_intake[course.key]
        nri = plan.nri[course.key]
        supernumerary = plan.supernumerary[course.key]
        ciwgc = plan.ciwgc[course.key]

        categories: list[str] = ["NRI"] * nri + ["REGULAR"] * max(0, within - nri)
        remaining_super = supernumerary - ciwgc
        categories += ["CIWGC"] * ciwgc
        for _ in range(max(0, remaining_super)):
            categories.append(gen.rng.choices(["FN", "OCI", "PIO"], weights=[6, 3, 1], k=1)[0])

        for category in categories:
            # Prior-year cohorts have largely finished or moved on.
            if course.academic_year == PRIOR_YEAR:
                status = gen.rng.choices(
                    ["ACTIVE", "COMPLETED", "WITHDRAWN"], weights=[80, 15, 5], k=1
                )[0]
            else:
                status = gen.rng.choices(["ACTIVE", "WITHDRAWN"], weights=[97, 3], k=1)[0]

            records.append(
                gen.student(
                    institution=institution,
                    course=course,
                    category=category,
                    academic_year=course.academic_year,
                    status=status,
                )
            )

    return records


def plant_ghost_clusters(
    gen: Generator,
    manifest: Manifest,
    seeded: list[StudentRecord],
    institutions: list[InstitutionRecord],
) -> None:
    """Rewrite contact details so clusters of students share a few contact points.

    This is the signal the Phase 3 ghost-student graph looks for: students who are
    separate records but share a phone, an email or a guardian-and-address across
    institutions, which is what enrolment padding looks like in real data.
    """
    current_active = [
        record
        for record in seeded
        if record.academic_year == CURRENT_YEAR and record.status == "ACTIVE"
    ]
    by_institution: dict[str, list[StudentRecord]] = defaultdict(list)
    for record in current_active:
        by_institution[record.institution_aicte_id].append(record)

    eligible = sorted(
        (aicte_id for aicte_id, rows in by_institution.items() if len(rows) >= GHOST_LARGE_SIZE),
        key=str,
    )
    if len(eligible) < GHOST_LARGE_INSTITUTIONS + 2:
        raise RuntimeError(
            "not enough populated institutions to plant ghost clusters; "
            "increase --students or --institutions"
        )

    # --- the large cluster: 40 students, 3 institutions, 3 phones ---------- #
    chosen = gen.rng.sample(eligible, GHOST_LARGE_INSTITUTIONS)
    phones = [gen.phone() for _ in range(GHOST_LARGE_PHONES)]
    shared_guardian = f"{gen.rng.choice(['Suresh', 'Ramesh', 'Mahadev'])} Enterprises Trustee"
    shared_address = gen.address(
        next(inst.district for inst in institutions if inst.aicte_id == chosen[0]),
        next(inst.state for inst in institutions if inst.aicte_id == chosen[0]),
    )

    per_institution = GHOST_LARGE_SIZE // GHOST_LARGE_INSTITUTIONS
    members: list[StudentRecord] = []
    for index, aicte_id in enumerate(chosen):
        take = per_institution
        if index == len(chosen) - 1:
            take = GHOST_LARGE_SIZE - per_institution * (GHOST_LARGE_INSTITUTIONS - 1)
        members.extend(gen.rng.sample(by_institution[aicte_id], take))

    for position, member in enumerate(members):
        member.phone = phones[position % GHOST_LARGE_PHONES]
        member.guardian_name = shared_guardian
        member.address = shared_address
        member.planted_cases.append("GHOST_CLUSTER_LARGE#001")

    manifest.add(
        kind="GHOST_CLUSTER_LARGE",
        rule_code="GHOST_CLUSTER",
        expected_severity="HIGH",
        scope="national",
        institution_aicte_id=",".join(chosen),
        academic_year=CURRENT_YEAR,
        locator={
            "size": len(members),
            "institutions": chosen,
            "shared_phones": phones,
            "shared_guardian_name": shared_guardian,
            "apaar_ids": [member.apaar_id for member in members if member.apaar_id],
        },
        notes=(
            f"{len(members)} students across {len(chosen)} institutions sharing "
            f"{GHOST_LARGE_PHONES} phone numbers, one guardian name and one address. "
            "Demo script step 5."
        ),
    )

    # --- the smaller clusters --------------------------------------------- #
    remaining = [aicte_id for aicte_id in eligible if aicte_id not in chosen]
    for index, size in enumerate(GHOST_SMALL_SIZES, start=1):
        pair = gen.rng.sample(remaining, 2)
        cluster_phones = [gen.phone() for _ in range(gen.rng.randint(1, 2))]
        cluster_members: list[StudentRecord] = []
        half = size // 2
        for offset, aicte_id in enumerate(pair):
            take = half if offset == 0 else size - half
            pool = [row for row in by_institution[aicte_id] if not row.planted_cases]
            if len(pool) < take:
                raise RuntimeError("not enough unplanted students for a small ghost cluster")
            cluster_members.extend(gen.rng.sample(pool, take))

        shared_email = f"cluster{index}.admissions{index}@gmail.com"
        for position, member in enumerate(cluster_members):
            member.phone = cluster_phones[position % len(cluster_phones)]
            member.email = shared_email
            member.planted_cases.append(f"GHOST_CLUSTER_SMALL#{index:03d}")

        manifest.add(
            kind="GHOST_CLUSTER_SMALL",
            rule_code="GHOST_CLUSTER",
            expected_severity="MEDIUM",
            scope="national",
            institution_aicte_id=",".join(pair),
            academic_year=CURRENT_YEAR,
            locator={
                "size": len(cluster_members),
                "institutions": pair,
                "shared_phones": cluster_phones,
                "shared_email": shared_email,
                "apaar_ids": [m.apaar_id for m in cluster_members if m.apaar_id],
            },
        )


def build_upload_rows(
    gen: Generator,
    manifest: Manifest,
    institutions: list[InstitutionRecord],
    courses: list[CourseRecord],
    seeded: list[StudentRecord],
) -> dict[str, list[StudentRecord]]:
    """Build each institution's pending upload batch, with planted row-level cases.

    Returns rows keyed by institution AICTE id, in file order — the row number in
    the manifest is the Excel row these land on.
    """
    courses_by_institution: dict[str, list[CourseRecord]] = defaultdict(list)
    for course in courses:
        if course.academic_year == CURRENT_YEAR:
            courses_by_institution[course.institution_aicte_id].append(course)

    institutions_by_id = {inst.aicte_id: inst for inst in institutions}
    rows: dict[str, list[StudentRecord]] = {}

    for institution in institutions:
        available = courses_by_institution.get(institution.aicte_id, [])
        if not available:
            rows[institution.aicte_id] = []
            continue
        count = gen.rng.randint(*UPLOAD_ROWS_PER_INSTITUTION)
        rows[institution.aicte_id] = [
            gen.student(
                institution=institution,
                course=gen.rng.choice(available),
                category=gen.rng.choices(
                    ["REGULAR", "NRI", "FN", "OCI", "PIO", "CIWGC"],
                    weights=[86, 5, 4, 2, 1, 2],
                    k=1,
                )[0],
                academic_year=CURRENT_YEAR,
            )
            for _ in range(count)
        ]

    populated = sorted((aicte_id for aicte_id, batch in rows.items() if len(batch) >= 6), key=str)

    def pick_row(exclude_planted: bool = True) -> tuple[str, StudentRecord]:
        """A random upload row, preferring ones not already planted."""
        for _ in range(500):
            aicte_id = gen.rng.choice(populated)
            candidates = [
                row
                for row in rows[aicte_id]
                if not (exclude_planted and row.planted_cases)
            ]
            if candidates:
                return aicte_id, gen.rng.choice(candidates)
        raise RuntimeError("ran out of unplanted upload rows; increase --institutions")

    # --- V2.FORMAT: 20 malformed APAAR IDs -------------------------------- #
    for _ in range(20):
        aicte_id, row = pick_row()
        valid = row.apaar_id or gen.apaar_id()
        broken, how = make_invalid_apaar(gen.rng, valid)
        row.apaar_id = broken
        # Not registered: a malformed id has nothing to look up. Validation
        # should short-circuit after the format error rather than also
        # reporting V2.NOT_FOUND.
        row.in_registry = False
        row.planted_cases.append("V2.FORMAT")
        manifest.add(
            kind="V2.FORMAT",
            rule_code="V2.FORMAT",
            expected_severity="ERROR",
            scope="batch",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={"apaar_id": broken, "institution_student_id": row.institution_student_id},
            notes=f"APAAR {how}; expect V2.FORMAT only, not V2.NOT_FOUND",
        )

    # --- V2.NOT_FOUND: 25 well-formed but unregistered IDs ---------------- #
    for _ in range(25):
        aicte_id, row = pick_row()
        if row.apaar_id is None:
            row.apaar_id = gen.apaar_id()
        row.in_registry = False
        row.planted_cases.append("V2.NOT_FOUND")
        manifest.add(
            kind="V2.NOT_FOUND",
            rule_code="V2.NOT_FOUND",
            expected_severity="ERROR",
            scope="batch",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={"apaar_id": row.apaar_id, "institution_student_id": row.institution_student_id},
            notes="well-formed APAAR deliberately absent from the ABC registry",
        )

    # --- V2.NAME_MISMATCH: 40 variants that MUST pass --------------------- #
    for _ in range(40):
        aicte_id, row = pick_row()
        if row.apaar_id is None:
            row.apaar_id = gen.apaar_id()
        canonical = row.name
        row.registry_name = canonical
        row.name = gen.passing_name_variant(canonical)
        row.planted_cases.append("V2.NAME_MISMATCH_PASS")
        manifest.add(
            kind="V2.NAME_MISMATCH_PASS",
            rule_code="V2.NAME_MISMATCH",
            expected_severity="NONE",
            scope="batch",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={
                "apaar_id": row.apaar_id,
                "submitted_name": row.name,
                "registry_name": canonical,
            },
            notes="transliteration variant; similarity >= 90 so it must NOT be flagged",
        )

    # --- V2.NAME_MISMATCH: 15 different people that MUST fail ------------- #
    for _ in range(15):
        aicte_id, row = pick_row()
        if row.apaar_id is None:
            row.apaar_id = gen.apaar_id()
        canonical = row.name
        row.registry_name = canonical
        row.name = gen.failing_name(canonical)
        row.planted_cases.append("V2.NAME_MISMATCH_FAIL")
        manifest.add(
            kind="V2.NAME_MISMATCH_FAIL",
            rule_code="V2.NAME_MISMATCH",
            expected_severity="ERROR",
            scope="batch",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={
                "apaar_id": row.apaar_id,
                "submitted_name": row.name,
                "registry_name": canonical,
            },
            notes="a different person's name; similarity < 80 so it must be an ERROR",
        )

    # --- V4.FN_INDIAN_BOARD: 12 foreign nationals on an Indian board ------ #
    for _ in range(12):
        aicte_id, row = pick_row()
        row.category = "FN"
        row.apaar_id = None
        row.nationality = "Nigerian"
        row.qualifying_board = gen.rng.choice(INDIAN_BOARDS_FOR_PLANTING)
        row.passport_no = f"{gen.rng.choice('ABCDEFGHJK')}{gen.rng.randint(1000000, 9999999)}"
        row.oci_card_issue_date = None
        row.nri_sponsor_doc_ref = None
        row.in_registry = False
        row.planted_cases.append("V4.FN_INDIAN_BOARD")
        manifest.add(
            kind="V4.FN_INDIAN_BOARD",
            rule_code="V4.FN_INDIAN_BOARD",
            expected_severity="WARNING",
            scope="batch",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={
                "institution_student_id": row.institution_student_id,
                "qualifying_board": row.qualifying_board,
                "nationality": row.nationality,
            },
            notes="SPEC 6.1 V4: WARNING at batch level, HIGH flag nationally",
        )

    # --- V4.NRI_NO_SPONSOR_DOC: 10 NRI rows with no sponsor document ------ #
    for _ in range(10):
        aicte_id, row = pick_row()
        row.category = "NRI"
        row.nationality = "Indian"
        if row.apaar_id is None:
            row.apaar_id = gen.apaar_id()
        row.nri_sponsor_doc_ref = None
        row.oci_card_issue_date = None
        row.planted_cases.append("V4.NRI_NO_SPONSOR_DOC")
        manifest.add(
            kind="V4.NRI_NO_SPONSOR_DOC",
            rule_code="V4.NRI_NO_SPONSOR_DOC",
            expected_severity="ERROR",
            scope="batch",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={"institution_student_id": row.institution_student_id},
        )

    # --- V5.ACTIVE_ELSEWHERE: 18 APAARs already active at another college -- #
    seeded_active_current = [
        record
        for record in seeded
        if record.academic_year == CURRENT_YEAR
        and record.status == "ACTIVE"
        and record.apaar_id
        and not record.planted_cases
    ]
    if len(seeded_active_current) < 18:
        raise RuntimeError("not enough seeded active enrolments to plant V5 duplicates")

    for original in gen.rng.sample(seeded_active_current, 18):
        for _ in range(500):
            aicte_id, row = pick_row()
            if aicte_id != original.institution_aicte_id:
                break
        else:
            raise RuntimeError("could not find a different institution for a V5 duplicate")

        row.apaar_id = original.apaar_id
        row.name = original.name
        row.dob = original.dob
        row.gender = original.gender
        row.category = "REGULAR"
        row.nationality = "Indian"
        row.passport_no = None
        row.oci_card_issue_date = None
        row.nri_sponsor_doc_ref = None
        # The registry already holds this student via the seeded enrolment.
        row.in_registry = False
        row.planted_cases.append("V5.ACTIVE_ELSEWHERE")
        manifest.add(
            kind="V5.ACTIVE_ELSEWHERE",
            rule_code="V5.ACTIVE_ELSEWHERE",
            expected_severity="ERROR",
            scope="batch",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={
                "apaar_id": original.apaar_id,
                "uploading_institution": aicte_id,
                "existing_institution": original.institution_aicte_id,
                "existing_admission_date": original.admission_date.isoformat(),
                "institution_student_id": row.institution_student_id,
            },
            notes=(
                "ACTIVE at the existing institution and submitted by another; "
                "ERROR at batch level, CRITICAL flag nationally. Demo step 4."
            ),
        )

    # --- V1.DUP_IN_BATCH: 15 APAARs repeated inside one file -------------- #
    for _ in range(15):
        aicte_id, row = pick_row()
        if row.apaar_id is None:
            row.apaar_id = gen.apaar_id()
        duplicate = StudentRecord(**{**asdict(row), "planted_cases": ["V1.DUP_IN_BATCH"]})
        duplicate.institution_student_id = gen.roll_number(aicte_id, CURRENT_YEAR)
        duplicate.admission_date = row.admission_date
        row.planted_cases.append("V1.DUP_IN_BATCH")

        batch = rows[aicte_id]
        batch.insert(min(len(batch), batch.index(row) + gen.rng.randint(1, 4)), duplicate)

        manifest.add(
            kind="V1.DUP_IN_BATCH",
            rule_code="V1.DUP_IN_BATCH",
            expected_severity="ERROR",
            scope="batch",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={
                "apaar_id": row.apaar_id,
                "institution_student_ids": [
                    row.institution_student_id,
                    duplicate.institution_student_id,
                ],
            },
            notes="same APAAR twice in one upload file",
        )

    return rows


def plant_national_cases(
    gen: Generator,
    manifest: Manifest,
    institutions: list[InstitutionRecord],
    courses: list[CourseRecord],
    rules: dict[str, Any],
) -> dict[str, Any]:
    """Choose the institutions and courses that will breach caps.

    Chosen before students are generated, because these cases are expressed as
    *how many* students a course admits, not as a mutation afterwards.
    """
    maharashtra = sorted(
        (inst.aicte_id for inst in institutions if inst.state == "Maharashtra"), key=str
    )
    others = sorted(
        (inst.aicte_id for inst in institutions if inst.state != "Maharashtra"), key=str
    )
    if len(maharashtra) < 3 or len(others) < 5:
        raise RuntimeError("too few institutions to plant the national cases")

    current_courses = [course for course in courses if course.academic_year == CURRENT_YEAR]
    by_institution: dict[str, list[CourseRecord]] = defaultdict(list)
    for course in current_courses:
        by_institution[course.institution_aicte_id].append(course)

    # Demo step 3 walks the map to Maharashtra, so two of the four over-intake
    # institutions are there by construction rather than by luck.
    over_intake_ids = gen.rng.sample(maharashtra, 2) + gen.rng.sample(others, 2)
    over_intake_course_keys: set[tuple] = set()
    for aicte_id in over_intake_ids:
        course = gen.rng.choice(by_institution[aicte_id])
        over_intake_course_keys.add(course.key)
        manifest.add(
            kind="V3.WITHIN_INTAKE_EXCEEDED",
            rule_code="V3.WITHIN_INTAKE_EXCEEDED",
            expected_severity="ERROR",
            scope="national",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={
                "course_name": course.name,
                "course_level": course.level,
                "program": course.program,
                "approved_intake": course.approved_intake,
            },
            notes="count(REGULAR + NRI) exceeds approved intake for this course",
        )

    remaining = [course for course in current_courses if course.key not in over_intake_course_keys]

    # NRI breaches need a cap above zero to exceed, which rules out intake 30
    # at a 5% cap (floor(1.5) = 1 is fine, but intake must be >= 60 for a
    # meaningful breach).
    nri_candidates = [course for course in remaining if _nri_cap(rules, course) >= 1]
    nri_courses = gen.rng.sample(nri_candidates, 3)
    nri_course_keys = {course.key for course in nri_courses}
    for course in nri_courses:
        manifest.add(
            kind="V3.NRI_CAP_EXCEEDED",
            rule_code="V3.NRI_CAP_EXCEEDED",
            expected_severity="ERROR",
            scope="national",
            institution_aicte_id=course.institution_aicte_id,
            academic_year=CURRENT_YEAR,
            locator={
                "course_name": course.name,
                "course_level": course.level,
                "program": course.program,
                "approved_intake": course.approved_intake,
                "nri_cap": _nri_cap(rules, course),
            },
            notes=f"NRI admissions exceed {rules['nri_cap_pct']:.0%} of approved intake",
        )

    super_candidates = [
        course
        for course in remaining
        if course.key not in nri_course_keys and _supernumerary_cap(rules, course) >= 2
    ]
    super_courses = gen.rng.sample(super_candidates, 3)
    super_course_keys = {course.key for course in super_courses}
    for course in super_courses:
        manifest.add(
            kind="V3.SUPERNUMERARY_EXCEEDED",
            rule_code="V3.SUPERNUMERARY_EXCEEDED",
            expected_severity="ERROR",
            scope="national",
            institution_aicte_id=course.institution_aicte_id,
            academic_year=CURRENT_YEAR,
            locator={
                "course_name": course.name,
                "course_level": course.level,
                "program": course.program,
                "approved_intake": course.approved_intake,
                "supernumerary_cap": _supernumerary_cap(rules, course),
            },
            notes="FN + OCI + PIO + CIWGC admissions exceed the supernumerary cap",
        )

    # --- outlier institutions --------------------------------------------- #
    used = set(over_intake_ids)
    outlier_pool = [
        aicte_id
        for aicte_id in sorted(by_institution, key=str)
        if aicte_id not in used and len(by_institution[aicte_id]) >= 3
    ]
    outlier_ids = gen.rng.sample(outlier_pool, 2)
    for aicte_id in outlier_ids:
        manifest.add(
            kind="INSTITUTION_OUTLIER",
            rule_code="INSTITUTION_OUTLIER",
            expected_severity="HIGH",
            scope="national",
            institution_aicte_id=aicte_id,
            academic_year=CURRENT_YEAR,
            locator={
                "prior_year": PRIOR_YEAR,
                "prior_fill_ratio": OUTLIER_PRIOR_RATIO,
                "current_fill_ratio": OUTLIER_CURRENT_RATIO,
            },
            notes=(
                f"enrolment/intake jumps {OUTLIER_PRIOR_RATIO}x -> {OUTLIER_CURRENT_RATIO}x "
                "year over year. Being above 1.0, these courses will also trip "
                "V3.WITHIN_INTAKE_EXCEEDED, which is expected, not a duplicate plant."
            ),
        )

    return {
        "over_intake_institutions": set(over_intake_ids),
        "over_intake_course_keys": over_intake_course_keys,
        "nri_breach_course_keys": nri_course_keys,
        "supernumerary_breach_course_keys": super_course_keys,
        "outlier_institutions": set(outlier_ids),
    }


# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #


def _json_default(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"cannot serialise {type(value)!r}")


def write_json(path: Path, payload: Any) -> None:
    """Write deterministic, diffable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, default=_json_default)
        handle.write("\n")


def student_to_dict(record: StudentRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["dob"] = record.dob.isoformat()
    payload["admission_date"] = record.admission_date.isoformat()
    payload["oci_card_issue_date"] = (
        record.oci_card_issue_date.isoformat() if record.oci_card_issue_date else None
    )
    return payload


def build_registry(
    seeded: list[StudentRecord], upload_rows: dict[str, list[StudentRecord]]
) -> list[dict[str, Any]]:
    """The mock registry's truth table: APAAR -> identity.

    Records flagged `in_registry=False` are left out, which is how the planted
    V2.NOT_FOUND cases become "not found". Where an upload row carries a name
    variant, the registry holds the canonical name — so the registry is the thing
    the submitted name is scored against, exactly as a real one would be.
    """
    registry: dict[str, dict[str, Any]] = {}

    for record in [*seeded, *(row for batch in upload_rows.values() for row in batch)]:
        if not record.apaar_id or not record.in_registry:
            continue
        registry.setdefault(
            record.apaar_id,
            {
                "apaar_id": record.apaar_id,
                "name": record.registry_truth_name,
                "dob": record.dob.isoformat(),
                "gender": record.gender,
                "active": True,
            },
        )

    return [registry[key] for key in sorted(registry)]


def write_upload_workbooks(
    out_dir: Path,
    institutions: list[InstitutionRecord],
    upload_rows: dict[str, list[StudentRecord]],
    manifest: Manifest,
) -> dict[str, str]:
    """Write one .xlsx per institution and resolve manifest row numbers.

    Row numbers can only be known once rows are in file order, so the manifest's
    batch locators are completed here rather than guessed earlier.
    """
    from app.uploads.template import FIRST_DATA_ROW
    from app.uploads.workbook import build_workbook

    uploads_dir = out_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # case_id -> (file, row_number), filled in as rows are laid out.
    located: dict[tuple[str, str], list[int]] = defaultdict(list)
    filenames: dict[str, str] = {}

    for institution in institutions:
        batch = upload_rows.get(institution.aicte_id, [])
        if not batch:
            continue

        filename = f"{institution.aicte_id}__{CURRENT_YEAR}.xlsx"
        filenames[institution.aicte_id] = filename

        sheet_rows: list[dict[str, Any]] = []
        for offset, record in enumerate(batch):
            sheet_rows.append(
                {
                    "apaar_id": record.apaar_id or "",
                    "institution_student_id": record.institution_student_id,
                    "name": record.name,
                    "dob": record.dob.isoformat(),
                    "gender": record.gender,
                    "phone": record.phone,
                    "email": record.email,
                    "guardian_name": record.guardian_name,
                    "address": record.address,
                    "nationality": record.nationality,
                    "qualifying_board": record.qualifying_board,
                    "passport_no": record.passport_no or "",
                    "course_name": record.course_name,
                    "course_level": record.course_level,
                    "program": record.program,
                    "academic_year": record.academic_year,
                    "admission_date": record.admission_date.isoformat(),
                    "category": record.category,
                    "oci_card_issue_date": (
                        record.oci_card_issue_date.isoformat()
                        if record.oci_card_issue_date
                        else ""
                    ),
                    "nri_sponsor_doc_ref": record.nri_sponsor_doc_ref or "",
                }
            )
            row_number = FIRST_DATA_ROW + offset
            for case_kind in record.planted_cases:
                located[(institution.aicte_id, case_kind)].append(row_number)

        workbook = build_workbook(sheet_rows)
        workbook.save(uploads_dir / filename)

    # Complete the batch-scope locators now that row numbers exist.
    consumed: dict[tuple[str, str], int] = defaultdict(int)
    for case in manifest.cases:
        if case.scope != "batch":
            continue
        kind = case.case_id.split("#")[0]
        key = (case.institution_aicte_id, kind)
        hits = located.get(key, [])
        index = consumed[key]
        consumed[key] = index + 1
        case.locator["file"] = f"uploads/{filenames.get(case.institution_aicte_id, '')}"
        case.locator["row_numbers"] = hits
        if index < len(hits):
            case.locator["row_number"] = hits[index]

    return filenames


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def generate(
    *,
    seed: int,
    out_dir: Path,
    institution_count: int,
    student_budget: int,
    rules_path: Path,
) -> dict[str, Any]:
    """Generate the whole dataset and return a summary."""
    gen = Generator(seed)
    manifest = Manifest()
    rules = _load_rules(rules_path)

    logger.info("generating %d institutions", institution_count)
    institutions = gen.institutions(institution_count)
    institutions_by_id = {inst.aicte_id: inst for inst in institutions}

    courses: list[CourseRecord] = []
    for institution in institutions:
        courses.extend(gen.courses_for(institution))
    logger.info("generated %d course-years", len(courses))

    targets = plant_national_cases(gen, manifest, institutions, courses, rules)

    plan = build_plan(
        gen,
        courses,
        rules,
        student_budget=student_budget,
        **targets,
    )

    seeded = generate_seeded_students(gen, institutions_by_id, courses, plan)
    logger.info("generated %d seeded enrolments", len(seeded))

    plant_ghost_clusters(gen, manifest, seeded, institutions)

    upload_rows = build_upload_rows(gen, manifest, institutions, courses, seeded)
    upload_row_count = sum(len(batch) for batch in upload_rows.values())
    logger.info("generated %d upload rows", upload_row_count)

    manifest.verify()

    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "institutions.json", [asdict(inst) for inst in institutions])
    write_json(out_dir / "courses.json", [asdict(course) for course in courses])
    write_json(out_dir / "students.json", [student_to_dict(record) for record in seeded])
    write_json(
        out_dir / "upload_rows.json",
        {
            aicte_id: [student_to_dict(row) for row in batch]
            for aicte_id, batch in sorted(upload_rows.items())
        },
    )
    write_json(
        out_dir / "abc_registry.json",
        {
            "synthetic": True,
            "note": "Mock APAAR/ABC registry truth table. No real student data.",
            "records": build_registry(seeded, upload_rows),
        },
    )

    filenames = write_upload_workbooks(out_dir, institutions, upload_rows, manifest)

    summary = {
        "seed": seed,
        "institutions": len(institutions),
        "course_years": len(courses),
        "seeded_enrolments": len(seeded),
        "upload_rows": upload_row_count,
        "upload_files": len(filenames),
        "registry_records": len(build_registry(seeded, upload_rows)),
        "students_total": len(seeded) + upload_row_count,
    }

    write_json(out_dir / "planted.json", manifest.as_dict(seed=seed, extra={"summary": summary}))

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generator.generate",
        description="Generate the synthetic APAAR dataset (SPEC 9.2).",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="deterministic seed")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument("--institutions", type=int, default=100)
    parser.add_argument(
        "--students",
        type=int,
        default=35000,
        help="approximate number of seeded enrolments to aim for",
    )
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(message)s",
    )

    summary = generate(
        seed=args.seed,
        out_dir=args.out,
        institution_count=args.institutions,
        student_budget=args.students,
        rules_path=args.rules,
    )

    print("\nsynthetic dataset written to", args.out)
    for key, value in summary.items():
        print(f"  {key:20s} {value}")
    print("\nplanted ground truth:", args.out / "planted.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
