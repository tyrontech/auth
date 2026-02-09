from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderUser:
    provider_id: str
    email: str
    name: str = ""
    picture: str | None = None
    email_verified: bool = False
    extra_data: dict[str, Any] | None = None


class IOAuthProvider(ABC):
    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        pass

    @abstractmethod
    def exchange_code_for_token(
        self, code: str, redirect_uri: str
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> ProviderUser:
        pass