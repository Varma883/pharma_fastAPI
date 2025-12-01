from fastapi import FastAPI
from app.db import Base, engine
from app.routers.drugs import router as drugs_router

app = FastAPI(title="Catalog Service")


@app.on_event("startup")
def startup():
    print("📌 CATALOG SERVICE — Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ CATALOG SERVICE — Tables ready!")


@app.get("/health")
def health():
    return {"service": "catalog", "status": "ok"}


@app.get("/")
def root():
    return {"service": "catalog", "status": "running"}


app.include_router(drugs_router, prefix="/drugs")
