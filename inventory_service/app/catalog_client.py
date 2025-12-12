import os
import httpx
import redis.asyncio as redis
import json
import time
import logging

logger = logging.getLogger("uvicorn")

CATALOG_URL = os.getenv("CATALOG_INTERNAL_URL", "http://catalog_service:9002")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


# ---------------------------
# Circuit Breaker Implementation
# ---------------------------
class CircuitBreakerOpen(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    async def call(self, func, *args, **kwargs):
        # check open state
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit Breaker transitioned to HALF-OPEN/CLOSED")
            else:
                raise CircuitBreakerOpen("Circuit breaker open")

        try:
            result = await func(*args, **kwargs)
            # If the call was successful (no exception raised), we reset
            self._success()
            return result
        except Exception as e:
            self._failure()
            raise e

    def _success(self):
        if self.failure_count > 0:
            self.failure_count = 0
            self.state = "CLOSED"
            logger.info("Circuit Breaker reset validation failures")

    def _failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(f"Circuit Breaker failure count: {self.failure_count}")
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error("Circuit Breaker OPENED")


# Global Circuit Breaker Instance
catalog_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)


# ---------------------------
# Cache helpers
# ---------------------------
def _cache_key(product_id: int) -> str:
    return f"catalog:product:{product_id}"


async def cache_product(product_id: int, data: dict):
    await redis_client.set(_cache_key(product_id), json.dumps(data), ex=300)


async def get_cached_product(product_id: int):
    raw = await redis_client.get(_cache_key(product_id))
    if raw:
        return json.loads(raw)
    return None


# ---------------------------
# MAIN catalog validator
# ---------------------------
async def _fetch_from_catalog(product_id: int, token: str, override_url: str = None) -> dict:
    """
    Internal function to make the HTTP request.
    This is wrapped by the circuit breaker.
    """
    base_url = override_url if override_url else CATALOG_URL
    url = f"{base_url}/drugs/{product_id}"
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    async with httpx.AsyncClient() as client:
        # If connection fails or 5xx, httpx raises generic errors or we can raise custom ones.
        # We'll rely on httpx exceptions (ConnectError, TimeoutException) to trigger the breaker failure.
        resp = await client.get(url, headers=headers, timeout=2)
        
        if resp.status_code == 404:
            return None
            
        resp.raise_for_status()  # This will raise HTTPStatusError for 4xx/5xx
        return resp.json()


async def get_product(product_id: int, token: str = None, simulate_failure_url: str = None) -> dict | None:
    """
    Fetch product from Catalog service with fallback to Redis cache.
    Uses Circuit Breaker for the HTTP call.
    """
    try:
        # Wrap the HTTP call with Circuit Breaker
        # Note: If simulate_failure_url is passed, we use that to force a connection error
        data = await catalog_breaker.call(_fetch_from_catalog, product_id, token, simulate_failure_url)
        
        # If success, verify and cache
        if data:
            await cache_product(product_id, data)
            return data
            
    except CircuitBreakerOpen:
        # If CB is open, just re-raise so the caller knows, OR return None/Fallback?
        # User requirement: "6th hit should show error msg"
        # We will let this exception bubble up or catch specific ones in the router.
        # For get_product usage, we might want fallback even if CB is open?
        # But for STOCK VALIDATION, we definitely want to fail if we can't verify.
        logger.error("Circuit breaker is OPEN. Fast failing.")
        raise
        
    except Exception as e:
        logger.error(f"Catalog fetch failed: {e}")
        # Try fallback to cache
        cached = await get_cached_product(product_id)
        if cached:
            return cached
            
        # If no cache and no live service
        # raise or return None based on requirement?
        # If we just raise, the caller handles it.
        # For the test endpoint, we want to see the exception.
        raise e

    return None
