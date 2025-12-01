from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User

router = APIRouter(tags=["Users"])


# ===========================================================
# GET CURRENT USER (requires gateway JWT)
# ===========================================================
@router.get("/users/me")
def read_users_me(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Uses headers injected by Gateway:
    x-username, x-role
    """

    username = request.headers.get("x-username")

    if not username:
        raise HTTPException(status_code=401, detail="Missing x-username header")

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "role": user.role,
    }


# ===========================================================
# GET ALL USERS — SUPERADMIN ONLY
# ===========================================================
@router.get("/users")
def list_all_users(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Only SUPERADMIN can fetch full user list.
    """

    role = request.headers.get("x-role")

    if role != "superadmin":
        raise HTTPException(
            status_code=403,
            detail="Only superadmin can view all users"
        )

    users = db.query(User).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active
        }
        for u in users
    ]
