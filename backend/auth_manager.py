"""
TenderPulse 4IR - Authentication & Enterprise User Session Manager
Provides secure user registration, salted hashing, login verification,
and persistent session token tracking stored in data/users.json.
"""

import os
import json
import time
import hashlib
import hmac
import secrets
from typing import Dict, Any, List, Optional
from backend.settings import get_settings

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Initial Enterprise Directory
DEFAULT_USERS = [
    {
        "id": "usr_admin",
        "name": "Enterprise Executive",
        "email": "admin@tendertrading.gov.bd",
        "role": "Managing Director & Lead",
        "initials": "EE",
        "clearance": "Level 4 (Executive)",
        "agency": "Tender Trading Inc.",
        "password_hash": hashlib.sha256(b"admin123_tenderpulse_salt").hexdigest(),
        "created_at": "2026-01-01 00:00:00"
    },
    {
        "id": "usr_02",
        "name": "Engr. M. A. Karim, FIEB",
        "email": "karim.engr@tendertrading.gov.bd",
        "role": "Chief Procurement Estimator",
        "initials": "MK",
        "clearance": "Level 3 (Senior)",
        "agency": "RHD Engineering Division",
        "password_hash": hashlib.sha256(b"karim123_tenderpulse_salt").hexdigest(),
        "created_at": "2026-01-15 08:30:00"
    },
    {
        "id": "usr_03",
        "name": "Tanzina Rahman, PMP",
        "email": "tanzina.pmp@tendertrading.gov.bd",
        "role": "GovTech Bid Strategist",
        "initials": "TR",
        "clearance": "Level 3 (Senior)",
        "agency": "LGED Procurement Cell",
        "password_hash": hashlib.sha256(b"tanzina123_tenderpulse_salt").hexdigest(),
        "created_at": "2026-02-01 10:15:00"
    },
    {
        "id": "usr_04",
        "name": "Dr. S. K. Majumder",
        "email": "majumder.law@tendertrading.gov.bd",
        "role": "Legal & SMT Compliance Auditor",
        "initials": "SM",
        "clearance": "Level 4 (Executive)",
        "agency": "CPTU Legal Review Board",
        "password_hash": hashlib.sha256(b"majumder123_tenderpulse_salt").hexdigest(),
        "created_at": "2026-02-10 14:00:00"
    }
]

