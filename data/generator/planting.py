"""Planted fraud and its ground-truth manifest (SPEC 9.2).

The dataset deliberately contains known-bad records in known places, recorded in
`/data/seed/planted.json`. That manifest is what makes detection testable instead
of impressionistic: `tests/test_planted.py` (Phase 2) asserts every case is caught
with the right rule code and severity — and, just as importantly, that the 40
spelling variants which *should* pass are not flagged.

Two scopes, because they are detected by different machinery:

* ``batch``    — a row inside an institution's upload file. Caught when that file
  is validated (SPEC 6.1), so the locator points at a file and a row number.
* ``national`` — only visible across the whole repository, so it is seeded
  straight into Postgres and caught by the national run (SPEC 6.2).

A `V5` case needs both: a seeded ACTIVE enrolment at one institution and an upload
row at another. It is filed as ``batch``, since that is where it first surfaces.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Scope = Literal["batch", "national"]

#: Expected counts, straight from the SPEC 9.2 table. The generator asserts it
#: produced exactly these, so a refactor cannot quietly stop planting something.
EXPECTED_COUNTS: dict[str, int] = {
    "V1.DUP_IN_BATCH": 15,
    "V2.FORMAT": 20,
    "V2.NOT_FOUND": 25,
    "V2.NAME_MISMATCH_PASS": 40,
    "V2.NAME_MISMATCH_FAIL": 15,
    "V3.WITHIN_INTAKE_EXCEEDED": 4,
    "V3.NRI_CAP_EXCEEDED": 3,
    "V3.SUPERNUMERARY_EXCEEDED": 3,
    "V4.FN_INDIAN_BOARD": 12,
    "V4.NRI_NO_SPONSOR_DOC": 10,
    "V5.ACTIVE_ELSEWHERE": 18,
    "GHOST_CLUSTER_LARGE": 1,
    "GHOST_CLUSTER_SMALL": 3,
    "INSTITUTION_OUTLIER": 2,
}


@dataclass
class PlantedCase:
    """One known-bad thing, and where to find it."""

    case_id: str
    #: Rule or flag type expected to fire. `V2.NAME_MISMATCH_PASS` is the
    #: exception: it names the rule that must *not* fire.
    rule_code: str
    #: ERROR, WARNING, INFO, a flag severity, or NONE for must-not-fire cases.
    expected_severity: str
    scope: Scope
    institution_aicte_id: str
    academic_year: str
    #: How to find it: {"file", "row_number"} for batch scope,
    #: {"apaar_id", "course_name", ...} for national scope.
    locator: dict[str, Any] = field(default_factory=dict)
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class Manifest:
    """Accumulates planted cases and verifies the totals before writing."""

    def __init__(self) -> None:
        self._cases: list[PlantedCase] = []
        self._counters: dict[str, int] = {}

    def add(
        self,
        *,
        kind: str,
        rule_code: str,
        expected_severity: str,
        scope: Scope,
        institution_aicte_id: str,
        academic_year: str,
        locator: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> PlantedCase:
        """Record one case. `kind` is the EXPECTED_COUNTS key."""
        self._counters[kind] = self._counters.get(kind, 0) + 1
        case = PlantedCase(
            case_id=f"{kind}#{self._counters[kind]:03d}",
            rule_code=rule_code,
            expected_severity=expected_severity,
            scope=scope,
            institution_aicte_id=institution_aicte_id,
            academic_year=academic_year,
            locator=locator or {},
            notes=notes,
        )
        self._cases.append(case)
        return case

    @property
    def cases(self) -> list[PlantedCase]:
        return list(self._cases)

    def totals(self) -> dict[str, int]:
        return dict(sorted(self._counters.items()))

    def verify(self) -> None:
        """Fail loudly if the planted counts drift from SPEC 9.2.

        A silently under-planted dataset would make Phase 2 and 3 look like they
        were passing when they were simply not being asked the question.
        """
        actual = self.totals()
        problems: list[str] = []

        for kind, expected in EXPECTED_COUNTS.items():
            got = actual.get(kind, 0)
            if got != expected:
                problems.append(f"{kind}: expected {expected}, planted {got}")

        for kind in actual:
            if kind not in EXPECTED_COUNTS:
                problems.append(f"{kind}: planted {actual[kind]} but not in SPEC 9.2")

        if problems:
            raise AssertionError("planted-case counts do not match SPEC 9.2:\n  " + "\n  ".join(problems))

    def as_dict(self, *, seed: int, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "seed": seed,
            "spec_reference": "SPEC 9.2",
            "synthetic": True,
            "note": (
                "Ground truth for the planted fraud in this dataset. All records "
                "are synthetic; every APAAR ID begins with 99."
            ),
            "expected_counts": EXPECTED_COUNTS,
            "totals": self.totals(),
            "cases": [case.as_dict() for case in self._cases],
            **(extra or {}),
        }


# --------------------------------------------------------------------------- #
# Row-level mutations applied to upload rows
# --------------------------------------------------------------------------- #


def make_invalid_apaar(rng, valid_apaar: str) -> tuple[str, str]:
    """Break an APAAR ID's format and say how.

    Length and non-digit characters only. No checksum is invented: SPEC 6.1
    V2.FORMAT says no official checksum spec is known, and a made-up one would
    reject genuine IDs once real data arrives.
    """
    style = rng.choice(["too_short", "too_long", "letters", "spaced", "punctuated"])
    match style:
        case "too_short":
            return valid_apaar[:10], "only 10 digits"
        case "too_long":
            return valid_apaar + str(rng.randint(0, 9)), "13 digits"
        case "letters":
            return valid_apaar[:8] + "ABCD", "contains letters"
        case "spaced":
            return f"{valid_apaar[:4]} {valid_apaar[4:8]} {valid_apaar[8:]}", "contains spaces"
        case _:
            return f"{valid_apaar[:4]}-{valid_apaar[4:8]}-{valid_apaar[8:]}", "contains hyphens"


#: Indian boards an FN student should never present (V4.FN_INDIAN_BOARD).
INDIAN_BOARDS_FOR_PLANTING: tuple[str, ...] = (
    "CBSE",
    "CISCE",
    "MSBSHSE",
    "KSEEB",
    "TNBSE",
    "UPMSP",
)
