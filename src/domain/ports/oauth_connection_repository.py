from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from domain.entities.oauth_connection import OAuthConnection, OAuthProvider


class OAuthConnectionRepository(ABC):

    @abstractmethod
    async def find_by_user_and_provider(
        self,
        user_id: UUID,
        provider: OAuthProvider
    ) -> Optional[OAuthConnection]:
        pass

    @abstractmethod
    async def find_by_provider_user_id(
        self,
        provider: OAuthProvider,
        provider_user_id: str
    ) -> Optional[OAuthConnection]:
        pass

    @abstractmethod
    async def find_all_by_user(
        self,
        user_id: UUID
    ) -> List[OAuthConnection]:
        pass

    @abstractmethod
    async def save(self, connection: OAuthConnection) -> OAuthConnection:
        pass

    @abstractmethod
    async def delete(self, connection_id: UUID) -> bool:
        pass