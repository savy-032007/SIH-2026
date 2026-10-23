"""External system adapters: APAAR/ABC registry and DigiLocker (SPEC 9.4)."""

from app.integrations.abc_registry import (
    AbcRegistry,
    AbcRegistryError,
    AbcRegistryProduction,
    AbcRegistryUnavailableError,
    ApaarStatusResult,
    ApaarVerification,
    MockAbcRegistry,
)
from app.integrations.digilocker import (
    ApiSetuSandboxDigiLocker,
    ConsentRequest,
    DigiLockerError,
    DigiLockerProvider,
    IssuedDocument,
    MockDigiLocker,
)
from app.integrations.factory import (
    build_abc_registry,
    build_digilocker,
    get_abc_registry,
    get_digilocker,
    reset_adapter_cache,
)

__all__ = [
    "AbcRegistry",
    "AbcRegistryError",
    "AbcRegistryProduction",
    "AbcRegistryUnavailableError",
    "ApaarStatusResult",
    "ApaarVerification",
    "ApiSetuSandboxDigiLocker",
    "ConsentRequest",
    "DigiLockerError",
    "DigiLockerProvider",
    "IssuedDocument",
    "MockAbcRegistry",
    "MockDigiLocker",
    "build_abc_registry",
    "build_digilocker",
    "get_abc_registry",
    "get_digilocker",
    "reset_adapter_cache",
]
