from fastapi import FastAPI
from app.db import Base, engine
from app.routers.orders import router as orders_router
import socket
from app.observability.metrics import metrics_middleware, metrics_endpoint
from app.observability.logging import setup_logging

setup_logging()

app = FastAPI(title="Orders Service")
app.middleware("http")(metrics_middleware("orders_service"))


@app.on_event("startup")
def startup():
    print("📌 ORDERS SERVICE — Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ ORDERS SERVICE — Tables ready!")


@app.get("/health")
def health():
    return {"service": "orders", "status": "ok"}


@app.get("/")
def root():
    return {
        "service": "orders",
        "hostname": socket.gethostname(),
        "status": "running"
    }

@app.get("/metrics")
def metrics():
    return metrics_endpoint()


app.include_router(orders_router, prefix="/orders")
