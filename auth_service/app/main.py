from fastapi import FastAPI
from app.db import Base, engine
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.observability.metrics import metrics_middleware, metrics_endpoint
from app.observability.logging import setup_logging

setup_logging()

app = FastAPI(title="Auth Service")

app.middleware("http")(metrics_middleware("auth"))


@app.on_event("startup")
def startup():
    print("📌 AUTH SERVICE — Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ AUTH SERVICE — Tables ready!")


@app.get("/health")
def health():
    return {"service": "auth", "status": "ok"}


@app.get("/")
def root():
    return {"service": "auth", "status": "running"}

@app.get("/metrics")
def metrics():
    return metrics_endpoint()




# Mount routers
app.include_router(auth_router, prefix="/auth")
app.include_router(users_router, prefix="/auth")
