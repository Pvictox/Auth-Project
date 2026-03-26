# app/redis_cache.py
from collections.abc import Callable
import functools
import json

from fastapi import Request
from pydantic import BaseModel

from app.log_config.logging_config import get_logger
from app.redis_config import RedisConfig

logger = get_logger(__name__)


def _serialize(data) -> str:
    """Converte o resultado para string JSON, suportando Pydantic e listas de Pydantic."""
    if isinstance(data, BaseModel):
        return data.model_dump_json()
    if isinstance(data, list) and all(isinstance(i, BaseModel) for i in data):
        return json.dumps([i.model_dump() for i in data])
    return json.dumps(data)


def redis_cache(ttl: int = 300, key_prefix: str = ""):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            redis = RedisConfig.get_instance()

            prefix = key_prefix or func.__name__
            key_params = ":".join(
                str(v) for v in kwargs.values() if not isinstance(v, Request)
            )
            cache_key = f"{prefix}:{key_params}" if key_params else prefix

            try:
                cached = redis.get(cache_key)
                if cached:
                    logger.info("Cache HIT → %s", cache_key)
                    return json.loads(cached)  # type: ignore
            except Exception as e:
                logger.warning("Erro ao ler cache (%s): %s", cache_key, e)

            result = await func(*args, **kwargs)

            try:
                redis.setex(cache_key, ttl, _serialize(result))
                logger.info("Cache SET → %s | TTL: %d}s", cache_key, ttl)
            except Exception as e:
                logger.warning("Erro ao salvar cache (%s): %s", cache_key, e)

            return result

        return wrapper

    return decorator


def redis_invalidate(*patterns: str):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            redis = RedisConfig.get_instance()

            for pattern in patterns:
                try:
                    # scan_iter busca as chaves que batem com o padrão
                    keys = list(redis.scan_iter(match=pattern))
                    if keys:
                        redis.delete(*keys)
                        logger.info(
                            "Cache INVALIDADO → %d chave(s) com padrão '%s'",
                            len(keys),
                            pattern,
                        )
                    else:
                        logger.info(
                            "Nenhuma chave encontrada para o padrão '%s'",
                            pattern,
                        )
                except Exception as e:
                    logger.warning(
                        "Erro ao invalidar cache (padrão: %s): %s", pattern, e
                    )

            return result

        return wrapper

    return decorator
