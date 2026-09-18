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
from app.database import get_db

def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


APP_ENV = os.getenv("APP_ENV", "demo").strip().lower()
IS_PRODUCTION = APP_ENV in {"prod", "production"}
ENABLE_DEMO_USERS = _env_bool("ENABLE_DEMO_USERS", default=not IS_PRODUCTION)

# main.py fails closed before importing auth in production when this is absent.
JWT_SECRET = os.getenv("JWT_SECRET", "geoshield-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
try:
    JWT_EXPIRY_HOURS = max(1, min(int(os.getenv("JWT_EXPIRY_HOURS", "24")), 168))
except ValueError:
    JWT_EXPIRY_HOURS = 24


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# Backward-compatible private aliases used by existing code/tests.
_hash_password = hash_password
_verify_password = verify_password

security = HTTPBearer(auto_error=False)

def _build_user_store() -> dict:
    """Build local demo users plus an optional secret-managed production admin."""
    users = {}

    if ENABLE_DEMO_USERS:
        users.update({
            "admin@geoshield.gov.in": {"password_hash": _hash_password("admin123"), "name": "Admin", "role": "admin"},
            "field@geoshield.gov.in": {"password_hash": _hash_password("field123"), "name": "Field Officer", "role": "field_officer"},
            "district@geoshield.gov.in": {"password_hash": _hash_password("district123"), "name": "District Admin", "role": "district_admin"},
            "citizen@geoshield.gov.in": {"password_hash": _hash_password("demo123"), "name": "Citizen", "role": "citizen"},
        })

    admin_email = os.getenv("GEOSHIELD_ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("GEOSHIELD_ADMIN_PASSWORD", "")
    if admin_email or admin_password:
        if not admin_email or not admin_password:
            raise RuntimeError(
                "GEOSHIELD_ADMIN_EMAIL and GEOSHIELD_ADMIN_PASSWORD must be set together."
            )
        if IS_PRODUCTION and len(admin_password) < 12:
            raise RuntimeError(
                "GEOSHIELD_ADMIN_PASSWORD must be at least 12 characters in production."
            )
        users[admin_email] = {
            "password_hash": _hash_password(admin_password),
            "name": os.getenv("GEOSHIELD_ADMIN_NAME", "GeoShield Admin").strip() or "GeoShield Admin",
            "role": "admin",
        }

    return users


AUTH_USERS = _build_user_store()


def authenticate_user(email: str, password: str, db=None) -> dict | None:
    """Authenticate a persistent database user first, then configured bootstrap/demo users."""
    normalized_email = email.strip().lower()

    if db is not None:
        from app.models import UserAccount

        account = (
            db.query(UserAccount)
            .filter(UserAccount.email == normalized_email)
            .first()
        )
        if account is not None:
            if not account.is_active or not verify_password(password, account.password_hash):
                return None

            account.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            return {
                "email": account.email,
                "name": account.name,
                "role": account.role,
            }

    user = AUTH_USERS.get(normalized_email)
    if user and verify_password(password, user["password_hash"]):
        return {
            "email": normalized_email,
            "name": user["name"],
            "role": user["role"],
        }
    return None


def ensure_bootstrap_admin(db) -> None:
    """Persist the configured production/bootstrap administrator if one is supplied."""
    admin_email = os.getenv("GEOSHIELD_ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("GEOSHIELD_ADMIN_PASSWORD", "")
    if not admin_email or not admin_password:
        return

    from app.models import UserAccount

    account = db.query(UserAccount).filter(UserAccount.email == admin_email).first()
    if account is None:
        db.add(
            UserAccount(
                email=admin_email,
                name=os.getenv("GEOSHIELD_ADMIN_NAME", "GeoShield Admin").strip()
                or "GeoShield Admin",
                password_hash=hash_password(admin_password),
                role="admin",
                is_active=True,
            )
        )
        db.commit()


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
    db=Depends(get_db),
) -> dict:
    """Verify the JWT and reconcile it with the persistent account state.

    Persistent users are checked on every authenticated request so disabling an
    account or changing its role takes effect immediately instead of waiting for
    an already-issued JWT to expire. Production also fails closed when a token
    references an account that no longer exists.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    normalized_email = str(payload.get("sub") or "").strip().lower()
    if not normalized_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    from app.models import UserAccount

    account = (
        db.query(UserAccount)
        .filter(UserAccount.email == normalized_email)
        .first()
    )
    if account is not None:
        if not account.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled",
            )
        # Use current database identity/role so privilege changes are immediate.
        payload["sub"] = account.email
        payload["name"] = account.name
        payload["role"] = account.role
        return payload

    if IS_PRODUCTION and not ENABLE_DEMO_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account no longer exists",
        )

    return payload


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
