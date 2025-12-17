# app/main.py
from fastapi import FastAPI
from app.db import Base, engine
from app.routers.inventory import router
import logging
from app.redis_client import get_redis
from app.observability.metrics import metrics_middleware, metrics_endpoint
from app.observability.logging import setup_logging

setup_logging()



app = FastAPI(title="Inventory Service")
app.middleware("http")(metrics_middleware("inventory_service"))
logger = logging.getLogger("uvicorn")

@app.on_event("startup")
async def startup():
    logger.info("INVENTORY SERVICE — creating tables...")
    Base.metadata.create_all(bind=engine)
    try:
        # warm up redis connection
        r = await get_redis()
        await r.ping()
        logger.info("Redis OK")
    except Exception as exc:
        logger.warning("Redis not available at startup: %s", exc)
    logger.info("INVENTORY SERVICE — ready")


app.include_router(router)

@app.get("/")
def root():
    return {"service": "inventory", "status": "running"}

@app.get("/health")
def health():
    return {"service": "inventory", "status": "ok"}

@app.get("/metrics")
def metrics():
    return metrics_endpoint()
