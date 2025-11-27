from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
import httpx
from shared.auth_utils import verify_jwt

router = APIRouter()

SERVICES = {
    "auth": "http://localhost:9001",
    "catalog": "http://localhost:9002",
    "orders": "http://localhost:9003",
}


async def _proxy_request(service: str, path: str | None, request: Request):

    if service not in SERVICES:
        raise HTTPException(404, "Unknown service")

    # ---- PUBLIC LOGIN ----
    is_auth_login = (service == "auth" and path in ["token", "token/"])

    auth_header = request.headers.get("authorization")
    injected_headers = {}

    if not is_auth_login:
        if not auth_header:
            raise HTTPException(401, "Missing Authorization header")

        payload = verify_jwt(auth_header)

        injected_headers = {
            "x-user-id": payload.get("sub"),
            "x-username": payload.get("username", payload.get("sub")),
            "x-role": payload.get("role", "user")
        }

    # ====================================================
    # CORRECT PATH GENERATION  (FIXED 🔥)
    # ====================================================
    if service == "auth":
        # /auth/token -> http://localhost:9001/auth/token
        target_path = f"auth/{path}" if path else "auth"

    else:
        # For catalog + orders:
        # /catalog/drugs -> /drugs
        # /orders/ -> /orders
        target_path = path if path else ""
    # ====================================================

    # Build URL
    target_url = f"{SERVICES[service].rstrip('/')}/{target_path.lstrip('/')}"
    if target_url.endswith("//"):
        target_url = target_url[:-1]

    # Clean headers
    clean_headers = {k: v for k, v in request.headers.items()}
    for h in ["host", "connection", "keep-alive", "proxy-authorization",
              "proxy-authenticate", "upgrade", "te"]:
        clean_headers.pop(h, None)

    if auth_header:
        clean_headers["authorization"] = auth_header

    clean_headers.update(injected_headers)

    body = await request.body()

    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=target_url,
            params=request.query_params,
            content=body,
            headers=clean_headers,
        )

    return Response(
        status_code=resp.status_code,
        content=resp.content,
        headers={k: v for k, v in resp.headers.items()
                 if k.lower() in ("content-type", "content-length")}
    )


# Routes
@router.api_route("/{service}/{path:path}",
                  methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_any(service: str, path: str, request: Request):
    return await _proxy_request(service, path, request)


@router.api_route("/{service}",
                  methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_root(service: str, request: Request):
    return await _proxy_request(service, path="", request=request)
