import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            try:
                cls._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                logger.info("Connected to Redis successfully.")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
        return cls._client

redis_client = RedisClient.get_client()
