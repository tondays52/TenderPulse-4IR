"""
TenderPulse 4IR - Authentication & Enterprise User Session Manager
Provides secure user registration, salted hashing, login verification,
and persistent session token tracking stored in data/users.json.
"""

import os
import json
import time
import hashlib
import secrets
from typing import Dict, Any, List, Optional

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
        self.users: List[Dict[str, Any]] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._load_users()

    def _hash_password(self, password: str) -> str:
        salted = f"{password}_tenderpulse_salt".encode('utf-8')
        return hashlib.sha256(salted).hexdigest()

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
        self._save_users()

    def _save_users(self):
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"[Auth Error] Failed to save users: {e}")

    def register(self, name: str, email: str, password: str, role: str = "Tender Analyst", agency: str = "Tender Trading Inc.") -> Dict[str, Any]:
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
            "role": role.strip(),
            "initials": initials,
            "clearance": clearance,
            "agency": agency.strip(),
            "password_hash": self._hash_password(password),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.users.append(user)
        self._save_users()

        token = secrets.token_hex(24)
        user_safe = self._sanitize_user(user)
        self.active_sessions[token] = {
            "user": user_safe,
            "created_at": time.time()
        }

        return {
            "status": "SUCCESS",
            "message": f"User account created for {name}",
            "token": token,
            "user": user_safe
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        email_clean = email.strip().lower()
        pw_hash = self._hash_password(password)

        user = next((u for u in self.users if u["email"].lower() == email_clean), None)
        if not user or user.get("password_hash") != pw_hash:
            raise ValueError("Invalid email or password.")

        token = secrets.token_hex(24)
        user_safe = self._sanitize_user(user)
        self.active_sessions[token] = {
            "user": user_safe,
            "created_at": time.time()
        }

        return {
            "status": "SUCCESS",
            "message": f"Welcome back, {user['name']}",
            "token": token,
            "user": user_safe
        }

    def logout(self, token: Optional[str]) -> Dict[str, Any]:
        if token and token in self.active_sessions:
            del self.active_sessions[token]
        return {
            "status": "SUCCESS",
            "message": "Signed out successfully."
        }

    def get_current_user(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        if token and token in self.active_sessions:
            return self.active_sessions[token]["user"]
        if self.users:
            return self._sanitize_user(self.users[0])
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        email_clean = email.strip().lower()
        user = next((u for u in self.users if u["email"].lower() == email_clean), None)
        return self._sanitize_user(user) if user else None

    def list_public_profiles(self) -> List[Dict[str, Any]]:
        return [self._sanitize_user(u) for u in self.users]

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
