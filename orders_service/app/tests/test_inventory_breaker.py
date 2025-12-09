# tests/test_inventory_breaker.py
import requests
import pybreaker
from app.services import inventory_client


def test_circuit_breaker_opens(monkeypatch):
    """
    Simulate inventory being DOWN (requests always fail).
    After several attempts, breaker should OPEN and safe_reserve
    should return a fallback status instead of raising.
    """

    # Always fail post
    def failing_post(*args, **kwargs):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(inventory_client.requests, "post", failing_post)

    items = [{"product_id": 1, "quantity": 1}]

    # Call multiple times to trigger breaker
    for _ in range(6):
        try:
            inventory_client.safe_reserve(items, token=None)
        except requests.RequestException:
            # initial failures before breaker opens
            pass

    # Now breaker should be OPEN, safe_reserve should hit fallback path
    result = inventory_client.safe_reserve(items, token=None)
    assert result["status"] in ("fallback", "reserved_from_cache")
