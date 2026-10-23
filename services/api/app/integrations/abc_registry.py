"""APAAR / ABC registry adapters (SPEC 9.4).

The platform never talks to a registry directly — it talks to `AbcRegistry`.
Swapping the mock for the real integration once AICTE is onboarded as an ABC
integrator is a change of one environment variable, with no call-site edits.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.config import Settings

logger = logging.getLogger(__name__)


class AbcRegistryError(Exception):
    """The registry could not be reached or answered unusably."""


class AbcRegistryUnavailableError(AbcRegistryError):
    """Transient failure — worth retrying."""


@dataclass(frozen=True)
class ApaarVerification:
    """Registry answer for one APAAR ID.

    `name_score` is a similarity, not a verdict: the pass/warn/fail bands live in
    the rule set (V2.NAME_MISMATCH), so tightening them never means redeploying
    an adapter.
    """

    exists: bool
    status: str
    name_score: int | None = None
    dob_match: bool | None = None
    masked_name: str | None = None

    @property
    def is_active(self) -> bool:
        return self.exists and self.status == "ACTIVE"


@dataclass(frozen=True)
class ApaarStatusResult:
    exists: bool
    active: bool


class AbcRegistry(ABC):
    """Interface every registry implementation satisfies."""

    @abstractmethod
    def verify(self, apaar_id: str, name: str, dob: date) -> ApaarVerification:
        """Verify an APAAR ID against the registry's identity record.

        Callers must hold a granted consent for the student first (SPEC section 8).
        """

    @abstractmethod
    def status(self, apaar_id: str) -> ApaarStatusResult:
        """Existence and active state only — no identity data is returned."""

    def close(self) -> None:  # pragma: no cover - default is a no-op
        """Release any held connections."""


class MockAbcRegistry(AbcRegistry):
    """Talks to the `services/mock-abc` service over HTTP.

    Deliberately a real network client rather than an in-process fake: the mock
    service injects latency and 1 % 503s, so this exercises the same timeout and
    backoff path the production adapter will need.
    """

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        """`client` lets tests drive the mock service in-process over ASGI.

        Left as None in normal operation, which builds a real HTTP client.
        """
        self._settings = settings
        self._client = client or httpx.Client(
            base_url=settings.abc_base_url,
            timeout=settings.abc_timeout_seconds,
            headers={
                "x-client-id": settings.abc_client_id,
                "x-client-secret": settings.abc_client_secret,
            },
        )
        self._max_attempts = settings.abc_max_attempts

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """One HTTP call with retry on transient failures.

        Retries 5xx, timeouts and connection errors. Does not retry 4xx: a bad
        client secret or malformed APAAR ID will fail identically every time, and
        hammering the registry with it is both useless and rude.
        """

        @retry(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential_jitter(initial=0.2, max=2.0),
            retry=retry_if_exception_type(AbcRegistryUnavailableError),
            reraise=True,
        )
        def _attempt() -> dict:
            try:
                response = self._client.request(method, url, **kwargs)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                raise AbcRegistryUnavailableError(f"registry unreachable: {exc}") from exc

            if response.status_code >= 500:
                raise AbcRegistryUnavailableError(
                    f"registry returned {response.status_code}"
                )
            if response.status_code >= 400:
                raise AbcRegistryError(
                    f"registry rejected the request ({response.status_code}): {response.text[:200]}"
                )
            return response.json()

        return _attempt()

    def verify(self, apaar_id: str, name: str, dob: date) -> ApaarVerification:
        payload = self._request(
            "POST",
            "/v1/apaar/verify",
            json={"apaar_id": apaar_id, "name": name, "dob": dob.isoformat()},
        )
        match = payload.get("match") or {}
        return ApaarVerification(
            exists=bool(payload.get("exists")),
            status=str(payload.get("status", "NOT_FOUND")),
            name_score=match.get("name_score"),
            dob_match=match.get("dob_match"),
            masked_name=payload.get("masked_name"),
        )

    def status(self, apaar_id: str) -> ApaarStatusResult:
        payload = self._request("GET", f"/v1/apaar/{apaar_id}/status")
        return ApaarStatusResult(
            exists=bool(payload.get("exists")), active=bool(payload.get("active"))
        )

    def close(self) -> None:
        self._client.close()


class AbcRegistryProduction(AbcRegistry):
    """The real integration — intentionally unimplemented.

    AICTE must first be onboarded as an ABC/APAAR integrator, which decides the
    base URL, the credential type and the consent artefact the registry expects
    per lookup. Guessing any of that now would be a stub pretending to be an
    integration.

    When those details arrive, implement `verify` and `status` here against the
    published contract and set `ABC_REGISTRY_IMPL=production`. Nothing else in the
    codebase changes: the interface, the dataclasses and the consent gate are
    already in place.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def verify(self, apaar_id: str, name: str, dob: date) -> ApaarVerification:
        raise NotImplementedError(
            "AbcRegistryProduction is a documented stub. Real ABC registry "
            "endpoints and credentials are not available until AICTE is onboarded "
            "as an integrator. Use ABC_REGISTRY_IMPL=mock for development."
        )

    def status(self, apaar_id: str) -> ApaarStatusResult:
        raise NotImplementedError(
            "AbcRegistryProduction is a documented stub. See verify()."
        )
