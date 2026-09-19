"""Regression checks for the production configuration preflight."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PREFLIGHT = ROOT / "scripts" / "validate_production_config.py"


def run_preflight(**overrides: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(overrides)
    return subprocess.run(
        [sys.executable, str(PREFLIGHT)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_safe_production_configuration_passes() -> None:
    result = run_preflight(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="ci-safe-jwt-secret-with-at-least-thirty-two-characters",
        POSTGRES_PASSWORD="ci-safe-postgres-password-with-length",
        CORS_ORIGINS="https://tenders.example.gov.bd",
        STRICT_AUTH="true",
        ALLOW_PUBLIC_REGISTRATION="false",
    )
    assert result.returncode == 0, result.stderr


def test_placeholder_secret_is_rejected_without_disclosure() -> None:
    placeholder = "replace-with-a-secret"
    result = run_preflight(
        ENVIRONMENT="production",
        JWT_SECRET_KEY=placeholder,
        POSTGRES_PASSWORD="ci-safe-postgres-password-with-length",
        CORS_ORIGINS="https://tenders.example.gov.bd",
        STRICT_AUTH="true",
        ALLOW_PUBLIC_REGISTRATION="false",
    )
    assert result.returncode == 1
    assert "JWT_SECRET_KEY" in result.stderr
    assert placeholder not in result.stderr


if __name__ == "__main__":
    test_safe_production_configuration_passes()
    test_placeholder_secret_is_rejected_without_disclosure()
    print("production configuration preflight tests passed")
