"""FastAPI application entrypoint.

Phase 1 exposes health, auth, audit and read-only rules. Security headers and
real rate limits are deliberately light here and hardened in Phase 5 (SPEC
section 12).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.db import engine
from app.routers import audit_log, auth, institution, rules

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "starting api environment=%s abc=%s digilocker=%s",
        settings.environment,
        settings.abc_registry_impl,
        settings.digilocker_impl,
    )
    yield
    engine.dispose()


app = FastAPI(
    title="APAAR Student Data Management & Verification Platform",
    version="0.1.0",
    description=(
        "AICTE student-level data submission, validation, monitoring and "
        "verification, keyed by APAAR ID.\n\n"
        "**All data in development is synthetic.** No real student records, and "
        "no calls to any government production system."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(institution.router, prefix=API_PREFIX)
app.include_router(audit_log.router, prefix=API_PREFIX)
app.include_router(rules.router, prefix=API_PREFIX)


@app.get("/health", tags=["ops"], summary="Liveness and database connectivity")
def health() -> dict[str, Any]:
    """Report whether the service and its database are reachable.

    Used by the compose healthcheck and the web scaffold's status page.
    """
    database_ok = True
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - exercised by stopping postgres
        database_ok = False
        logger.warning("health check could not reach the database: %s", exc)

    return {
        "status": "ok" if database_ok else "degraded",
        "environment": settings.environment,
        "database": "up" if database_ok else "down",
        "adapters": {
            "abc_registry": settings.abc_registry_impl,
            "digilocker": settings.digilocker_impl,
        },
    }
