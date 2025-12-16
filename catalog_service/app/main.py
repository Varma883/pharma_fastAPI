from fastapi import FastAPI
from app.db import Base, engine
from app.routers.drugs import router as drugs_router
import logging
import socket

app = FastAPI(title="Catalog Service")


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


app.include_router(drugs_router, prefix="/drugs")
