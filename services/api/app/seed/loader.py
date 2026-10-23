"""Loading the generated dataset into PostgreSQL (SPEC 9.2).

Bulk inserts via SQLAlchemy Core rather than the ORM: ~35k students with four
encrypted fields each is enough that per-object ORM overhead is the difference
between seconds and minutes, and none of these rows need identity tracking.

Encryption happens here, on the way in, so nothing unencrypted is ever written —
the generated JSON on disk is synthetic plaintext by design, but the database
holds only ciphertext and lookup hashes.
"""

from __future__ import annotations

import csv
import json
import logging
import uuid
from collections.abc import Iterable, Iterator
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import insert, select, text
from sqlalchemy.orm import Session

from app.models import (
    ApaarStatus,
    Course,
    Enrolment,
    EnrolmentStatus,
    Institution,
    Student,
    derive_seat_type,
)
from app.models.enums import EnrolmentCategory
from app.security.crypto import encrypt_field, hmac_hash, last4

logger = logging.getLogger(__name__)

CHUNK_SIZE = 2000

#: Tables emptied by `--reset`, children before parents.
TRUNCATE_ORDER: tuple[str, ...] = (
    "audit_log",
    "validation_issue",
    "upload_batch",
    "flag",
    "certificate",
    "consent",
    "enrolment_version",
    "document",
    "enrolment",
    "student",
    "api_key",
    "app_user",
    "course",
    "institution",
    "rule_set",
)


def chunked(items: Iterable[dict[str, Any]], size: int = CHUNK_SIZE) -> Iterator[list[dict]]:
    batch: list[dict[str, Any]] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def reset_database(db: Session) -> None:
    """Empty every application table.

    `RESTART IDENTITY` matters for `audit_log`: a fresh seed should start a fresh
    chain from the genesis hash rather than continue a half-truncated one.
    """
    logger.info("truncating application tables")
    db.execute(
        text(
            "TRUNCATE TABLE "
            + ", ".join(TRUNCATE_ORDER)
            + " RESTART IDENTITY CASCADE"
        )
    )
    db.commit()


def database_has_data(db: Session) -> bool:
    return (
        db.execute(select(Institution.id).limit(1)).scalar_one_or_none() is not None
    )


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


# --------------------------------------------------------------------------- #
# Institutions and courses
# --------------------------------------------------------------------------- #


def load_institutions(db: Session, seed_dir: Path, reference_dir: Path) -> dict[str, uuid.UUID]:
    """Insert institutions and return aicte_id -> row id.

    A real list dropped into `/data/reference/institutions.csv` takes precedence
    over the generated one (SPEC 9.1).
    """
    reference_csv = reference_dir / "institutions.csv"
    if reference_csv.exists():
        logger.info("using real institution reference data from %s", reference_csv)
        with reference_csv.open(encoding="utf-8-sig", newline="") as handle:
            records = [dict(row) for row in csv.DictReader(handle)]
    else:
        records = read_json(seed_dir / "institutions.json")

    rows = [
        {
            "id": uuid.uuid4(),
            "aicte_id": record["aicte_id"].strip(),
            "name": record["name"].strip(),
            "state": record["state"].strip(),
            "district": record["district"].strip(),
            "region": record["region"].strip(),
            "type": record["type"].strip(),
            "lat": float(record["lat"]) if record.get("lat") not in (None, "") else None,
            "lng": float(record["lng"]) if record.get("lng") not in (None, "") else None,
        }
        for record in records
    ]

    for batch in chunked(rows):
        db.execute(insert(Institution), batch)
    db.flush()
    logger.info("loaded %d institutions", len(rows))
    return {row["aicte_id"]: row["id"] for row in rows}


