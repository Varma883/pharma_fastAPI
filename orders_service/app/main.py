from fastapi import FastAPI
from app.routers.orders import router

app = FastAPI(title="Orders Service")


@app.get("/")
def root():
    return {"service": "orders", "status": "running"}


@app.get("/health")
def health():
    return {"service": "orders", "status": "ok"}


# all routes under /orders
app.include_router(router, prefix="/orders")
