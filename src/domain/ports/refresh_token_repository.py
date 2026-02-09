from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def find_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        pass

    @abstractmethod
    async def find_active_by_user(self, user_id: UUID) -> List[RefreshToken]:
        pass

    @abstractmethod
    async def save(self, token: RefreshToken) -> RefreshToken:
        pass

    @abstractmethod
    async def revoke(self, token_id: UUID) -> None:
        pass
