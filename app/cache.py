
import logging

import redis

from app.config import settings

log = logging.getLogger(__name__)
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def chave_produto(produto_id: int) -> str:
    return f"produto:{produto_id}"


def get(chave: str) -> str | None:
    try:
        return redis_client.get(chave)
    except redis.RedisError:
        log.warning("Redis indisponível; lendo direto do banco") 
        return None


def set(chave: str, valor: str) -> None:
    try:
        redis_client.set(chave, valor, ex=settings.cache_ttl_segundos)
    except redis.RedisError:
        log.warning("Falha ao gravar no cache")


def invalidar(chave: str) -> None:
    try:
        redis_client.delete(chave)
    except redis.RedisError:
        log.warning("Falha ao invalidar cache; o TTL vai expirar a chave")
