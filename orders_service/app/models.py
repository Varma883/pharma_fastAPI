from sqlalchemy import Column, Integer, String, JSON
from app.db import Base

class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)  # who placed the order
    status = Column(String, default="CONFIRMED")
    items = Column(JSON)  # store list of items as JSON
