"""Use case: exchange a valid refresh token for new access + refresh tokens (rotation)."""

from datetime import datetime, timezone
from uuid import uuid4

from application.dtos.auth_response import AuthResponse, UserDTO
from application.exceptions import InvalidRefreshTokenError
from domain.entities.refresh_token import RefreshToken
from domain.ports.refresh_token_repository import RefreshTokenRepository
from domain.ports.token_service import ITokenService
from domain.ports.user_repository import UserRepository


class RefreshTokens:
    """
    Validates refresh token, revokes it, issues new access + refresh and persists the new refresh.
    """

    def __init__(
        self,
        token_service: ITokenService,
        refresh_token_repository: RefreshTokenRepository,
        user_repository: UserRepository,
    ):
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository
        self.user_repository = user_repository

    async def execute(self, refresh_token: str) -> AuthResponse:
        decoded = self.token_service.decode_refresh_token(refresh_token)
        if not decoded:
            raise InvalidRefreshTokenError("Invalid or expired refresh token")

        user_id, expires_at = decoded
        token_hash = self.token_service.hash_refresh_token(refresh_token)
        stored = await self.refresh_token_repository.find_by_token_hash(token_hash)

        if not stored:
            raise InvalidRefreshTokenError("Refresh token not found")

        now = datetime.now(timezone.utc)
        if not stored.is_active(now):
            raise InvalidRefreshTokenError("Refresh token expired or revoked")

        await self.refresh_token_repository.revoke(stored.id)

        new_access = self.token_service.create_access_token(
            user_id, claims=None
        )
        new_refresh_str = self.token_service.create_refresh_token(user_id)
        decoded_new = self.token_service.decode_refresh_token(new_refresh_str)

        if decoded_new:
            _, new_expires_at = decoded_new
            new_hash = self.token_service.hash_refresh_token(new_refresh_str)
            new_entity = RefreshToken(
                id=uuid4(),
                user_id=user_id,
                token_hash=new_hash,
                expires_at=new_expires_at,
                revoked_at=None,
                created_at=now,
            )
            await self.refresh_token_repository.save(new_entity)

        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise InvalidRefreshTokenError("User not found")

        return AuthResponse(
            user=UserDTO(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.picture,
            ),
            access_token=new_access,
            refresh_token=new_refresh_str,
            is_new_user=False,
        )
