from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from bootstrap import (
    get_db,
    get_oauth_provider,
    get_state_store,
    get_token_service,
)
from config.settings import get_settings, Settings
from domain.entities.user import User
from domain.ports.oauth_connection_repository import OAuthConnectionRepository
from domain.ports.oauth_provider import IOAuthProvider
from domain.ports.refresh_token_repository import RefreshTokenRepository
from domain.ports.state_store import IStateStore
from domain.ports.token_service import ITokenService
from domain.ports.user_credentials_repository import UserCredentialsRepository
from domain.ports.user_repository import UserRepository
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
from application.use_cases.authenticate_with_google import AuthenticateWithGoogle


def get_google_redirect_uri(
    settings: Settings = Depends(get_settings),
) -> str:
    return settings.GOOGLE_REDIRECT_URI


def get_oauth_state(
    state_store: IStateStore = Depends(get_state_store),
    settings: Settings = Depends(get_settings),
) -> str:
    return state_store.generate_and_store(
        ttl_seconds=settings.OAUTH_STATE_TTL_SECONDS
    )


def require_oauth_state(
    state: str = Query(..., description="State devuelto por Google"),
    state_store: IStateStore = Depends(get_state_store),
) -> str:
    if not state_store.consume(state):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state. Restart the login flow.",
        )
    return state


def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
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
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization"
        )
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
