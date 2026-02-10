"""
State store OAuth (CSRF) backed by Redis. Use when running multiple workers.
Config (redis_url, key_prefix) comes from Settings via container.
"""
import secrets

import redis

from domain.ports.state_store import IStateStore


class RedisStateStore(IStateStore):
    """Almacén de state OAuth en Redis. TTL por clave; compartido entre workers."""

    def __init__(self, redis_url: str, key_prefix: str = "auth:oauth:state:") -> None:
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._key_prefix = key_prefix if key_prefix.endswith(":") else key_prefix + ":"

    def _key(self, state: str) -> str:
        return f"{self._key_prefix}{state}"

    def set(self, state: str, ttl_seconds: int = 600) -> None:
        key = self._key(state)
        self._client.setex(key, ttl_seconds, "1")

    def consume(self, state: str) -> bool:
        key = self._key(state)
        if self._client.get(key) is None:
            return False
        self._client.delete(key)
        return True

    def generate_and_store(self, ttl_seconds: int = 600) -> str:
        state = secrets.token_urlsafe(32)
        self.set(state, ttl_seconds=ttl_seconds)
        return state
