from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
import httpx
from shared.auth_utils import verify_jwt

router = APIRouter()

# Configuration for downstream services
# 'prepend_service_name': If True, /service/path -> http://host/service/path
#                         If False, /service/path -> http://host/path
SERVICE_CONFIG = {
    "auth": {
        "url": "http://auth_service:9001",
        "prepend_service_name": True
    },
    "catalog": {
        "url": "http://catalog_service:9002",
        "prepend_service_name": False
    },
    "orders": {
        "url": "http://orders_service:9003",
        "prepend_service_name": True
    },
    "inventory": {
        "url": "http://inventory_service:9004",
        "prepend_service_name": True
    },
}

async def _proxy_request(service: str, path: str | None, request: Request):
    if service not in SERVICE_CONFIG:
        raise HTTPException(404, "Unknown service")

    service_conf = SERVICE_CONFIG[service]
    
    # -------- LOGIN + REGISTER ARE PUBLIC --------
    public_auth_paths = {"token", "login", "register", "docs", "openapi.json"} 
    # Added docs/openapi for convenience if needed, strictly keeping to request is fine too.
    # Original logic only checked first segment.
    
    path_segments = path.split("/") if path else []
    first_segment = path_segments[0] if path_segments else ""

    is_public_auth = (
        service == "auth"
        and first_segment in public_auth_paths
    )

    # -------- JWT VALIDATION FOR SECURED ROUTES --------
    auth_header = request.headers.get("authorization")
    injected_headers = {}

    if not is_public_auth and request.method != "OPTIONS":
        if not auth_header:
            raise HTTPException(401, "Missing Authorization header")

        payload = verify_jwt(auth_header)
        injected_headers = {
            "x-user-id": str(payload.get("sub")),
            "x-username": payload.get("username", str(payload.get("sub"))),
            "x-role": payload.get("role", "user"),
        }

    # ====================================================
    # DYNAMIC PATH CONSTRUCTION
    # ====================================================
    base_url = service_conf["url"].rstrip("/")
    clean_path = path.lstrip("/") if path else ""
    
    if service_conf["prepend_service_name"]:
        # e.g. /auth/login -> internal /auth/login
        target_path = f"{service}/{clean_path}"
    else:
        # e.g. /catalog/drugs -> internal /drugs
        target_path = clean_path

    # Fix potential double slashes if target_path is empty (rare but possible)
    target_path = target_path.strip("/")
    
    target_url = f"{base_url}/{target_path}"

    # Clean headers
    clean_headers = {k: v for k, v in request.headers.items()}
    # Headers to drop as per RFC or practical proxying
    hop_by_hop = {
        "host", "connection", "keep-alive", "proxy-authorization", 
        "proxy-authenticate", "upgrade", "te", "transfer-encoding"
    }
    for h in hop_by_hop:
        clean_headers.pop(h, None)
    
    clean_headers.update(injected_headers)

    # Stream the body
    body = await request.body()

    # We use a timeout? Default is fine for now.
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                content=body,
                headers=clean_headers,
                timeout=60.0 
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Service {service} unavailable: {str(exc)}")

    return Response(
        status_code=resp.status_code,
        content=resp.content,
        headers={
            k: v
            for k, v in resp.headers.items()
            if k.lower() not in hop_by_hop
        },
    )

@router.api_route(
    "/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_any(service: str, path: str, request: Request):
    return await _proxy_request(service, path, request)

@router.api_route(
    "/{service}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_root(service: str, request: Request):
    return await _proxy_request(service, "", request)
