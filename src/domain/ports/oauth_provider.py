from abc import ABC, abstractmethod
from typing import Dict
from domain.entities.user import User

class IOAuthProvider(ABC):
    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        pass

    @abstractmethod
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict:
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> User:
        pass
