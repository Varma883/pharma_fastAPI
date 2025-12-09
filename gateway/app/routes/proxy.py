from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
import httpx
from shared.auth_utils import verify_jwt

router = APIRouter()

SERVICE_MAP = {
    "auth": "http://auth_service:9001",
    "catalog": "http://catalog_service:9002",
    "orders": "http://orders_service:9003",
    "inventory": "http://inventory_service:9004",
}


async def _proxy_request(service: str, path: str | None, request: Request):
    if service not in SERVICE_MAP:
        raise HTTPException(404, "Unknown service")

    # -------- LOGIN + REGISTER ARE PUBLIC --------
    public_auth_paths = {"token", "login", "register"}
    is_public_auth = (
        service == "auth"
        and path is not None
        and path.split("/")[0] in public_auth_paths
    )

    # -------- JWT VALIDATION FOR SECURED ROUTES --------
    auth_header = request.headers.get("authorization")
    injected_headers = {}

    if not is_public_auth:
        if not auth_header:
            raise HTTPException(401, "Missing Authorization header")

        payload = verify_jwt(auth_header)

        injected_headers = {
            "x-user-id": payload.get("sub"),
            "x-username": payload.get("username", payload.get("sub")),
            "x-role": payload.get("role", "user"),
        }

    # ====================================================
    # CORRECT PATH MAPPING
    # ====================================================
    if service == "auth":
        # /auth/login → http://auth_service:9001/auth/login
        target_path = f"auth/{path}".rstrip("/") if path else "auth"

    elif service == "inventory":
        # /inventory/reserve → http://inventory_service:9004/inventory/reserve
        target_path = f"inventory/{path}".rstrip("/") if path else "inventory"

    elif service == "orders":
        # /orders/ → http://orders_service:9003/orders/
        target_path = f"orders/{path}".rstrip("/") if path else "orders"

    elif service == "catalog":
        # /catalog/drugs → http://catalog_service:9002/drugs
        target_path = path.lstrip("/") if path else ""

    base = SERVICE_MAP[service].rstrip("/")
    target_url = f"{base}/{target_path}" if target_path else base

    # Clean headers
    clean_headers = {k: v for k, v in request.headers.items()}
    for h in [
        "host",
        "connection",
        "keep-alive",
        "proxy-authorization",
        "proxy-authenticate",
        "upgrade",
        "te",
    ]:
        clean_headers.pop(h, None)

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
        headers={
            k: v
            for k, v in resp.headers.items()
            if k.lower() in ("content-type", "content-length")
        },
    )


@router.api_route(
    "/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_any(service: str, path: str, request: Request):
    return await _proxy_request(service, path, request)


@router.api_route(
    "/{service}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_root(service: str, request: Request):
    return await _proxy_request(service, "", request)
