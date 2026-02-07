from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import UUID
from jose import jwt

from domain.ports.token_service import ITokenService

class JWTTokenService(ITokenService):
    def __init__(self, secret_key: str, algorithm: str, access_expire_minutes: int, refresh_expire_minutes: int):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_expire_minutes = access_expire_minutes
        self.refresh_expire_minutes = refresh_expire_minutes

    def create_access_token(self, user_id: UUID, claims: Dict[str, Any] = None) -> str:
        to_encode = claims.copy() if claims else {}
        expire = datetime.utcnow() + timedelta(minutes=self.access_expire_minutes)
        to_encode.update({"exp": expire, "sub": str(user_id), "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: UUID) -> str:
        expire = datetime.utcnow() + timedelta(minutes=self.refresh_expire_minutes)
        to_encode = {"exp": expire, "sub": str(user_id), "type": "refresh"}
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