def load_courses(
    db: Session, seed_dir: Path, institution_ids: dict[str, uuid.UUID]
) -> dict[tuple[str, str, str, str], uuid.UUID]:
    """Insert courses and return (aicte_id, name, level, year) -> row id."""
    records = read_json(seed_dir / "courses.json")

    rows: list[dict[str, Any]] = []
    keys: list[tuple[str, str, str, str]] = []
    for record in records:
        aicte_id = record["institution_aicte_id"]
        if aicte_id not in institution_ids:
            # Possible when a real institutions.csv replaced the generated list.
            continue
        rows.append(
            {
                "id": uuid.uuid4(),
                "institution_id": institution_ids[aicte_id],
                "level": record["level"],
                "program": record["program"],
                "name": record["name"],
                "approved_intake": int(record["approved_intake"]),
                "academic_year": record["academic_year"],
            }
        )
        keys.append((aicte_id, record["name"], record["level"], record["academic_year"]))

    for batch in chunked(rows):
        db.execute(insert(Course), batch)
    db.flush()
    logger.info("loaded %d course-years", len(rows))
    return {key: row["id"] for key, row in zip(keys, rows, strict=True)}


# --------------------------------------------------------------------------- #
# Students and enrolments
# --------------------------------------------------------------------------- #


def load_students(
    db: Session,
    seed_dir: Path,
    institution_ids: dict[str, uuid.UUID],
    course_ids: dict[tuple[str, str, str, str], uuid.UUID],
) -> dict[str, int]:
    """Insert students and their enrolments with every identifier encrypted."""
    records = read_json(seed_dir / "students.json")

    student_rows: list[dict[str, Any]] = []
    enrolment_rows: list[dict[str, Any]] = []
    skipped = 0

    for record in records:
        aicte_id = record["institution_aicte_id"]
        course_key = (
            aicte_id,
            record["course_name"],
            record["course_level"],
            record["academic_year"],
        )
        if aicte_id not in institution_ids or course_key not in course_ids:
            skipped += 1
            continue

        student_id = uuid.uuid4()
        apaar_id = record.get("apaar_id")
        category = EnrolmentCategory(record["category"])

        student_rows.append(
            {
                "id": student_id,
                "apaar_id_enc": encrypt_field(apaar_id, "apaar"),
                "apaar_id_hash": hmac_hash(apaar_id, "apaar"),
                "apaar_last4": last4(apaar_id),
                "name": record["name"],
                "dob": _parse_date(record["dob"]),
                "gender": record["gender"],
                "phone_enc": encrypt_field(record.get("phone"), "phone"),
                "phone_hash": hmac_hash(record.get("phone"), "phone"),
                "email_enc": encrypt_field(record.get("email"), "email"),
                "email_hash": hmac_hash(record.get("email"), "email"),
                "guardian_name": record.get("guardian_name"),
                "address_hash": hmac_hash(record.get("address"), "address"),
                "nationality": record.get("nationality") or "Indian",
                "qualifying_board": record.get("qualifying_board"),
                "passport_no_enc": encrypt_field(record.get("passport_no"), "passport"),
            }
        )

        enrolment_rows.append(
            {
                "id": uuid.uuid4(),
                "student_id": student_id,
                "institution_id": institution_ids[aicte_id],
                "course_id": course_ids[course_key],
                "academic_year": record["academic_year"],
                "admission_date": _parse_date(record["admission_date"]),
                "institution_student_id": record.get("institution_student_id"),
                "category": category.value,
                "seat_type": derive_seat_type(category).value,
                "oci_card_issue_date": _parse_date(record.get("oci_card_issue_date")),
                "status": EnrolmentStatus(record.get("status", "ACTIVE")).value,
                # Seeded history predates this platform, so nothing is verified
                # until a consent flow runs (SPEC section 8). FN students hold no
                # APAAR at all and are exempt rather than pending.
                "apaar_status": (
                    ApaarStatus.EXEMPT.value
                    if category is EnrolmentCategory.FN
                    else ApaarStatus.PENDING_CONSENT.value
                ),
                "version": 1,
            }
        )

    for batch in chunked(student_rows):
        db.execute(insert(Student), batch)
    db.flush()
    for batch in chunked(enrolment_rows):
        db.execute(insert(Enrolment), batch)
    db.flush()

    if skipped:
        logger.warning("skipped %d students with no matching institution or course", skipped)
    logger.info("loaded %d students and enrolments", len(student_rows))
    return {"students": len(student_rows), "enrolments": len(enrolment_rows), "skipped": skipped}
