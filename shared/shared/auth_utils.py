from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path

security = HTTPBearer()

# ---------------------------------------------------------
# Load RSA PUBLIC KEY (works after Poetry install)
# ---------------------------------------------------------
# __file__ => <venv>/Lib/site-packages/shared/auth_utils.py
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_KEY_PATH = BASE_DIR / "keys" / "public.pem"

if not PUBLIC_KEY_PATH.exists():
    raise RuntimeError(f"PUBLIC KEY not found at: {PUBLIC_KEY_PATH}")

with open(PUBLIC_KEY_PATH, "r") as f:
    PUBLIC_KEY = f.read()


# ---------------------------------------------------------
# JWT Verifier
# ---------------------------------------------------------
def verify_jwt(credentials: HTTPAuthorizationCredentials | str = Depends(security)):

    if isinstance(credentials, str):
        if not credentials.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid Authorization header")
        token = credentials.split(" ", 1)[1]
    else:
        token = credentials.credentials

    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

