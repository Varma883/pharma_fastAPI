from fastapi import FastAPI
from app.db import Base, engine
from app.routers.inventory import router

app = FastAPI(title="Inventory Service")

# Auto create tables
Base.metadata.create_all(bind=engine)

app.include_router(router)

@app.get("/")
def root():
    return {"service": "inventory", "status": "running"}
