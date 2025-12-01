from datetime import datetime, timedelta
from jose import jwt
import os

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
# Token Creation Only (Auth service does NOT verify tokens)
# ============================================================

def create_access_token(data: dict, expires_minutes: int = 15):
    """
    Create short-lived access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGO)
    return token


def create_refresh_token(data: dict, expires_days: int = 7):
    """
    Create long-lived refresh token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=expires_days)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGO)
    return token
