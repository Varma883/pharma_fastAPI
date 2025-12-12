# app/main.py
from fastapi import FastAPI
from app.db import Base, engine
from app.routers.inventory import router
import logging
from app.redis_client import get_redis


app = FastAPI(title="Inventory Service")
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
