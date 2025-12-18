from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from app.db import Base, engine
from app.routers.drugs import router as drugs_router
import logging
import socket
from app.observability.metrics import metrics_middleware, metrics_endpoint
from app.observability.logging import setup_logging

setup_logging()

app = FastAPI(title="Catalog Service")
app.middleware("http")(metrics_middleware("catalog_service"))


logger = logging.getLogger("uvicorn")

@app.on_event("startup")
def startup():
    logger.info("CATALOG SERVICE — Creating tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("CATALOG SERVICE — Tables ready!")



@app.get("/health")
def health():
    return {"service": "catalog", "status": "ok"}


@app.get("/")
def root():
    return {
        "service": "catalog", 
        "hostname": socket.gethostname(),
        "status": "running"
    }

@app.get("/metrics")
def metrics():
    return metrics_endpoint()


# Ensure uploads directory exists
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

app.include_router(drugs_router, prefix="/drugs")
