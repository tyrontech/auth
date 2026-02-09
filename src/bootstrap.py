"""
Composition root: único lugar que lee config y crea infra.
Main llama init() al arranque; deps importa los getters desde aquí.
Singletons (token, oauth, state_store) se crean aquí; get_db por request.
"""
from config.settings import get_database_url, get_settings
from infrastructure.database.session import create_db_provider
from infrastructure.services.oauth_state_store import InMemoryStateStore
from infrastructure.services.jwt_service import JWTTokenService
from infrastructure.providers.google import GoogleOAuthProvider

from domain.ports.state_store import IStateStore
from domain.ports.token_service import ITokenService
from domain.ports.oauth_provider import IOAuthProvider

_db_provider = None
_state_store: IStateStore | None = None
_token_service: ITokenService | None = None
_oauth_provider: IOAuthProvider | None = None


def init() -> None:
    """Compose infra from config. Must be called at startup (main) before loading routers."""
    global _db_provider, _state_store, _token_service, _oauth_provider
    settings = get_settings()

    _db_provider = create_db_provider(
        get_database_url(),
        echo=settings.DEBUG,
        pool_size=settings.DB_POOL_MAX_SIZE,
        max_overflow=0,
    )
    _state_store = InMemoryStateStore()
    _token_service = JWTTokenService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    _oauth_provider = GoogleOAuthProvider(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.GOOGLE_SCOPES,
    )


def get_db():
    """Session provider per request. Raises if bootstrap not initialized."""
    if _db_provider is None:
        raise RuntimeError(
            "Bootstrap not initialized. Call bootstrap.init() before starting the application."
        )
    return _db_provider()


def get_state_store() -> IStateStore:
    if _state_store is None:
        raise RuntimeError(
            "Bootstrap not initialized. Call bootstrap.init() before starting the application."
        )
    return _state_store


def get_token_service() -> ITokenService:
    if _token_service is None:
        raise RuntimeError(
            "Bootstrap not initialized. Call bootstrap.init() before starting the application."
        )
    return _token_service


def get_oauth_provider() -> IOAuthProvider:
    if _oauth_provider is None:
        raise RuntimeError(
            "Bootstrap not initialized. Call bootstrap.init() before starting the application."
        )
    return _oauth_provider
