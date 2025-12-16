from fastapi import FastAPI
from app.db import Base, engine
from app.routers.orders import router as orders_router
import socket

app = FastAPI(title="Orders Service")


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


app.include_router(orders_router, prefix="/orders")
