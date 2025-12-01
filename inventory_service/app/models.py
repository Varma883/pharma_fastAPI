from sqlalchemy import Column, Integer
from app.db import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, unique=True, nullable=False)
    quantity = Column(Integer, nullable=False)
