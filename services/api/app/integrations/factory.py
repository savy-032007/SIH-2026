"""Adapter selection by environment variable (SPEC 9.4).

"Production swap = change one env var once AICTE onboards as DigiLocker requester
/ ABC integrator" — this module is where that promise is kept.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.integrations.abc_registry import (
    AbcRegistry,
    AbcRegistryProduction,
    MockAbcRegistry,
)
from app.integrations.digilocker import (
    ApiSetuSandboxDigiLocker,
    DigiLockerProvider,
    MockDigiLocker,
)


def build_abc_registry(settings: Settings) -> AbcRegistry:
    if settings.abc_registry_impl == "production":
        return AbcRegistryProduction(settings)
    return MockAbcRegistry(settings)


def build_digilocker(settings: Settings) -> DigiLockerProvider:
    if settings.digilocker_impl == "apisetu_sandbox":
        return ApiSetuSandboxDigiLocker(settings)
    return MockDigiLocker(settings)


@lru_cache(maxsize=1)
def _cached_abc_registry() -> AbcRegistry:
    """One registry client per process, so its connection pool is reused."""
    return build_abc_registry(get_settings())


@lru_cache(maxsize=1)
def _cached_digilocker() -> DigiLockerProvider:
    return build_digilocker(get_settings())


def get_abc_registry(settings: Settings = Depends(get_settings)) -> AbcRegistry:
    """FastAPI dependency yielding the configured registry adapter."""
    return _cached_abc_registry()


def get_digilocker(settings: Settings = Depends(get_settings)) -> DigiLockerProvider:
    """FastAPI dependency yielding the configured DigiLocker adapter."""
    return _cached_digilocker()


def reset_adapter_cache() -> None:
    """Drop cached adapters so a changed configuration takes effect (tests)."""
    _cached_abc_registry.cache_clear()
    _cached_digilocker.cache_clear()
