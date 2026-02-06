from abc import ABC, abstractmethod
from typing import Dict, Any
from uuid import UUID

class ITokenService(ABC):
    @abstractmethod
    def create_access_token(self, user_id: UUID, claims: Dict[str, Any] = None) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, user_id: UUID) -> str:
        pass
