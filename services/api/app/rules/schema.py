"""Typed, validated shape of a rule set (SPEC section 7).

Everything the validation engine needs to decide a cap lives here. Nothing in
`app/validation` may hardcode a threshold: a rule the handbook can change must be
editable in the Rules Manager and auditable, not recompiled.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import CourseLevel, Program


class NameMatchThresholds(BaseModel):
    """Fuzzy name-match bands for V2.NAME_MISMATCH.

    A score at or above `warn_below` passes; between the two it warns; below
    `error_below` it errors.
    """

    model_config = ConfigDict(extra="forbid")

    warn_below: int = Field(default=90, ge=0, le=100)
    error_below: int = Field(default=80, ge=0, le=100)

    @model_validator(mode="after")
    def _ordered(self) -> NameMatchThresholds:
        if self.error_below > self.warn_below:
            raise ValueError(
                f"error_below ({self.error_below}) must not exceed "
                f"warn_below ({self.warn_below})"
            )
        return self


class RiskWeights(BaseModel):
    """Weights for the institution risk score (SPEC 6.2)."""

    model_config = ConfigDict(extra="forbid")

    CRITICAL: float = Field(default=25, ge=0)
    HIGH: float = Field(default=10, ge=0)
    MEDIUM: float = Field(default=4, ge=0)
    LOW: float = Field(default=1, ge=0)
    over_intake_year: float = Field(default=8, ge=0)
    unverified_pct: float = Field(default=0.3, ge=0)
    iforest: float = Field(default=0.3, ge=0)


class RuleSetConfig(BaseModel):
    """One academic year's validation configuration."""

    model_config = ConfigDict(extra="forbid")

    academic_year: str = Field(pattern=r"^\d{4}-\d{2}$")

    #: Share of approved intake reservable for NRI admissions (V3.NRI_CAP_EXCEEDED).
    nri_cap_pct: float = Field(default=0.05, ge=0, le=1)

    #: Supernumerary cap as a share of approved intake, by level then program.
    #: TODO(verify): the 2026-27 Approval Process Handbook slabs (15% UG/diploma
    #: engineering, 25% PG engineering and management/design/other-technical) and
    #: its statement that supernumerary seats are exclusively for international
    #: students are not confirmed against the published handbook. Configurable on
    #: purpose — see data/rules/README.md.
    supernumerary_pct: dict[CourseLevel, dict[Program, float]]

    #: Share of the supernumerary pool reserved for CIWGC (V3.CIWGC_SPLIT).
    #: TODO(verify): whether the one-third sub-pool split survived the 2026-27
    #: rewrite is unknown. Never hardcode this.
    ciwgc_fraction_of_supernumerary: float = Field(default=0.3333, ge=0, le=1)

    #: Whether unfilled CIWGC seats transfer to the wider supernumerary pool.
    #: TODO(verify): unconfirmed.
    ciwgc_vacancy_transfer: bool = True

    #: OCI card issue date on or after which a student counts as foreign for seat
    #: classification (V4.OCI_CLASSIFICATION).
    #: TODO(verify): unconfirmed cutoff.
    oci_foreign_cutoff_date: date = date(2021, 3, 4)

    #: Fraction of any cap at which V3.NEAR_CAP warns.
    near_cap_threshold: float = Field(default=0.95, gt=0, le=1)

    #: Plausible age at admission (V4.AGE_IMPLAUSIBLE).
    age_min: int = Field(default=15, ge=0, le=120)
    age_max: int = Field(default=60, ge=0, le=120)

    name_match: NameMatchThresholds = Field(default_factory=NameMatchThresholds)
    risk_weights: RiskWeights = Field(default_factory=RiskWeights)

    @model_validator(mode="after")
    def _age_range_ordered(self) -> RuleSetConfig:
        if self.age_min >= self.age_max:
            raise ValueError(f"age_min ({self.age_min}) must be below age_max ({self.age_max})")
        return self

    @model_validator(mode="after")
    def _supernumerary_is_complete(self) -> RuleSetConfig:
        """Every level/program combination must have a cap.

        A missing entry would otherwise mean "no cap" at validation time, i.e. a
        silently unlimited pool. Failing loudly here is the whole point.
        """
        missing: list[str] = []
        for level in CourseLevel:
            programs = self.supernumerary_pct.get(level)
            if programs is None:
                missing.append(f"{level}.*")
                continue
            missing.extend(
                f"{level}.{program}" for program in Program if program not in programs
            )
        if missing:
            raise ValueError("supernumerary_pct is missing entries: " + ", ".join(missing))

        for level, programs in self.supernumerary_pct.items():
            for program, pct in programs.items():
                if not 0 <= pct <= 1:
                    raise ValueError(
                        f"supernumerary_pct[{level}][{program}] must be between 0 and 1, got {pct}"
                    )
        return self

    # --- helpers used by the validation engine ---------------------------- #

    def supernumerary_cap(self, level: CourseLevel, program: Program, approved_intake: int) -> int:
        """Seat count cap for the supernumerary pool (V3.SUPERNUMERARY_EXCEEDED)."""
        pct = self.supernumerary_pct[level][program]
        return int(approved_intake * pct)

    def nri_cap(self, approved_intake: int) -> int:
        """Seat count cap for NRI admissions (V3.NRI_CAP_EXCEEDED)."""
        return int(approved_intake * self.nri_cap_pct)

    def ciwgc_cap(self, level: CourseLevel, program: Program, approved_intake: int) -> int:
        """Seat count cap for the CIWGC sub-pool (V3.CIWGC_SPLIT)."""
        return int(
            self.supernumerary_cap(level, program, approved_intake)
            * self.ciwgc_fraction_of_supernumerary
        )
