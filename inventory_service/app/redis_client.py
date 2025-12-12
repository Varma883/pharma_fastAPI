import os
import redis.asyncio as redis
import json


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client
