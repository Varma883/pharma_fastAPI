from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.jwt_utils import verify_access_token

router = APIRouter(tags=["Users"])
security = HTTPBearer()

def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_access_token(token)
    if not payload:
         raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


# ===========================================================
# GET CURRENT USER (requires valid JWT)
# ===========================================================
@router.get("/users/me")
def read_users_me(
    payload: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Uses JWT token to identify user.
    """
    username = payload.get("sub")

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")

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
    payload: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """
    Only SUPERADMIN can fetch full user list.
    """
    role = payload.get("role")

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
