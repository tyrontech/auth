from typing import AsyncGenerator

import secrets
from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_database_url, get_settings, Settings
from domain.ports.oauth_connection_repository import OAuthConnectionRepository
from domain.ports.oauth_provider import IOAuthProvider
from domain.ports.refresh_token_repository import RefreshTokenRepository
from domain.ports.state_store import IStateStore
from domain.ports.token_service import ITokenService
from domain.ports.user_credentials_repository import UserCredentialsRepository
from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from infrastructure.database.session import create_async_engine_and_session_factory
from infrastructure.repositories.sqlalchemy_oauth_connection_repository import (
    SQLAlchemyOAuthConnectionRepository,
)
from infrastructure.repositories.sqlalchemy_refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)
from infrastructure.repositories.sqlalchemy_user_credentials_repository import (
    SQLAlchemyUserCredentialsRepository,
)
from infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from infrastructure.services.jwt_service import JWTTokenService
from infrastructure.providers.google import GoogleOAuthProvider
from infrastructure.services.oauth_state_store import InMemoryStateStore
from application.use_cases.authenticate_with_google import AuthenticateWithGoogle

# Composition root: solo aquí se une config con infra. Infra no importa config.
_settings = get_settings()
_state_store: IStateStore = InMemoryStateStore()
OAUTH_STATE_TTL_SECONDS = 600
_engine, _session_factory = create_async_engine_and_session_factory(
    get_database_url(),
    echo=_settings.DEBUG,
    pool_size=_settings.DB_POOL_MAX_SIZE,
    max_overflow=0,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provee una sesión asíncrona por request."""
    async with _session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_token_service(settings: Settings = Depends(get_settings)) -> ITokenService:
    return JWTTokenService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )

def get_oauth_provider(settings: Settings = Depends(get_settings)) -> IOAuthProvider:
    return GoogleOAuthProvider(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.GOOGLE_SCOPES,
    )


def get_google_redirect_uri(
    settings: Settings = Depends(get_settings),
) -> str:
    """Redirect URI para OAuth. La presentación no importa config."""
    return settings.GOOGLE_REDIRECT_URI


def get_state_store() -> IStateStore:
    return _state_store


def get_oauth_state(
    state_store: IStateStore = Depends(get_state_store),
) -> str:
    """Genera state, lo guarda con TTL y lo devuelve para el redirect OAuth."""
    state = secrets.token_urlsafe(32)
    state_store.set(state, ttl_seconds=OAUTH_STATE_TTL_SECONDS)
    return state


def require_oauth_state(
    state: str = Query(..., description="State devuelto por Google"),
    state_store: IStateStore = Depends(get_state_store),
) -> str:
    """Verifica y consume el state (protección CSRF). Falla si no existe o expiró."""
    if not state_store.consume(state):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state. Restart the login flow.",
        )
    return state


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(session)

def get_oauth_repository(
    session: AsyncSession = Depends(get_db),
) -> OAuthConnectionRepository:
    return SQLAlchemyOAuthConnectionRepository(session)


def get_refresh_token_repository(
    session: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    return SQLAlchemyRefreshTokenRepository(session)


def get_user_credentials_repository(
    session: AsyncSession = Depends(get_db),
) -> UserCredentialsRepository:
    return SQLAlchemyUserCredentialsRepository(session)


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
    token_service: ITokenService = Depends(get_token_service),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    """Extrae y valida el access token Bearer; devuelve el usuario o 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization")
    token = authorization.removeprefix("Bearer ").strip()
    user_id = token_service.validate_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_authenticate_google_use_case(
    token_service: ITokenService = Depends(get_token_service),
    oauth_provider: IOAuthProvider = Depends(get_oauth_provider),
    user_repository: UserRepository = Depends(get_user_repository),
    oauth_repository: OAuthConnectionRepository = Depends(get_oauth_repository),
    refresh_token_repository: RefreshTokenRepository = Depends(
        get_refresh_token_repository
    ),
) -> AuthenticateWithGoogle:
    return AuthenticateWithGoogle(
        oauth_provider=oauth_provider,
        user_repository=user_repository,
        oauth_connection_repository=oauth_repository,
        token_service=token_service,
        refresh_token_repository=refresh_token_repository,
    )
