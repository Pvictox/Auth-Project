from redis import Redis

from app.redis_config import RedisConfig


def get_redis() -> Redis:
    return RedisConfig.get_instance()
