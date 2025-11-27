from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.jwt_utils import create_access_token, create_refresh_token
from app.hashing import verify_password, hash_password
from app.models import fake_db, UserInDB, UserRegister

router = APIRouter(tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister):
    """
    Simple in-memory registration.
    In real life you'd write to a DB.
    """
    if payload.username in fake_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    hashed = hash_password(payload.password)

    new_user = UserInDB(
        id=len(fake_db) + 1,
        username=payload.username,
        full_name=payload.full_name,
        is_active=True,
        role=payload.role or "user",
        hashed_password=hashed,
    )

    fake_db[payload.username] = new_user

    return {
        "message": "User registered",
        "username": new_user.username,
        "role": new_user.role,
    }


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user: UserInDB | None = fake_db.get(form_data.username)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Include role in token
    claims = {"sub": user.username, "role": user.role}

    access = create_access_token(claims)
    refresh = create_refresh_token(claims)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }
