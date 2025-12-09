from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path

security = HTTPBearer()

# ---------------------------------------------------------
# Load RSA PUBLIC KEY
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_KEY_PATH = BASE_DIR / "keys" / "public.pem"

if not PUBLIC_KEY_PATH.exists():
    raise RuntimeError(f"PUBLIC KEY not found at: {PUBLIC_KEY_PATH}")

with open(PUBLIC_KEY_PATH, "r") as f:
    PUBLIC_KEY = f.read()


def verify_jwt(credentials: HTTPAuthorizationCredentials | str = Depends(security)):
    """
    Can be used in TWO ways:

    1) As a FastAPI dependency:
       user = Depends(verify_jwt)
       -> credentials is HTTPAuthorizationCredentials

    2) Called manually (e.g. from gateway) with a raw header string:
       payload = verify_jwt("Bearer <token>")

    Returns:
        Decoded payload + original token under key 'token'
    """
    # ----- Case 1: called manually from gateway with a string -----
    if isinstance(credentials, str):
        if not credentials.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid Authorization header")
        token = credentials.split(" ", 1)[1]

    # ----- Case 2: used as FastAPI dependency -----
    else:
        token = credentials.credentials

    # Decode JWT
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Attach the original token so downstream services can forward it
    payload = dict(payload)
    payload["token"] = token
    return payload
