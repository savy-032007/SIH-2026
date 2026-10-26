"""Demo user definitions (SPEC section 13).

Development only. Every account shares one password from `DEMO_USER_PASSWORD` and
its TOTP secret is printed by `make seed`, which is acceptable precisely because
none of this data is real. A production deployment seeds no users at all — the
first super admin is created out of band.

`example.com` addresses are RFC 2606 reserved, so nothing here can collide with a
real mailbox.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import MFA_REQUIRED_ROLES, Region, Role


@dataclass(frozen=True)
class DemoUser:
    email: str
    role: Role
    #: Which demo step this account is for, printed next to the credentials.
    purpose: str
    region: Region | None = None
    #: True when the account belongs to the demo Maharashtra institution.
    attach_to_demo_institution: bool = False

    @property
    def mfa_required(self) -> bool:
        return self.role in MFA_REQUIRED_ROLES


#: One per role (SPEC section 13), with the institution pair on a Maharashtra
#: institution that also carries a planted over-intake case, so demo steps 1-3
#: follow the same college from upload to national map.
DEMO_USERS: tuple[DemoUser, ...] = (
    DemoUser(
        email="admin@aicte.gov.in",
        role=Role.AICTE_SUPER_ADMIN,
        purpose="AICTE Admin login",
    ),
    DemoUser(
        email="verifier@tcs.com",
        role=Role.VERIFIER,
        purpose="Verifier / Employer login",
    ),
    DemoUser(
        email="super.admin@aicte.example.com",
        role=Role.AICTE_SUPER_ADMIN,
        purpose="national dashboard, rules, users (demo steps 3-8)",
    ),
    DemoUser(
        email="regional.officer@aicte.example.com",
        role=Role.AICTE_REGIONAL_OFFICER,
        region=Region.WESTERN,
        purpose="Western region only - proves row-level scoping",
    ),
    DemoUser(
        email="analyst@aicte.example.com",
        role=Role.AICTE_ANALYST,
        purpose="read-only with PII masked",
    ),
    DemoUser(
        email="inst.admin@college.example.com",
        role=Role.INST_ADMIN,
        purpose="approves and submits batches (demo step 2)",
        attach_to_demo_institution=True,
    ),
    DemoUser(
        email="admin@xyzcollege.ac.in",
        role=Role.INST_ADMIN,
        purpose="UI Demo Institution Admin (Screen 0 Login)",
        attach_to_demo_institution=True,
    ),
    DemoUser(
        email="inst.operator@college.example.com",
        role=Role.INST_OPERATOR,
        purpose="uploads and edits, cannot submit (demo step 1)",
        attach_to_demo_institution=True,
    ),
)
