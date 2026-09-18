"""
JWT Authentication for GeoShield API.
Provides token creation, verification, and FastAPI dependency injection.
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Secret key for JWT signing — in production, use a proper secret manager
JWT_SECRET = os.getenv("JWT_SECRET", "geoshield-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

security = HTTPBearer(auto_error=False)

# Demo user database (in production, use a real DB with hashed passwords)
# Passwords are hashed with bcrypt
DEMO_USERS = {
    "admin@geoshield.gov.in": {"password_hash": _hash_password("admin123"), "name": "Admin", "role": "admin"},
    "field@geoshield.gov.in": {"password_hash": _hash_password("field123"), "name": "Field Officer", "role": "field_officer"},
    "district@geoshield.gov.in": {"password_hash": _hash_password("district123"), "name": "District Admin", "role": "district_admin"},
    "citizen@geoshield.gov.in": {"password_hash": _hash_password("demo123"), "name": "Citizen", "role": "citizen"},
}


def authenticate_user(email: str, password: str) -> dict | None:
    """Authenticate a user against the demo user database."""
    user = DEMO_USERS.get(email)
    if user and _verify_password(password, user["password_hash"]):
        return {"email": email, "name": user["name"], "role": user["role"]}
    return None


def create_token(user_data: dict) -> str:
    """Create a JWT token for the given user data."""
    payload = {
        "sub": user_data["email"],
        "name": user_data["name"],
        "role": user_data["role"],
        "iat": datetime.now(timezone.utc).replace(tzinfo=None),
        "exp": datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token. Returns the payload or raises."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI dependency that extracts and verifies the current user from the
    Authorization header. Raises 401 if missing or invalid."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_token(credentials.credentials)


def require_role(*allowed_roles: str):
    """Return a FastAPI dependency that enforces role-based access control.

    Usage:
        @router.put("/admin-only")
        def admin_action(user: dict = Depends(require_role("admin"))):
            ...

        @router.put("/staff-or-above")
        def staff_action(user: dict = Depends(require_role("admin", "field_officer", "district_admin"))):
            ...
    """
    def _role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.get('role')}' is not authorized. Required: {', '.join(allowed_roles)}",
            )
        return user
    return _role_checker
