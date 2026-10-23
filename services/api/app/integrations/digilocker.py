"""DigiLocker adapters for consented APAAR/ABC ID card retrieval (SPEC 9.4).

DigiLocker is the second, stronger consent channel: instead of an OTP the student
authorises the platform in DigiLocker, which then issues the APAAR/ABC ID card as
a verified document. The mock simulates that OAuth-consent-then-pull shape so the
Phase 2 consent flow can be built against the real sequence of steps.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from app.config import Settings

logger = logging.getLogger(__name__)


class DigiLockerError(Exception):
    """DigiLocker could not be reached, or refused the request."""


@dataclass(frozen=True)
class ConsentRequest:
    """A pending authorisation the student must complete."""

    request_id: str
    #: Where the student is sent to authorise. In the mock this is a local route.
    authorization_url: str
    expires_at: datetime


@dataclass(frozen=True)
class IssuedDocument:
    """A document DigiLocker released after the student authorised it."""

    doc_type: str
    issuer: str
    #: Parsed fields — for an APAAR/ABC card: apaar_id, name, dob, gender.
    fields: dict[str, Any] = field(default_factory=dict)
    #: Hash of the raw document bytes, for the `document.sha256` audit trail.
    sha256: str | None = None


class DigiLockerProvider(ABC):
    """Interface every DigiLocker implementation satisfies."""

    @abstractmethod
    def start_consent(self, *, student_reference: str, purpose: str) -> ConsentRequest:
        """Begin authorisation and return where to send the student."""

    @abstractmethod
    def fetch_document(self, *, request_id: str, doc_type: str) -> IssuedDocument:
        """Pull an issued document after the student authorised it.

        Must raise `DigiLockerError` if consent was never granted — a provider
        that returns data without it would defeat the consent gate entirely.
        """


class MockDigiLocker(DigiLockerProvider):
    """In-process simulation of the DigiLocker consent flow.

    State lives in a process dictionary, so it resets on restart. That is fine for
    development and keeps a table out of the schema that SPEC section 5 does not
    define — the authoritative consent record is the `consent` row the platform
    writes, not this.
    """

    #: request_id -> {student_reference, purpose, expires_at, granted}
    _pending: dict[str, dict[str, Any]] = {}

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def start_consent(self, *, student_reference: str, purpose: str) -> ConsentRequest:
        request_id = secrets.token_urlsafe(24)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        self._pending[request_id] = {
            "student_reference": student_reference,
            "purpose": purpose,
            "expires_at": expires_at,
            "granted": False,
        }
        logger.info("mock digilocker consent started for purpose=%s", purpose)
        return ConsentRequest(
            request_id=request_id,
            authorization_url=f"{self._settings.web_origin}/consent/{request_id}",
            expires_at=expires_at,
        )

    def grant(self, request_id: str, document_fields: dict[str, Any]) -> None:
        """Simulate the student approving in DigiLocker.

        Called by the mock consent route in Phase 2; no production counterpart.
        """
        pending = self._pending.get(request_id)
        if pending is None:
            raise DigiLockerError("unknown consent request")
        if datetime.now(UTC) > pending["expires_at"]:
            raise DigiLockerError("consent request has expired")
        pending["granted"] = True
        pending["fields"] = document_fields

    def fetch_document(self, *, request_id: str, doc_type: str) -> IssuedDocument:
        pending = self._pending.get(request_id)
        if pending is None:
            raise DigiLockerError("unknown consent request")
        if not pending.get("granted"):
            raise DigiLockerError("student has not granted consent for this request")
        if datetime.now(UTC) > pending["expires_at"]:
            raise DigiLockerError("consent request has expired")

        fields = pending.get("fields", {})
        canonical = repr(sorted(fields.items())).encode("utf-8")
        return IssuedDocument(
            doc_type=doc_type,
            issuer="MOCK-DIGILOCKER",
            fields=fields,
            sha256=hashlib.sha256(canonical).hexdigest(),
        )

    @classmethod
    def reset(cls) -> None:
        """Clear pending requests — used by tests."""
        cls._pending.clear()


class ApiSetuSandboxDigiLocker(DigiLockerProvider):
    """API Setu sandbox integration — intentionally unimplemented.

    The team has not confirmed which endpoints `sandbox.api-setu.in` exposes for
    APAAR/ABC ID cards, or whether AICTE can register as a DigiLocker requester
    for this purpose (SPEC 9.4). The configuration keys are already wired
    (`DIGILOCKER_BASE_URL`, `DIGILOCKER_CLIENT_ID`, `DIGILOCKER_CLIENT_SECRET`), so
    filling this in is a self-contained change once the contract is known.

    Expected shape, to be confirmed, not assumed:
      1. redirect the student to the authorisation endpoint with client id,
         redirect URI, state and the requested document type
      2. exchange the returned code for an access token
      3. pull the issued document and parse its fields

    Set `DIGILOCKER_IMPL=apisetu_sandbox` only once steps 1-3 are implemented.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if not settings.digilocker_client_id or not settings.digilocker_client_secret:
            logger.warning(
                "DIGILOCKER_IMPL=apisetu_sandbox selected without credentials configured"
            )

    def start_consent(self, *, student_reference: str, purpose: str) -> ConsentRequest:
        raise NotImplementedError(
            "ApiSetuSandboxDigiLocker is a documented stub: the API Setu sandbox "
            "endpoints for APAAR/ABC documents are not yet confirmed. Use "
            "DIGILOCKER_IMPL=mock for development."
        )

    def fetch_document(self, *, request_id: str, doc_type: str) -> IssuedDocument:
        raise NotImplementedError(
            "ApiSetuSandboxDigiLocker is a documented stub. See start_consent()."
        )
