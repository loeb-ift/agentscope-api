from app.core.config import settings
import redis.asyncio as aioredis

# 创建异步Redis客户端
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    encoding="utf-8",
    max_connections=100
)