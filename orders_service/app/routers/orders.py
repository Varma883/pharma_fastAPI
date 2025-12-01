from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.auth_utils import verify_jwt
from app.db import get_db
from app.models import OrderModel
from app.schemas import Order, OrderCreate

router = APIRouter()


# fake inventory check for now
def mock_inventory(items):
    return True


# ===========================================================
# CREATE ORDER — supports BOTH /orders and /orders/
# ===========================================================
@router.post("", response_model=Order)
@router.post("/", response_model=Order)
def create_order(
    payload: OrderCreate,
    user=Depends(verify_jwt),
    db: Session = Depends(get_db)
):
    if not mock_inventory(payload.items):
        raise HTTPException(400, "Inventory reservation failed")

    username = user["sub"]

    order = OrderModel(
        username=username,
        items=[item.model_dump() for item in payload.items],
        status="CONFIRMED"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


# ===========================================================
# LIST ORDERS — supports BOTH /orders and /orders/
# ===========================================================
@router.get("", response_model=list[Order])
@router.get("/", response_model=list[Order])
def list_orders(
    user=Depends(verify_jwt),
    db: Session = Depends(get_db)
):
    username = user["sub"]

    # normal users only see their orders
    # admin/superadmin see all
    if user["role"] in ["admin", "superadmin"]:
        result = db.query(OrderModel).all()
    else:
        result = db.query(OrderModel).filter(OrderModel.username == username).all()

    return result
