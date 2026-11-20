import redis.asyncio as aioredis
from app.core.config import settings

# Global async Redis connection pool to prevent connection exhaustion
redis_pool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=50,
    decode_responses=False,
)


def get_async_redis_client() -> aioredis.Redis:
    """Returns an async Redis client backed by the shared connection pool."""
    return aioredis.Redis(connection_pool=redis_pool)
