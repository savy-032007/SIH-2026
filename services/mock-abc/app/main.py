"""Mock APAAR / Academic Bank of Credits registry (SPEC 9.3).

Stands in for the real institutional ABC verification API so the platform can be
built and demonstrated without touching a government production system. It
mirrors the *shape* of such an API, not any real one.

Deliberately hostile by default: 50-300 ms of latency and a 1 % random 503, so
the client adapter's retry and backoff is exercised in development rather than
discovered in production. Set `MOCK_ABC_CHAOS=0` for deterministic tests.

The dataset it answers from is the generator's "truth" file — the synthetic
APAAR -> (name, dob, gender) mapping. Students that the generator planted as
"not in registry" are simply absent from it.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import unicodedata
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from rapidfuzz import fuzz

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("mock-abc")

DATASET_PATH = Path(os.getenv("MOCK_ABC_DATASET", "/data/seed/abc_registry.json"))
CHAOS_ENABLED = os.getenv("MOCK_ABC_CHAOS", "1") == "1"
CLIENT_ID = os.getenv("ABC_CLIENT_ID", "aicte-apaar-dev")
CLIENT_SECRET = os.getenv("ABC_CLIENT_SECRET", "dev-only-abc-secret")

_LATENCY_RANGE_MS = (50, 300)
_FAILURE_RATE = 0.01

app = FastAPI(
    title="Mock APAAR / ABC Registry",
    version="1.0.0",
    description=(
        "Synthetic stand-in for the institutional ABC verification API. "
        "Contains no real student data."
    ),
)


# --------------------------------------------------------------------------- #
# Dataset
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=1)
def _registry() -> dict[str, dict[str, Any]]:
    """Load the synthetic truth table, keyed by APAAR ID.

    Cached for the process lifetime. Re-seeding means restarting this service,
    which `make seed` does not do — so the cache is cleared via /admin/reload
    rather than guessing at file mtimes.
    """
    if not DATASET_PATH.exists():
        logger.warning("dataset %s not found; registry is empty until `make seed` runs", DATASET_PATH)
        return {}

    with DATASET_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    records = payload["records"] if isinstance(payload, dict) else payload
    registry = {str(record["apaar_id"]): record for record in records}
    logger.info("loaded %d APAAR records from %s", len(registry), DATASET_PATH)
    return registry


def _normalize_name(value: str) -> str:
    """Accent-strip, lowercase and collapse — matched to the client's normaliser."""
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^\w\s]", " ", ascii_only, flags=re.UNICODE).casefold()
    return " ".join(cleaned.split())


def _mask_name(name: str) -> str:
    return " ".join(
        word[0] + "*" * (len(word) - 1) if len(word) > 1 else word for word in name.split()
    )


async def _chaos() -> None:
    """Latency and random failure, so retry/backoff is proven in dev (SPEC 9.3)."""
    if not CHAOS_ENABLED:
        return
    await asyncio.sleep(random.uniform(*_LATENCY_RANGE_MS) / 1000)
    if random.random() < _FAILURE_RATE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registry temporarily unavailable, please retry",
        )


def _authenticate(client_id: str | None, client_secret: str | None) -> None:
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid x-client-id / x-client-secret",
        )


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #


class VerifyRequest(BaseModel):
    apaar_id: str = Field(examples=["123456789012"])
    name: str = Field(examples=["Aarav Sharma"])
    dob: date = Field(examples=["2008-04-17"])


class MatchResult(BaseModel):
    name_score: int = Field(ge=0, le=100, description="rapidfuzz token_sort_ratio, 0-100")
    dob_match: bool


class VerifyResponse(BaseModel):
    exists: bool
    match: MatchResult | None = None
    masked_name: str | None = None
    status: str = Field(description="ACTIVE, INACTIVE or NOT_FOUND")


class StatusResponse(BaseModel):
    exists: bool
    active: bool


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #


@app.get("/health", tags=["ops"])
async def health() -> dict[str, Any]:
    return {"status": "ok", "records": len(_registry()), "chaos": CHAOS_ENABLED}


@app.post("/v1/apaar/verify", response_model=VerifyResponse, tags=["apaar"])
async def verify_apaar(
    payload: VerifyRequest,
    x_client_id: Annotated[str | None, Header(alias="x-client-id")] = None,
    x_client_secret: Annotated[str | None, Header(alias="x-client-secret")] = None,
) -> VerifyResponse:
    """Check an APAAR ID and score the name and date of birth against the registry.

    Returns a *score*, not a verdict: whether 84 is close enough is the
    platform's policy decision (V2.NAME_MISMATCH thresholds), not the registry's.
    """
    _authenticate(x_client_id, x_client_secret)
    await _chaos()

    record = _registry().get(payload.apaar_id.strip())
    if record is None:
        return VerifyResponse(exists=False, status="NOT_FOUND")

    name_score = int(
        round(fuzz.token_sort_ratio(_normalize_name(payload.name), _normalize_name(record["name"])))
    )
    return VerifyResponse(
        exists=True,
        match=MatchResult(name_score=name_score, dob_match=str(record["dob"]) == str(payload.dob)),
        masked_name=_mask_name(record["name"]),
        status="ACTIVE" if record.get("active", True) else "INACTIVE",
    )


@app.get("/v1/apaar/{apaar_id}/status", response_model=StatusResponse, tags=["apaar"])
async def apaar_status(
    apaar_id: str,
    x_client_id: Annotated[str | None, Header(alias="x-client-id")] = None,
    x_client_secret: Annotated[str | None, Header(alias="x-client-secret")] = None,
) -> StatusResponse:
    """Existence and active state only — no identity data, so no consent needed."""
    _authenticate(x_client_id, x_client_secret)
    await _chaos()

    record = _registry().get(apaar_id.strip())
    if record is None:
        return StatusResponse(exists=False, active=False)
    return StatusResponse(exists=True, active=bool(record.get("active", True)))


@app.post("/admin/reload", tags=["ops"])
async def reload_dataset() -> dict[str, Any]:
    """Re-read the dataset after `make seed` regenerates it."""
    _registry.cache_clear()
    return {"status": "reloaded", "records": len(_registry())}
