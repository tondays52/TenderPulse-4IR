"""Regression checks for safe PostgreSQL URL construction."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def test_reserved_password_characters_are_encoded() -> None:
    environment = os.environ.copy()
    environment.update({
        "DATABASE_URL": "",
        "POSTGRES_HOST": "postgres",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "tenderpulse",
        "POSTGRES_PASSWORD": "safe@password/with?reserved",
        "POSTGRES_DB": "tenderpulse",
    })
    result = subprocess.run(
        [sys.executable, "-c", "from backend.database import resolve_database_url; print(resolve_database_url())"],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=True,
    )
    url = result.stdout.strip()
    assert "safe%40password%2Fwith%3Freserved" in url
    assert "@postgres:5432" in url


def test_alembic_uses_the_same_resolved_database_url() -> None:
    environment = os.environ.copy()
    environment.update({
        "DATABASE_URL": "",
        "POSTGRES_HOST": "postgres",
        "POSTGRES_PASSWORD": "safe@password/with?reserved",
    })
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "current"],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert "invalid interpolation syntax" not in result.stderr, result.stderr
    assert "Could not parse SQLAlchemy URL" not in result.stderr, result.stderr


if __name__ == "__main__":
    test_reserved_password_characters_are_encoded()
    test_alembic_uses_the_same_resolved_database_url()
    print("database URL encoding tests passed")
