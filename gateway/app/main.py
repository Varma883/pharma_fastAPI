from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.routes.proxy import router as proxy_router

app = FastAPI(title="API Gateway")

@app.get("/")
def root():
    return {"service": "gateway", "status": "running"}

app.include_router(proxy_router)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title="API Gateway",
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

    PUBLIC = ["/auth/token"]

    for path, methods in schema["paths"].items():
        # exact match or paths that begin with the public path + '/'
        if any(path == p or path.startswith(p + "/") for p in PUBLIC):
            continue

        for method in methods.values():
            method.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

print("🔥 API Gateway Loaded:", __file__)
