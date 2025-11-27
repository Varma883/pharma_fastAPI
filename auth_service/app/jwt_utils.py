from datetime import datetime, timedelta
from jose import jwt, JWTError
import os

from fastapi import Header, HTTPException, status

from app.models import UserInDB, fake_db

# ============================================================
# Load RSA Keys
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_DIR = os.path.join(BASE_DIR, "keys")

PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "private.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "public.pem")

with open(PRIVATE_KEY_PATH, "r") as f:
    PRIVATE_KEY = f.read()

with open(PUBLIC_KEY_PATH, "r") as f:
    PUBLIC_KEY = f.read()

ALGO = "RS256"


# ============================================================
# Token Creation
# ============================================================

def create_access_token(data: dict, expires: int = 15):
    """Create short-lived access token."""
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=expires)
    return jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGO)


def create_refresh_token(data: dict):
    """Create long-lived refresh token."""
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGO)


# ============================================================
# Token Verification
# ============================================================

def get_current_user(authorization: str = Header(None)) -> UserInDB:
    """Verify JWT Access Token and return logged-in user.

    This dependency extracts the Authorization header, supports `Bearer <token>` format,
    decodes the token using the public key, and returns the user from the fake DB.
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGO])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = fake_db.get(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user