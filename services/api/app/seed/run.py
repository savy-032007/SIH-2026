"""`make seed` — build and load the whole demo dataset (SPEC section 12, Phase 1).

    python -m app.seed.run --reset

Steps, in order: migrate, generate the synthetic dataset, load the rule sets, load
institutions/courses/students, create the demo users, print the credentials.

Safe by default: without `--reset` it refuses to run over a database that already
has data, so nobody loses a half-finished demo state by muscle memory.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal, engine
from app.models import Institution, Role, User
from app.rules import load_all_from_disk
from app.security import audit, mfa, passwords
from app.seed.demo_users import DEMO_USERS, DemoUser
from app.seed.loader import (
    database_has_data,
    load_courses,
    load_institutions,
    load_students,
    read_json,
    reset_database,
)

logger = logging.getLogger("seed")

ACTIVE_YEAR = "2026-27"


def run_migrations() -> None:
    """Apply Alembic migrations in-process-adjacent via the CLI.

    The CLI is used rather than the Python API so the output a developer sees here
    is identical to `make migrate`.
    """
    logger.info("applying database migrations")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit("alembic upgrade failed")
    logger.info("migrations applied")


def run_generator(seed: int, out_dir: Path, institutions: int, students: int) -> dict[str, Any]:
    """Generate the synthetic dataset."""
    from generator.generate import DEFAULT_RULES, generate

    logger.info("generating synthetic dataset (seed=%d)", seed)
    return generate(
        seed=seed,
        out_dir=out_dir,
        institution_count=institutions,
        student_budget=students,
        rules_path=DEFAULT_RULES,
    )


def pick_demo_institution(seed_dir: Path, institution_ids: dict[str, uuid.UUID]) -> str:
    """Choose the Maharashtra institution the demo institution users belong to.

    Preference order: a Maharashtra institution that also carries a planted
    over-intake case (so demo steps 1-3 follow one college from upload through to
    the national map), then any Maharashtra institution, then anything at all.
    """
    institutions = {
        record["aicte_id"]: record for record in read_json(seed_dir / "institutions.json")
    }

    planted_path = seed_dir / "planted.json"
    if planted_path.exists():
        manifest = read_json(planted_path)
        for case in manifest.get("cases", []):
            if case.get("rule_code") != "V3.WITHIN_INTAKE_EXCEEDED":
                continue
            aicte_id = case.get("institution_aicte_id", "")
            record = institutions.get(aicte_id)
            if record and record["state"] == "Maharashtra" and aicte_id in institution_ids:
                return aicte_id

    for aicte_id, record in institutions.items():
        if record["state"] == "Maharashtra" and aicte_id in institution_ids:
            return aicte_id

    return next(iter(institution_ids))


def create_demo_users(
    db, demo_institution_id: uuid.UUID, demo_institution_name: str
) -> list[dict[str, Any]]:
    """Create one user per role and return their printable credentials."""
    settings = get_settings()
    created: list[dict[str, Any]] = []

    for definition in DEMO_USERS:
        existing = db.execute(
            select(User).where(User.email == definition.email)
        ).scalar_one_or_none()
        if existing is not None:
            logger.info("user %s already exists, skipping", definition.email)
            continue

        secret: str | None = None
        secret_enc = None
        if definition.mfa_required:
            secret = mfa.generate_secret()
            secret_enc = mfa.encrypt_secret(secret)

        user = User(
            email=definition.email,
            password_hash=passwords.hash_password(settings.demo_user_password),
            role=definition.role,
            institution_id=demo_institution_id if definition.attach_to_demo_institution else None,
            region=definition.region,
            totp_secret_enc=secret_enc,
            mfa_enabled=definition.mfa_required,
            is_active=True,
        )
        db.add(user)
        db.flush()

        audit.append(
            db,
            action="USER_CREATED",
            entity="app_user",
            entity_id=str(user.id),
            after={"email": user.email, "role": user.role.value, "mfa": user.mfa_enabled},
        )

        created.append(
            {
                "email": definition.email,
                "role": definition.role.value,
                "purpose": definition.purpose,
                "scope": _describe_scope(definition, demo_institution_name),
                "mfa": definition.mfa_required,
                "totp_secret": secret,
                "otpauth_uri": mfa.provisioning_uri(secret, definition.email) if secret else None,
                "current_code": mfa.current_code(secret) if secret else None,
            }
        )

    return created


def _describe_scope(definition: DemoUser, institution_name: str) -> str:
    if definition.attach_to_demo_institution:
        return institution_name
    if definition.region:
        return f"{definition.region.value} region"
    if definition.role is Role.AICTE_ANALYST:
        return "national, PII masked"
    return "national"


def print_report(
    summary: dict[str, Any],
    counts: dict[str, int],
    credentials: list[dict[str, Any]],
    demo_institution: tuple[str, str],
    seed_dir: Path,
) -> None:
    settings = get_settings()
    line = "=" * 78

    print()
    print(line)
    print("  APAAR platform — seed complete")
    print(line)

    print("\n  dataset")
    for key, value in summary.items():
        print(f"    {key:22s} {value}")
    print(f"    {'students loaded':22s} {counts.get('students', 0)}")
    print(f"    {'enrolments loaded':22s} {counts.get('enrolments', 0)}")

    print(f"\n  demo institution (Maharashtra)\n    {demo_institution[0]}  {demo_institution[1]}")

    print(f"\n  demo users — password for all: {settings.demo_user_password}")
    print(f"  {'-' * 74}")
    for entry in credentials:
        print(f"    {entry['email']}")
        print(f"      role   {entry['role']}   scope: {entry['scope']}")
        print(f"      for    {entry['purpose']}")
        if entry["mfa"]:
            print(f"      TOTP   {entry['totp_secret']}   (code right now: {entry['current_code']})")
            print(f"      otpauth {entry['otpauth_uri']}")
        else:
            print("      TOTP   not required for this role")
        print()

    if not credentials:
        print("    (demo users already existed — rerun with --reset to recreate)\n")

    print("  planted fraud ground truth")
    print(f"    {seed_dir / 'planted.json'}")
    print(f"    upload files: {seed_dir / 'uploads'}")

    print("\n  next")
    print("    api docs   http://localhost:8000/docs")
    print("    log in     POST /api/v1/auth/login  then  POST /api/v1/auth/mfa/verify")
    print("    audit      GET  /api/v1/audit/verify")
    print()
    print("  All data is synthetic. Every APAAR ID begins with 99.")
    print(line)
    print()


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        prog="app.seed.run",
        description="Generate and load the synthetic APAAR dataset and demo users.",
    )
    parser.add_argument(
        "--reset", action="store_true", help="truncate all application tables first"
    )
    parser.add_argument("--seed", type=int, default=settings.seed)
    parser.add_argument("--institutions", type=int, default=settings.gen_institutions)
    parser.add_argument("--students", type=int, default=settings.gen_students)
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="reuse the dataset already in /data/seed",
    )
    parser.add_argument(
        "--skip-migrate", action="store_true", help="assume migrations are already applied"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")

    seed_dir = Path(settings.seed_dir)
    reference_dir = Path(settings.reference_dir)

    if not args.skip_migrate:
        run_migrations()

    with SessionLocal() as db:
        if args.reset:
            reset_database(db)
        elif database_has_data(db):
            raise SystemExit(
                "database already contains data. Re-run with --reset to replace it "
                "(this deletes all existing rows)."
            )

    if args.skip_generate:
        if not (seed_dir / "students.json").exists():
            raise SystemExit(f"--skip-generate given but no dataset found in {seed_dir}")
        summary = read_json(seed_dir / "planted.json").get("summary", {})
        logger.info("reusing existing dataset in %s", seed_dir)
    else:
        summary = run_generator(args.seed, seed_dir, args.institutions, args.students)
        try:
            import httpx
            httpx.post(f"{settings.abc_base_url}/admin/reload", timeout=2.0)
        except Exception:
            pass

    with SessionLocal() as db:
        logger.info("loading rule sets")
        load_all_from_disk(db, activate_year=ACTIVE_YEAR)

        institution_ids = load_institutions(db, seed_dir, reference_dir)
        course_ids = load_courses(db, seed_dir, institution_ids)
        counts = load_students(db, seed_dir, institution_ids, course_ids)

        demo_aicte_id = pick_demo_institution(seed_dir, institution_ids)
        demo_institution = db.get(Institution, institution_ids[demo_aicte_id])
        assert demo_institution is not None

        credentials = create_demo_users(db, demo_institution.id, demo_institution.name)

        audit.append(
            db,
            action="DATASET_SEEDED",
            entity="dataset",
            entity_id=str(args.seed),
            after={"summary": summary, "counts": counts},
        )
        db.commit()

        print_report(
            summary,
            counts,
            credentials,
            (demo_institution.aicte_id, demo_institution.name),
            seed_dir,
        )

    engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
