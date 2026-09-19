"""Regression checks for secure administrator provisioning."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "bootstrap_admin.py"


def test_password_is_not_disclosed_when_validation_fails() -> None:
    secret = "this-temporary-secret-must-not-appear-in-output"
    environment = os.environ.copy()
    environment.update({"BOOTSTRAP_ADMIN_EMAIL": "admin@example.test", "BOOTSTRAP_ADMIN_PASSWORD": secret})
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    # The active production database connection is deliberately unavailable to
    # this isolated test; regardless of failure mode, secrets must never leak.
    assert secret not in result.stdout
    assert secret not in result.stderr


if __name__ == "__main__":
    test_password_is_not_disclosed_when_validation_fails()
    print("administrator bootstrap safety test passed")
