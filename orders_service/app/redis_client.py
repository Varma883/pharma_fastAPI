# app/redis_client.py
import redis
from functools import lru_cache


@lru_cache
def get_redis():
    """
    Return a shared Redis client instance.
    Locally we use localhost:6379.
    In Docker, we'll later switch to the redis container name.
    """
    return redis.Redis(
        host="redis",  # Use "redis" in Docker, "localhost" locally
        port=6379,
        db=0,
        decode_responses=True,  # so values are str, not bytes
    )
