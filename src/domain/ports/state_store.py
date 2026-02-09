from abc import ABC, abstractmethod


class IStateStore(ABC):
    """Almacén temporal para state OAuth (protección CSRF)."""

    @abstractmethod
    def set(self, state: str, ttl_seconds: int = 600) -> None:
        """Guarda el state; expira tras ttl_seconds."""
        pass

    @abstractmethod
    def consume(self, state: str) -> bool:
        """Devuelve True si el state existía y lo elimina; False si no existe o ya expiró."""
        pass

    @abstractmethod
    def generate_and_store(self, ttl_seconds: int = 600) -> str:
        """Genera un state seguro, lo guarda con TTL y lo devuelve."""
        pass
