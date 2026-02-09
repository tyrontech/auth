from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.entities.user_credentials import UserCredentials


class UserCredentialsRepository(ABC):
    @abstractmethod
    async def find_by_user_id(self, user_id: UUID) -> Optional[UserCredentials]:
        pass

    @abstractmethod
    async def save(self, credentials: UserCredentials) -> UserCredentials:
        pass
