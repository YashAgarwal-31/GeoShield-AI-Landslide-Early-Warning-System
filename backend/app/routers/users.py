"""Persistent user administration for GeoShield."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, hash_password, require_role
from app.database import get_db
from app.models import UserAccount
from app.schemas import UserCreateRequest, UserPasswordRequest, UserStatusRequest


router = APIRouter(prefix="/api/users", tags=["users"])


def _serialize(account: UserAccount) -> dict:
    return {
        "id": account.id,
        "email": account.email,
        "name": account.name,
        "role": account.role,
        "is_active": account.is_active,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        "last_login_at": account.last_login_at.isoformat() if account.last_login_at else None,
    }


@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    return user


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    accounts = db.query(UserAccount).order_by(UserAccount.email).all()
    return [_serialize(account) for account in accounts]


@router.post("", status_code=201)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    email = payload.email.strip().lower()
    if db.query(UserAccount).filter(UserAccount.email == email).first():
        raise HTTPException(status_code=409, detail="User already exists")

    account = UserAccount(
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return _serialize(account)


@router.put("/{user_id}/status")
def set_user_status(
    user_id: int,
    payload: UserStatusRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    account = db.query(UserAccount).filter(UserAccount.id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="User not found")

    if account.email == user.get("sub") and not payload.is_active:
        raise HTTPException(status_code=400, detail="An administrator cannot disable their own active session account")

    account.is_active = payload.is_active
    db.commit()
    db.refresh(account)
    return _serialize(account)


@router.put("/{user_id}/password")
def reset_user_password(
    user_id: int,
    payload: UserPasswordRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    account = db.query(UserAccount).filter(UserAccount.id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="User not found")

    account.password_hash = hash_password(payload.password)
    account.token_version = int(account.token_version or 0) + 1
    db.commit()
    return {
        "status": "success",
        "id": account.id,
        "sessions_revoked": True,
    }
