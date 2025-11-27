from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router

app = FastAPI(title="Auth Service")


@app.get("/")
def root():
    return {"service": "auth", "status": "running"}


@app.get("/health")
def health():
    return {"service": "auth", "status": "ok"}


# Prefix all auth endpoints
app.include_router(auth_router, prefix="/auth")
app.include_router(users_router, prefix="/auth")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title="Auth Service",
        version="1.0.0",
        routes=app.routes,
    )

    schema.setdefault("components", {})
    schema["components"].setdefault("securitySchemes", {})

    schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    PUBLIC = ["/auth/token", "/auth/register", "/health", "/"]

    for path, methods in schema["paths"].items():
        if path in PUBLIC:
            continue
        for method in methods.values():
            method.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

print("🔥 AUTH SERVICE LOADED:", __file__)
