import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from authlib.jose import jwt

from domain.ports.token_service import ITokenService


def _ensure_str(token: bytes | str) -> str:
    return token.decode("utf-8") if isinstance(token, bytes) else token


class JWTTokenService(ITokenService):
    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        access_expire_minutes: int,
        refresh_expire_minutes: int,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_expire_minutes = access_expire_minutes
        self.refresh_expire_minutes = refresh_expire_minutes

    def create_access_token(
        self,
        user_id: UUID,
        claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_expire_minutes)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": expire,
            **(claims or {}),
        }
        header = {"alg": self.algorithm, "typ": "JWT"}
        token = jwt.encode(header, payload, self.secret_key)
        return _ensure_str(token)

    def create_refresh_token(self, user_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.refresh_expire_minutes)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expire,
        }
        header = {"alg": self.algorithm, "typ": "JWT"}
        token = jwt.encode(header, payload, self.secret_key)
        return _ensure_str(token)

    def validate_access_token(self, token: str) -> Optional[UUID]:
        try:
            payload = jwt.decode(token, self.secret_key)
            if payload.get("type") != "access":
                return None
            sub = payload.get("sub")
            return UUID(sub) if sub else None
        except Exception:
            return None

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def decode_refresh_token(
        self, token: str
    ) -> Optional[tuple[UUID, datetime]]:
        try:
            payload = jwt.decode(token, self.secret_key)
            if payload.get("type") != "refresh":
                return None
            sub = payload.get("sub")
            exp = payload.get("exp")
            if not sub or exp is None:
                return None
            expires_at = (
                datetime.fromtimestamp(exp, tz=timezone.utc)
                if isinstance(exp, (int, float))
                else exp
            )
            return UUID(sub), expires_at
        except Exception:
            return None
