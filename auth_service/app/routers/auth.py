from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi import Request
from app.jwt_utils import create_access_token, create_refresh_token
from app.hashing import verify_password, hash_password
from app.db import get_db
from app.models import User
from app.schemas import UserRegister

router = APIRouter(tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Register a new user.
    - First user can be superadmin without any header.
    - After that, only SUPERADMIN can create another SUPERADMIN.
    """

    user_count = db.query(User).count()

    # If trying to create a superadmin:
    if payload.role == "superadmin":
        if user_count > 0:  # only enforce for non-first user
            role = request.headers.get("x-role")
            if role != "superadmin":
                raise HTTPException(
                    status_code=403,
                    detail="Only superadmin can create another superadmin."
                )

    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed = hash_password(payload.password)

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hashed,
        role=payload.role or "user",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "username": user.username,
        "role": user.role,
    }



@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    REAL login: read from Postgres, verify password, issue JWT.
    """

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    # Include role in token
    claims = {"sub": user.username, "role": user.role}

    access = create_access_token(claims)
    refresh = create_refresh_token(claims)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }



@router.get("/users")
def list_users(request: Request, db: Session = Depends(get_db)):
    """
    Only SUPERADMIN can list all users.
    Role is passed from Gateway as header: x-role
    """

    role = request.headers.get("x-role")  # injected by gateway

    if role != "superadmin":
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: requires superadmin role"
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