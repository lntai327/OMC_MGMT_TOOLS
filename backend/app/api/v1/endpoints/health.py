import time
from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import db_manager
from app.core.redis_client import get_async_redis_client

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get("")
async def health_check():
    health = {
        "status": "healthy",
        "timestamp": time.time(),
        "database": "unknown",
        "redis": "unknown",
        "db_latency_ms": None,
        "redis_latency_ms": None,
    }

    # Test Database (Non-blocking async)
    try:
        t0 = time.time()
        async with db_manager.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health["db_latency_ms"] = round((time.time() - t0) * 1000, 2)
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Test Redis (Non-blocking async using shared connection pool)
    try:
        t0 = time.time()
        redis_client = get_async_redis_client()
        pong = await redis_client.ping()
        if pong:
            health["redis_latency_ms"] = round((time.time() - t0) * 1000, 2)
            health["redis"] = "connected"
        else:
            health["redis"] = "unresponsive"
            health["status"] = "degraded"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health


