from datetime import datetime, timezone
from uuid import uuid4

from application.dtos.auth_response import AuthResponse, UserDTO
from domain.entities.oauth_connection import OAuthConnection, OAuthProvider
from domain.entities.refresh_token import RefreshToken
from domain.entities.user import User
from domain.ports.oauth_connection_repository import OAuthConnectionRepository
from domain.ports.oauth_provider import IOAuthProvider
from domain.ports.refresh_token_repository import RefreshTokenRepository
from domain.ports.token_service import ITokenService
from domain.ports.user_repository import UserRepository


class AuthenticateWithGoogle:
    def __init__(
        self,
        oauth_provider: IOAuthProvider,
        user_repository: UserRepository,
        oauth_connection_repository: OAuthConnectionRepository,
        token_service: ITokenService,
        refresh_token_repository: RefreshTokenRepository,
    ):
        self.oauth_provider = oauth_provider
        self.user_repository = user_repository
        self.oauth_connection_repository = oauth_connection_repository
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def execute(self, code: str, redirect_uri: str) -> AuthResponse:
        tokens = self.oauth_provider.exchange_code_for_token(code, redirect_uri)
        google_access_token = tokens["access_token"]

        provider_user = await self.oauth_provider.get_user_info(google_access_token)

        user = await self.user_repository.find_by_email(provider_user.email)
        is_new_user = False
        now = datetime.now(timezone.utc)

        if not user:
            is_new_user = True
            user = User(
                id=uuid4(),
                email=provider_user.email,
                name=provider_user.name or "",
                picture=provider_user.picture,
                created_at=now,
                updated_at=now,
            )
            user = await self.user_repository.save(user)

        connection = await self.oauth_connection_repository.find_by_provider_user_id(
            OAuthProvider.GOOGLE,
            provider_user.provider_id,
        )
        if not connection:
            connection = OAuthConnection(
                id=uuid4(),
                user_id=user.id,
                provider=OAuthProvider.GOOGLE,
                provider_user_id=provider_user.provider_id,
                provider_email=provider_user.email,
                access_token_hash=None,
                refresh_token_hash=None,
                token_expires_at=None,
                created_at=now,
                last_used_at=now,
            )
            await self.oauth_connection_repository.save(connection)

        access_token = self.token_service.create_access_token(
            user.id, claims={"email": user.email}
        )
        refresh_token_str = self.token_service.create_refresh_token(user.id)

        decoded = self.token_service.decode_refresh_token(refresh_token_str)
        if decoded:
            user_id_refresh, expires_at = decoded
            token_hash = self.token_service.hash_refresh_token(refresh_token_str)
            refresh_entity = RefreshToken(
                id=uuid4(),
                user_id=user_id_refresh,
                token_hash=token_hash,
                expires_at=expires_at,
                revoked_at=None,
                created_at=now,
            )
            await self.refresh_token_repository.save(refresh_entity)

        return AuthResponse(
            user=UserDTO(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.picture,
            ),
            is_new_user=is_new_user,
            access_token=access_token,
            refresh_token=refresh_token_str,
        )
