from sqlalchemy import Column, Integer, String
from app.db import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    ndc = Column(String, unique=True, index=True)
    form = Column(String)
    strength = Column(String)