class AuthManager:
    def __init__(self):
        # Retained only as a one-time import source for existing installations.
        self.users: List[Dict[str, Any]] = []
        self._migration_complete = False
        self._load_users()

    def _hash_password(self, password: str) -> str:
        """Create a self-describing PBKDF2-SHA256 password hash."""
        iterations = 600_000
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> tuple[bool, bool]:
        """Return (valid, needs_upgrade), including support for legacy seed users."""
        if stored_hash.startswith("pbkdf2_sha256$"):
            try:
                _, iterations, salt, expected = stored_hash.split("$", 3)
                candidate = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
                ).hex()
                return hmac.compare_digest(candidate, expected), False
            except (TypeError, ValueError):
                return False, False

        # Legacy JSON accounts are upgraded after their next successful login.
        legacy = hashlib.sha256(f"{password}_tenderpulse_salt".encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored_hash), True

    def _db_session(self):
        from backend.database import SessionLocal, init_db
        import backend.models  # Ensure all SQLAlchemy models are registered before create_all.
        init_db()
        return SessionLocal()

    def _ensure_migrated(self) -> None:
        """Import legacy users.json records once without overwriting database users."""
        if self._migration_complete:
            return
        db = self._db_session()
        try:
            from backend.models import UserModel
            for user in self.users:
                email = user.get("email", "").strip().lower()
                if not email or db.query(UserModel).filter(UserModel.email == email).first():
                    continue
                db.add(UserModel(
                    email=email,
                    name=user.get("name", "User"),
                    password_hash=user.get("password_hash", ""),
                    salt="legacy-json-migration",
                    role=user.get("role", "Tender Analyst"),
                    agency=user.get("agency", "Tender Trading Inc."),
                    is_active=True,
                ))
            db.commit()
            self._migration_complete = True
        finally:
            db.close()

    @staticmethod
    def _to_public_user(user) -> Dict[str, Any]:
        return {
            "id": str(user.id), "name": user.name, "email": user.email,
            "role": user.role, "initials": "".join(part[0] for part in user.name.split()[:2]).upper() or "TP",
            "clearance": "Level 4 (Executive)" if "admin" in user.role.lower() or "director" in user.role.lower() else "Level 3 (Senior)",
            "agency": user.agency, "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    def _generate_initials(self, name: str) -> str:
        parts = [p for p in name.replace('.', ' ').split() if p and not p.lower() in ('engr', 'dr', 'fieb', 'pmp', 'adv')]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        elif len(parts) == 1:
            return parts[0][:2].upper()
        return "TP"

    def _load_users(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    self.users = json.load(f)
                    return
            except Exception:
                pass
        self.users = list(DEFAULT_USERS)

    def _save_users(self):
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"[Auth Error] Failed to save users: {e}")

    def register(self, name: str, email: str, password: str, role: str = "Tender Analyst", agency: str = "Tender Trading Inc.") -> Dict[str, Any]:
        if not get_settings().allow_public_registration:
            raise PermissionError("Self-registration is disabled. Ask an administrator to provision your account.")
        if len(password) < 12:
            raise ValueError("Password must contain at least 12 characters.")
        email_clean = email.strip().lower()
        if any(u["email"].lower() == email_clean for u in self.users):
            raise ValueError(f"An account with email '{email_clean}' already exists.")

        user_id = f"usr_{secrets.token_hex(4)}"
        initials = self._generate_initials(name)
        clearance = "Level 4 (Executive)" if "director" in role.lower() or "executive" in role.lower() or "admin" in role.lower() else "Level 3 (Senior)"

        user = {
            "id": user_id,
            "name": name.strip(),
            "email": email_clean,
            # Public registration must never be able to mint privileged roles.
            "role": "Tender Analyst",
            "initials": initials,
            "clearance": clearance,
            "agency": agency.strip(),
            "password_hash": self._hash_password(password),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        db = self._db_session()
        try:
            from backend.models import UserModel
            db_user = UserModel(
                email=email_clean, name=user["name"], password_hash=user["password_hash"], salt="pbkdf2-embedded",
                role=user["role"], agency=user["agency"], is_active=True,
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            user_safe = self._to_public_user(db_user)
        finally:
            db.close()

        return {
            "status": "SUCCESS",
            "message": f"User account created for {name}",
            "user": user_safe
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        email_clean = email.strip().lower()
        self._ensure_migrated()
        db = self._db_session()
        try:
            from backend.models import UserModel
            user = db.query(UserModel).filter(UserModel.email == email_clean).first()
            if not user or not user.is_active:
                raise ValueError("Invalid email or password.")
            valid, needs_upgrade = self._verify_password(password, user.password_hash)
            if not valid:
                raise ValueError("Invalid email or password.")
            if needs_upgrade:
                user.password_hash = self._hash_password(password)
                user.salt = "pbkdf2-embedded"
                db.commit()
                db.refresh(user)
            user_safe = self._to_public_user(user)
            return {"status": "SUCCESS", "message": f"Welcome back, {user.name}", "user": user_safe}
        finally:
            db.close()

    def logout(self, token: Optional[str]) -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "message": "Signed out successfully."
        }

    def get_current_user(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        self._ensure_migrated()
        db = self._db_session()
        try:
            from backend.models import UserModel
            user = db.query(UserModel).filter(UserModel.email == email.strip().lower()).first()
            return self._to_public_user(user) if user else None
        finally:
            db.close()

    def list_public_profiles(self) -> List[Dict[str, Any]]:
        self._ensure_migrated()
        db = self._db_session()
        try:
            from backend.models import UserModel
            return [self._to_public_user(user) for user in db.query(UserModel).filter(UserModel.is_active.is_(True)).all()]
        finally:
            db.close()

    def _sanitize_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "initials": user.get("initials", "TP"),
            "clearance": user.get("clearance", "Level 3 (Senior)"),
            "agency": user.get("agency", "Tender Trading Inc."),
            "created_at": user.get("created_at")
        }

# Global Singleton
auth_manager = AuthManager()
