"""Create the first production administrator from local environment settings.

The password is read only from BOOTSTRAP_ADMIN_PASSWORD, hashed before storage,
and never written to stdout, logs, or the database in clear text.
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.auth_jwt import ROLE_ADMIN
from backend.auth_manager import auth_manager
from backend.database import SessionLocal
from backend.models import UserModel


def provision_admin(email: str, password: str, name: str, agency: str) -> None:
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("A valid administrator email is required.")
    if len(password) < 16:
        raise ValueError("BOOTSTRAP_ADMIN_PASSWORD must be at least 16 characters.")

    db = SessionLocal()
    try:
        if db.query(UserModel).filter(UserModel.email == email).first():
            raise ValueError("An account already exists for this administrator email; refusing to overwrite it.")
        db.add(UserModel(
            email=email,
            name=name.strip() or "TenderPulse Administrator",
            password_hash=auth_manager._hash_password(password),
            salt="pbkdf2-embedded",
            role=ROLE_ADMIN,
            agency=agency.strip() or "TenderPulse",
            is_active=True,
        ))
        db.commit()
    finally:
        db.close()


def main() -> int:
    load_dotenv(override=False)
    parser = argparse.ArgumentParser(description="Provision the first TenderPulse administrator.")
    parser.add_argument("--email", default=os.getenv("BOOTSTRAP_ADMIN_EMAIL", ""))
    parser.add_argument("--name", default=os.getenv("BOOTSTRAP_ADMIN_NAME", "TenderPulse Administrator"))
    parser.add_argument("--agency", default=os.getenv("BOOTSTRAP_ADMIN_AGENCY", "TenderPulse"))
    args = parser.parse_args()

    try:
        provision_admin(args.email, os.getenv("BOOTSTRAP_ADMIN_PASSWORD", ""), args.name, args.agency)
    except ValueError as error:
        print(f"Administrator bootstrap failed: {error}", file=sys.stderr)
        return 1

    print(f"Administrator account provisioned for {args.email.strip().lower()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
