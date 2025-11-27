from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer
from app.routers import drugs

app = FastAPI(title="Catalog Service")

security = HTTPBearer()


@app.get("/")
def root():
    return {"service": "catalog", "status": "running"}


@app.get("/health")
def health():
    return {"service": "catalog", "status": "ok"}


app.include_router(drugs.router, prefix="/drugs", tags=["Drugs"])


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Catalog Service",
        version="1.0.0",
        routes=app.routes,
    )

    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault("securitySchemes", {})

    openapi_schema["components"]["securitySchemes"]["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    # secure all non-health endpoints
    for path, path_item in openapi_schema["paths"].items():
        if path in ["/", "/health"]:
            continue
        for method in path_item.values():
            method["security"] = [{"bearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

print("🔥 Catalog Service Loaded:", __file__)
