from fastapi import APIRouter, Depends, HTTPException
from app.jwt_utils import get_current_user
from app.models import UserInDB, fake_db

router = APIRouter(tags=["Users"])


# ============================================
# GET CURRENT USER (/users/me)
# ============================================
@router.get("/users/me")
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "role": current_user.role,
    }


# ============================================
# GET ALL USERS (/users) - ADMIN ONLY
# ============================================
@router.get("/users")
def get_all_users(current_user: UserInDB = Depends(get_current_user)):

    # Admin authentication (required)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view all users")

    # Convert all UserInDB objects to public User schema
    users = []
    for user in fake_db.values():
        users.append({
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "role": user.role
        })

    return users
