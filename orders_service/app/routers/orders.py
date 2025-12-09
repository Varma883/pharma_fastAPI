from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.auth_utils import verify_jwt
from app.db import get_db
from app.models import OrderModel
from app.schemas import Order, OrderCreate
from app.services.inventory_client import safe_reserve
import requests

router = APIRouter()


@router.post("", response_model=Order)
@router.post("/", response_model=Order)
def create_order(
    payload: OrderCreate,
    user=Depends(verify_jwt),
    db: Session = Depends(get_db)
):
    # 1) Prepare items
    order_items = [item.model_dump() for item in payload.items]

    # 2) Extract raw token (we put this into payload["token"] in shared/auth_utils)
    token = user.get("token")

    # 3) Reserve inventory with circuit breaker + Redis fallback
    try:
        reserve_result = safe_reserve(order_items, token)
    except requests.RequestException:
        # Inventory is DOWN but breaker not yet open -> transient network failure
        raise HTTPException(
            status_code=503,
            detail="Inventory service unavailable, please try again later."
        )

    status = "CONFIRMED"

    if reserve_result.get("status") == "reserved":
        status = "CONFIRMED"

    elif reserve_result.get("status") == "reserved_from_cache":
        # Inventory is down, but cached info says it's fine.
        # Mark order differently so ops can review or reconcile later.
        status = "PENDING_RESERVE"

    else:
        # Any other status means failure or unsafe fallback.
        raise HTTPException(
            status_code=400,
            detail=f"Inventory reservation failed: {reserve_result}"
        )

    # 4) Create order in DB
    username = user["sub"]

    order = OrderModel(
        username=username,
        items=order_items,
        status=status,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


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
