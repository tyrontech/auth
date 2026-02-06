from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict
from typing import Dict
from domain.entities.user import User

@dataclass
class ProviderUser:
    provider_id: str
    email: str
    name: str = ""
    picture: str = None
    email_verified: bool = False
    extra_data: dict = None

class IOAuthProvider(ABC):
    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        pass

    @abstractmethod
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict:
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> ProviderUser:
        pass
