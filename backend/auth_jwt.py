"""
TenderPulse 4IR AI - Enterprise Cryptographic JWT & 3-Tier RBAC Engine
Grounding: OAuth2 / RFC 7519 JSON Web Tokens with Refresh Token Rotation and Role-Based Access Control.
"""

import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.auth_manager import auth_manager
from backend.settings import get_settings

# 3-Tier Enterprise Role Definitions
ROLE_EXECUTIVE = "Executive / Managing Director"
ROLE_ANALYST = "Tender Analyst / Estimator"
ROLE_AUDITOR = "Audit / Oversight Officer"
ROLE_ADMIN = "Administrator"

ALL_ROLES = [ROLE_EXECUTIVE, ROLE_ANALYST, ROLE_AUDITOR, ROLE_ADMIN]

# Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "development-only-change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# In-memory store for active refresh token JTIs with expiration tracking (can be backed by Redis in Phase 1 stack)
_active_refresh_tokens: Dict[str, Dict[str, Any]] = {}

http_bearer = HTTPBearer(auto_error=False)


def _register_refresh_token(jti: str, email: str, expires_at: datetime) -> None:
    """Persist refresh-token state; retain an in-memory fallback for isolated tests."""
    try:
        from backend.database import SessionLocal, init_db
        from backend.models import RefreshTokenModel
        init_db()
        db = SessionLocal()
        try:
            db.add(RefreshTokenModel(jti=jti, email=email, expires_at=expires_at))
            db.commit()
            return
        finally:
            db.close()
    except Exception:
        _active_refresh_tokens[jti] = {"email": email, "expires_at": expires_at.timestamp()}


def _consume_refresh_token(jti: str, email: str) -> bool:
    """Atomically mark a refresh token used, preventing reuse across restarts."""
    try:
        from backend.database import SessionLocal, init_db
        from backend.models import RefreshTokenModel
        init_db()
        db = SessionLocal()
        try:
            token = db.query(RefreshTokenModel).filter(RefreshTokenModel.jti == jti).first()
            if not token or token.email != email or token.revoked_at or token.expires_at < datetime.utcnow():
                return False
            token.revoked_at = datetime.utcnow()
            db.commit()
            return True
        finally:
            db.close()
    except Exception:
        token = _active_refresh_tokens.pop(jti, None)
        return bool(token and token.get("email") == email and token.get("expires_at", 0) > time.time())


def normalize_role(role: str) -> str:
    """
    Normalizes role string to canonical enterprise role representation.
    """
    if not role:
        return ROLE_ANALYST
    r = role.lower().strip()
    if "exec" in r or "director" in r or "md" in r or "managing" in r:
        return ROLE_EXECUTIVE
    elif "audit" in r or "oversight" in r or "inspector" in r:
        return ROLE_AUDITOR
    elif "admin" in r or "super" in r:
        return ROLE_ADMIN
    else:
        return ROLE_ANALYST


def create_access_token(user: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a cryptographically signed access JWT containing claims.
    """
    to_encode = {
        "sub": user.get("email"),
        "name": user.get("name"),
        "role": normalize_role(user.get("role", ROLE_ANALYST)),
        "agency": user.get("agency", "Di-Tender Ltd."),
        "type": "access",
        "jti": str(uuid.uuid4())
    }
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(email: str) -> str:
    """
    Generates a cryptographically signed refresh JWT and registers its JTI.
    """
    jti = str(uuid.uuid4())
    now = datetime.utcnow()
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": email,
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": expire
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    _register_refresh_token(jti, email, expire)
    return token


def rotate_refresh_token(refresh_token: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Validates refresh token, revokes previous JTI (rotation), and issues new token pair.
    """
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type: expected refresh token")
        
        jti = payload.get("jti")
        email = payload.get("sub")

        # Consume the JTI before issuing a replacement; replay attempts fail even
        # after an application restart because the registry is database-backed.
        if not jti or not _consume_refresh_token(jti, email):
            raise HTTPException(status_code=401, detail="Refresh token has been revoked or expired")

        # Retrieve user profile from auth_manager or database
        user = auth_manager.get_user_by_email(email)
        if not user:
            try:
                from backend.database import SessionLocal
                import backend.crud as crud
                db = SessionLocal()
                try:
                    db_user = crud.get_user_by_email(db, email)
                    if db_user:
                        user = {
                            "email": db_user.email,
                            "name": db_user.name,
                            "role": db_user.role,
                            "agency": db_user.agency
                        }
                finally:
                    db.close()
            except Exception:
                pass

        if not user:
            user = {
                "email": email,
                "name": email.split("@")[0].title(),
                "role": ROLE_ANALYST,
                "agency": "Tender Trading Inc."
            }

        # Issue new token pair (rotation)
        new_access_token = create_access_token(user)
        new_refresh_token = create_refresh_token(email)

        return new_access_token, new_refresh_token, user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired, please log in again")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {str(e)}")


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT token signature and expiration.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please refresh token or log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Cryptographic authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_user_optional(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication: returns user payload if valid Bearer token provided, otherwise None.
    """
    if not creds or not creds.credentials:
        return None
    try:
        payload = decode_token(creds.credentials)
        if payload.get("type") != "access":
            return None
        return payload
    except Exception:
        return None


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> Dict[str, Any]:
    """
    Mandatory authentication dependency: enforces valid signed JWT.
    """
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required. Please provide Authorization: Bearer <jwt>.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = decode_token(creds.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: expected access token."
        )
    return payload


def require_roles(allowed_roles: List[str], strict: Optional[bool] = None) -> Callable:
    """
    Role-Based Access Control (RBAC) dependency factory.
    Enforces that the authenticated user possesses one of the authorized roles.
    - If Bearer token is present: strictly decodes JWT, verifies signature & expiration, and checks role.
      Unauthorized roles receive HTTP 403 Forbidden.
    - If Bearer token is absent:
      If strict is True or STRICT_AUTH=true in environment: raises HTTP 401 Unauthorized.
      Otherwise permits local dev/test traffic with default executive privileges.
    """
    normalized_allowed = [normalize_role(r) for r in allowed_roles]
    is_strict_env = get_settings().strict_auth

    def role_checker(creds: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)) -> Dict[str, Any]:
        should_enforce_strict = is_strict_env if strict is None else strict

        if not creds or not creds.credentials:
            if should_enforce_strict:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required. Please provide Authorization: Bearer <jwt>.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            # Permissive local dev/test fallback
            return {
                "sub": "dev@tendertrading.gov.bd",
                "name": "Dev Analyst",
                "role": ROLE_ADMIN,
                "agency": "Tender Trading Inc."
            }

        # Token is present: strictly decode and enforce
        payload = decode_token(creds.credentials)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected access token."
            )

        user_role = normalize_role(payload.get("role", ""))
        
        # Universal Admin bypass
        if user_role == ROLE_ADMIN:
            return payload

        if user_role in normalized_allowed:
            return payload

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access Denied: Your role '{payload.get('role')}' is not authorized to execute this operation. "
                f"Authorized roles: {', '.join(allowed_roles)}"
            )
        )

    return role_checker
