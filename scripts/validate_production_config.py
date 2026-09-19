"""Fail fast when a production deployment has unsafe configuration.

The script intentionally reports only the names of invalid settings, never their
values. It is invoked by the container before database migrations and FastAPI
start, so a bad deployment cannot become a partially-running service.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv


PLACEHOLDER_MARKERS = ("change-me", "replace", "example", "development", "placeholder")


def _is_safe_secret(value: str, minimum_length: int) -> bool:
    normalized = value.strip().lower()
    return (
        len(value.strip()) >= minimum_length
        and not any(marker in normalized for marker in PLACEHOLDER_MARKERS)
    )


def validate() -> list[str]:
    """Return safe, actionable configuration errors for a production runtime."""
    load_dotenv(override=False)
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    if environment != "production":
        return []

    errors: list[str] = []
    if not _is_safe_secret(os.getenv("JWT_SECRET_KEY", ""), 32):
        errors.append("JWT_SECRET_KEY must be a non-placeholder secret of at least 32 characters")
    if not _is_safe_secret(os.getenv("POSTGRES_PASSWORD", ""), 16):
        errors.append("POSTGRES_PASSWORD must be a non-placeholder secret of at least 16 characters")

    origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
    if not origins or "*" in origins:
        errors.append("CORS_ORIGINS must list explicit trusted HTTPS origins in production")
    elif all("localhost" in origin or "127.0.0.1" in origin for origin in origins):
        errors.append("CORS_ORIGINS must include at least one production origin, not only localhost")

    if os.getenv("STRICT_AUTH", "true").strip().lower() != "true":
        errors.append("STRICT_AUTH must be true in production")
    if os.getenv("ALLOW_PUBLIC_REGISTRATION", "false").strip().lower() == "true":
        errors.append("ALLOW_PUBLIC_REGISTRATION must be false in production")
    return errors


if __name__ == "__main__":
    configuration_errors = validate()
    if configuration_errors:
        print("Production configuration preflight failed:", file=sys.stderr)
        for error in configuration_errors:
            print(f"- {error}", file=sys.stderr)
        sys.exit(1)
    print("Production configuration preflight passed.")
