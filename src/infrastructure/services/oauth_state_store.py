"""
Servicio de almacén temporal para state OAuth (protección CSRF).
Implementación en memoria; en producción podría ser Redis u otro cache.
"""
import secrets
from datetime import datetime, timezone
from threading import Lock

from domain.ports.state_store import IStateStore


class InMemoryStateStore(IStateStore):
    """Almacén en memoria para state OAuth. TTL por entrada. No persistente."""

    def __init__(self) -> None:
        self._store: dict[str, datetime] = {}
        self._lock = Lock()

    def set(self, state: str, ttl_seconds: int = 600) -> None:
        expires_at = datetime.now(timezone.utc).timestamp() + ttl_seconds
        with self._lock:
            self._store[state] = datetime.fromtimestamp(expires_at, tz=timezone.utc)
            self._prune_locked()

    def consume(self, state: str) -> bool:
        with self._lock:
            self._prune_locked()
            if state not in self._store:
                return False
            del self._store[state]
            return True

    def generate_and_store(self, ttl_seconds: int = 600) -> str:
        state = secrets.token_urlsafe(32)
        self.set(state, ttl_seconds=ttl_seconds)
        return state

    def _prune_locked(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [k for k, v in self._store.items() if v <= now]
        for k in expired:
            del self._store[k]
