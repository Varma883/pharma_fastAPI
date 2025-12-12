from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Inventory
from app.schemas import ReserveRequest, InventoryItem
from shared.auth_utils import verify_jwt  # ⬅️ JWT from shared
from app.catalog_client import get_product, CircuitBreakerOpen  # ⬅️ Import client

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


@router.get("/test-circuit-breaker")
async def test_circuit_breaker(user=Depends(verify_jwt)):
    """
    Test endpoint to demonstrate Circuit Breaker.
    It forces a connection to a non-existent service to simulate failure.
    
    Expected behavior:
    1. First 5 calls: Fail with Connection Timeout/Error -> Returns 503 Service Unavailable
    2. 6th call onwards: Fail immediately -> Returns 503 Circuit breaker open
    """
    token = user.get("token")
    try:
        # 1. Force failure by using a bad URL
        await get_product(999, token=token, simulate_failure_url="http://localhost:11111")
        return {"status": "Unexpected success"}
    except CircuitBreakerOpen:
        # 2. Circuit is OPEN - Fail fast
        raise HTTPException(status_code=503, detail="Circuit breaker open")
    except Exception as e:
        # 3. Connection failed (Circuit CLOSED but failing)
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {str(e)}")


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
async def set_stock(
    item: InventoryItem,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),  # ⬅️ admin-only
):
    # 1. Validate against Catalog (or Cache)
    token = admin.get("token")
    try:
        product_data = await get_product(item.product_id, token=token)
        if not product_data:
            # Not found in catalog AND not in cache
            raise HTTPException(400, f"Product {item.product_id} does not exist in Catalog")
            
    except HTTPException:
        # Re-raise HTTP exceptions (like the 400 above) as-is
        raise
    except CircuitBreakerOpen:
        raise HTTPException(503, "Catalog service unavailable (Circuit Open)")
    except Exception as e:
        # Could not verify due to network/timeout
        # Requirement: Only set stock for products in database.
        # If we can't verify, we should probably block it to be safe, or allow if strictly cached?
        # Use safe approach: Block if we can't verify.
        raise HTTPException(503, f"Catalog Validation Failed: {str(e)}")

    # 2. Update stock
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
