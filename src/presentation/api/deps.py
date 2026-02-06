from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database.session import get_db

from infrastructure.database.session import get_db
from infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from infrastructure.repositories.sqlalchemy_oauth_connection_repository import SQLAlchemyOAuthConnectionRepository
from infrastructure.services.jwt_service import JWTTokenService
from infrastructure.providers.google import GoogleOAuthProvider
from application.use_cases.authenticate_with_google import AuthenticateWithGoogle
from domain.ports.token_service import ITokenService
from domain.ports.oauth_provider import IOAuthProvider
from domain.ports.user_repository import UserRepository
from domain.ports.oauth_connection_repository import OAuthConnectionRepository
from config.settings import get_settings

def get_token_service() -> ITokenService:
    settings = get_settings()
    return JWTTokenService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )

def get_oauth_provider() -> IOAuthProvider:
    settings = get_settings()
    return GoogleOAuthProvider(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.GOOGLE_SCOPES
    )

def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(session)

def get_oauth_repository(session: AsyncSession = Depends(get_db)) -> OAuthConnectionRepository:
    return SQLAlchemyOAuthConnectionRepository(session)

def get_authenticate_google_use_case(
    token_service: ITokenService = Depends(get_token_service),
    oauth_provider: IOAuthProvider = Depends(get_oauth_provider),
    user_repository: UserRepository = Depends(get_user_repository),
    oauth_repository: OAuthConnectionRepository = Depends(get_oauth_repository)
) -> AuthenticateWithGoogle:
    return AuthenticateWithGoogle(
        oauth_provider=oauth_provider,
        user_repository=user_repository,
        oauth_connection_repository=oauth_repository,
        token_service=token_service
    )
