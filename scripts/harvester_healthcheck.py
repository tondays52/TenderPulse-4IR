"""Container health check for the independent procurement harvester."""

from __future__ import annotations

import json
import os
import sys
import time


STATUS_FILE = "/app/data/harvester_status.json"
MAX_AGE_SECONDS = int(os.getenv("HARVEST_HEALTH_MAX_AGE_SEC", "2100"))


def main() -> int:
    try:
        age = time.time() - os.path.getmtime(STATUS_FILE)
        with open(STATUS_FILE, encoding="utf-8") as handle:
            status = json.load(handle)
        if age > MAX_AGE_SECONDS or status.get("status") == "failed":
            return 1
    except (OSError, ValueError, TypeError):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
