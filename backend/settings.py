"""Central runtime configuration for TenderPulse.

Configuration deliberately has secure production defaults while preserving an
explicit development mode for local work.  Keep secrets in the environment or
the deployment secret store; never add them to this module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Tuple


def _csv(value: str) -> Tuple[str, ...]:
    return tuple(item.strip().rstrip("/") for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    environment: str
    cors_origins: Tuple[str, ...]
    strict_auth: bool
    allow_public_registration: bool
    max_upload_bytes: int

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    if environment not in {"development", "test", "staging", "production"}:
        environment = "development"

    raw_origins = os.getenv("CORS_ORIGINS", "").strip()
    # Wildcard origins cannot safely be combined with credentialed requests.
    # Same-origin requests do not require CORS, so production treats '*' as an
    # empty allow-list until deployers explicitly set trusted origins.
    if raw_origins == "*":
        origins: Tuple[str, ...] = () if environment == "production" else ("*")
    else:
        origins = _csv(raw_origins)

    strict_default = environment in {"staging", "production"}
    strict_auth = os.getenv("STRICT_AUTH", str(strict_default)).lower() == "true"
    public_registration = os.getenv("ALLOW_PUBLIC_REGISTRATION", "false").lower() == "true"
    max_upload_mb = max(1, min(int(os.getenv("MAX_UPLOAD_MB", "25")), 100))

    return Settings(
        environment=environment,
        cors_origins=origins,
        strict_auth=strict_auth,
        allow_public_registration=public_registration,
        max_upload_bytes=max_upload_mb * 1024 * 1024,
    )
