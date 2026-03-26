import os

import redis

from app.log_config.logging_config import get_logger

logger = get_logger(__name__)


class RedisConfig:
    _instance: redis.Redis | None = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                logger.error("REDIS_URL environment variable is not set.")
                raise ValueError("REDIS_URL environment variable is not set.")
            cls._instance = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,  # Timeout for connection attempts
                retry_on_timeout=True,  # Enable retry on timeout
            )
            logger.info("Redis connection established successfully.")
        return cls._instance

    @classmethod
    def check_connection(cls) -> bool:
        try:
            client = cls.get_instance()
            client.ping()
            logger.info("Redis connection successful")
            return True
        except redis.ConnectionError as e:
            logger.error("Redis connection failed: %s", e)
            return False

    @classmethod
    def close(cls) -> None:
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
            logger.info("Redis connection closed")
