"""Application settings, loaded from the environment (see .env.example)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    web_origin: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://apaar:apaar_dev_password@postgres:5432/apaar"
    test_database_url: str = (
        "postgresql+psycopg://apaar:apaar_dev_password@postgres:5432/apaar_test"
    )

    # --- crypto -----------------------------------------------------------
    field_master_key: str = "ZGV2LW9ubHktbWFzdGVyLWtleS0zMi1ieXRlcyEhISE="
    hash_pepper: str = "dev-only-hash-pepper-change-me"
    key_provider: Literal["local", "kms"] = "local"
    key_id: str = "local-v1"

    # --- auth -------------------------------------------------------------
    jwt_secret: str = "dev-only-jwt-secret-change-me"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7
    mfa_token_ttl_minutes: int = 5
    lockout_max_attempts: int = 5
    lockout_window_minutes: int = 15
    demo_user_password: str = "Demo@1234"

    # --- integrations -----------------------------------------------------
    abc_registry_impl: Literal["mock", "production"] = "mock"
    abc_base_url: str = "http://mock-abc:9001"
    abc_client_id: str = "aicte-apaar-dev"
    abc_client_secret: str = "dev-only-abc-secret"
    abc_timeout_seconds: float = 5.0
    abc_max_attempts: int = 3

    digilocker_impl: Literal["mock", "apisetu_sandbox"] = "apisetu_sandbox"
    digilocker_client_id: str = "in.gov.sandbox"
    digilocker_client_secret: str = "demokey123456ABCD789"
    digilocker_api_key: str = "demokey123456ABCD789"
    digilocker_base_url: str = "https://sandbox.api-setu.in"

    # --- paths ------------------------------------------------------------
    data_dir: str = "/data"
    seed_dir: str = "/data/seed"
    rules_dir: str = "/data/rules"
    reference_dir: str = "/data/reference"

    @field_validator("data_dir", "seed_dir", "rules_dir", "reference_dir", mode="before")
    @classmethod
    def _resolve_path_if_missing(cls, value: str) -> str:
        from pathlib import Path
        p = Path(value)
        if p.exists():
            return value
        # Fallback to local services/api/data or project root /data
        base = Path(__file__).resolve().parent.parent / "data"
        if base.exists():
            sub = p.name
            target = base / sub if sub != "data" else base
            if target.exists():
                return str(target)
            return str(base)
        return value

    # --- synthetic data ---------------------------------------------------
    seed: int = 20262026
    gen_institutions: int = Field(default=100, ge=1)
    gen_students: int = Field(default=35000, ge=1)

    @field_validator("field_master_key")
    @classmethod
    def _master_key_is_32_bytes(cls, value: str) -> str:
        import base64

        try:
            raw = base64.b64decode(value, validate=True)
        except Exception as exc:  # pragma: no cover - configuration error path
            raise ValueError("FIELD_MASTER_KEY must be valid base64") from exc
        if len(raw) != 32:
            raise ValueError(
                f"FIELD_MASTER_KEY must decode to exactly 32 bytes, got {len(raw)}"
            )
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
