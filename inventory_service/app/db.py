from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()  # <--- IMPORTANT

DATABASE_URL = os.getenv("INVENTORY_DATABASE_URL")

if not DATABASE_URL:
    raise Exception("INVENTORY_DATABASE_URL is not set in .env")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
