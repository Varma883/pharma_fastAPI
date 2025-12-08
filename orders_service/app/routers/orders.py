from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.auth_utils import verify_jwt
from app.db import get_db
from app.models import OrderModel
from app.schemas import Order, OrderCreate
from app.services.inventory_client import reserve_items

router = APIRouter()

# ===========================================================
# CREATE ORDER — supports BOTH /orders and /orders/
# ===========================================================
@router.post("", response_model=Order)
@router.post("/", response_model=Order)
async def create_order(
    payload: OrderCreate,
    user=Depends(verify_jwt),
    db: Session = Depends(get_db)
):
    # Step 1 – Reserve inventory
    order_items = [item.model_dump() for item in payload.items]

    # 🔥 Pass token to inventory service
    token = user["token"]  # ensure verify_jwt returns "token"

    reserve_result = await reserve_items(order_items, token)

    if reserve_result.get("status") != "reserved":
        raise HTTPException(status_code=400, detail="Inventory reservation failed")

    # Step 2 – Create order
    username = user["sub"]

    order = OrderModel(
        username=username,
        items=order_items,
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

    if user["role"] in ["admin", "superadmin"]:
        result = db.query(OrderModel).all()
    else:
        result = db.query(OrderModel).filter(OrderModel.username == username).all()

    return result
