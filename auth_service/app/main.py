from fastapi import FastAPI
from app.db import Base, engine
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router

app = FastAPI(title="Auth Service")


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


# Mount routers
app.include_router(auth_router, prefix="/auth")
app.include_router(users_router, prefix="/auth")
