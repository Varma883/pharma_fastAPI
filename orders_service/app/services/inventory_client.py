# app/services/inventory_client.py
import requests
import pybreaker

from app.redis_client import get_redis

INVENTORY_BASE = "http://inventory_service:9004" 

# Circuit breaker for inventory calls
inventory_breaker = pybreaker.CircuitBreaker(
    fail_max=5,        # after 5 failures -> OPEN
    reset_timeout=30,  # after 30s -> HALF-OPEN
)


def _cache_key(product_id: int) -> str:
    return f"inventory:{product_id}"


def cache_inventory(product_id: int, quantity: int) -> None:
    r = get_redis()
    # Cache for 60 seconds (tune as needed)
    r.set(_cache_key(product_id), quantity, ex=60)


def get_cached_inventory(product_id: int) -> int | None:
    r = get_redis()
    val = r.get(_cache_key(product_id))
    return int(val) if val is not None else None


@inventory_breaker
def call_inventory_get(product_id: int, token: str | None = None) -> dict:
    """
    Calls GET /inventory/{product_id} on inventory service.
    Updates Redis cache on success.
    Wrapped by circuit breaker.
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        f"{INVENTORY_BASE}/inventory/{product_id}",
        headers=headers,
        timeout=2,
    )
    resp.raise_for_status()
    data = resp.json()

    # Expecting shape: {"product_id": ..., "quantity": ...}
    qty = data.get("quantity")
    if qty is not None:
        cache_inventory(product_id, qty)

    return data


@inventory_breaker
def call_inventory_reserve(items: list[dict], token: str | None = None) -> dict:
    """
    Calls POST /inventory/reserve on inventory service.
    Wrapped by circuit breaker.
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.post(
        f"{INVENTORY_BASE}/inventory/reserve",
        headers=headers,
        json={"items": items},
        timeout=2,
    )
    resp.raise_for_status()
    return resp.json()


def safe_reserve(items: list[dict], token: str | None = None) -> dict:
    """
    High-level API that Orders router uses.

    - If inventory is healthy -> calls reserve normally.
    - If breaker is OPEN -> uses Redis cache as fallback.
    """
    import pybreaker as _pyb
    try:
        # Try real reservation first (may raise breaker or requests errors)
        return call_inventory_reserve(items, token)

    except _pyb.CircuitBreakerError:
        # Breaker is OPEN -> inventory is considered DOWN.
        # Try Redis-based fallback.
        for item in items:
            pid = item["product_id"]
            needed = item["quantity"]
            cached_qty = get_cached_inventory(pid)
            if cached_qty is None or cached_qty < needed:
                # Fallback is not safe: not enough cached info.
                return {
                    "status": "fallback",
                    "reason": "inventory_down_no_cache",
                    "details": {
                        "product_id": pid,
                        "needed": needed,
                        "cached": cached_qty,
                    },
                }

        # All items have enough cached stock
        return {
            "status": "reserved_from_cache",
            "reason": "inventory_down_but_cache_sufficient",
        }
