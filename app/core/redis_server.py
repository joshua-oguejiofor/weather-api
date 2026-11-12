import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL, 
    decode_responses=True,
    socket_timeout=5.0,  # Set a timeout for socket operations
    socket_connect_timeout=5.0,  # Set a timeout for socket connections
    retry_on_timeout=True,  # Retry on timeout
    health_check_interval=30,  # Perform health checks every 30 seconds
    max_connections=20,  # Limits pool size per worker process
)


async def get_redis():
    return redis_client


async def get_cache(key: str):
    return await redis_client.get(key)


async def set_cache(key: str, value: str, expire: int= 300):
    await redis_client.setex(key, expire, value)


async def delete_cache(key: str):
    await redis_client.delete(key)


async def increment_cache(key: str, expire: int= 900):
    value= await redis_client.incr(key)
    await redis_client.expire(key, expire)
    return value


async def invalidate_token(token: str, expire: int= 86400):
    await redis_client.setex(f"blacklist:{token}", expire, "1")


async def is_token_blacklisted(token: str) -> bool:
    return bool(await redis_client.get(f"blacklist:{token}"))

