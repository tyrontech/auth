from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID


class ITokenService(ABC):
    @abstractmethod
    def create_access_token(
        self, user_id: UUID, claims: Optional[Dict[str, Any]] = None
    ) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, user_id: UUID) -> str:
        pass

    @abstractmethod
    def validate_access_token(self, token: str) -> Optional[UUID]:
        """Devuelve user_id si el token es válido, None en caso contrario."""
        pass

    @abstractmethod
    def hash_refresh_token(self, token: str) -> str:
        """Hash del token para almacenar en BD (buscar/revocar)."""
        pass

    @abstractmethod
    def decode_refresh_token(
        self, token: str
    ) -> Optional[tuple[UUID, datetime]]:
        """Devuelve (user_id, expires_at) si el token es válido."""
        pass
