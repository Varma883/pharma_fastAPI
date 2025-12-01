from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Inventory
from app.schemas import ReserveRequest, InventoryItem
from shared.auth_utils import verify_jwt  # ⬅️ JWT from shared

router = APIRouter(prefix="/inventory")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 



def require_admin(user=Depends(verify_jwt)):
    """
    Allow only users with role == 'admin'.
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user


@router.get("/{product_id}")
def check_inventory(
    product_id: int,
    db: Session = Depends(get_db),
    user=Depends(verify_jwt),  # ⬅️ any valid user
):
    item = db.query(Inventory).filter_by(product_id=product_id).first()
    if not item:
        raise HTTPException(404, "Product not found in inventory")
    return {"product_id": item.product_id, "quantity": item.quantity}


@router.post("/reserve")
def reserve_inventory(
    request: ReserveRequest,
    db: Session = Depends(get_db),
    user=Depends(verify_jwt),  # user placing an order
):
    for item in request.items:
        row = db.query(Inventory).filter_by(product_id=item.product_id).first()

        if not row or row.quantity < item.quantity:
            raise HTTPException(
                400, f"Not enough inventory for product {item.product_id}"
            )

        row.quantity -= item.quantity
        db.add(row)

    db.commit()
    return {"status": "reserved"}


@router.post("/admin/set-stock")
def set_stock(
    item: InventoryItem,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),  # ⬅️ admin-only
):
    row = db.query(Inventory).filter_by(product_id=item.product_id).first()

    if row:
        row.quantity = item.quantity
    else:
        row = Inventory(product_id=item.product_id, quantity=item.quantity)
        db.add(row)

    db.commit()
    db.refresh(row)

    return {
        "status": "ok",
        "item": {
            "product_id": row.product_id,
            "quantity": row.quantity,
        },
    }
