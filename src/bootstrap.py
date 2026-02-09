"""
Composition root: único lugar que lee config y crea infra.
Main llama init() al arranque; deps importa los getters desde aquí.
Singletons (token, oauth, state_store) se crean aquí; get_db por request.
Para tests: init(container=mi_container) con un container que tenga mocks.
"""
from typing import Any, Protocol

from config.settings import get_database_url, get_settings
from infrastructure.database.session import create_db_provider
from infrastructure.services.oauth_state_store import InMemoryStateStore
from infrastructure.services.jwt_service import JWTTokenService
from infrastructure.providers.google import GoogleOAuthProvider

from domain.ports.state_store import IStateStore
from domain.ports.token_service import ITokenService
from domain.ports.oauth_provider import IOAuthProvider


class AppContainer(Protocol):
    """Protocol for the app container. Tests can provide a substitute."""

    def get_db(self) -> Any:
        """Returns the async generator function for session per request."""
        ...

    def get_state_store(self) -> IStateStore:
        ...

    def get_token_service(self) -> ITokenService:
        ...

    def get_oauth_provider(self) -> IOAuthProvider:
        ...


class _DefaultContainer:
    """Default container built from config."""

    def __init__(
        self,
        db_provider,
        state_store: IStateStore,
        token_service: ITokenService,
        oauth_provider: IOAuthProvider,
    ):
        self._db_provider = db_provider
        self._state_store = state_store
        self._token_service = token_service
        self._oauth_provider = oauth_provider

    def get_db(self):
        """Returns the async generator function (FastAPI will call it and iterate)."""
        return self._db_provider

    def get_state_store(self) -> IStateStore:
        return self._state_store

    def get_token_service(self) -> ITokenService:
        return self._token_service

    def get_oauth_provider(self) -> IOAuthProvider:
        return self._oauth_provider


_container: AppContainer | None = None


def init(container: AppContainer | None = None) -> None:
    """
    Compose infra from config. Must be called at startup (main) before loading routers.
    If container is provided (e.g. in tests with mocks), it is used; otherwise a default
    container is built from settings.
    """
    global _container
    if container is not None:
        _container = container
        return

    settings = get_settings()

    db_provider = create_db_provider(
        get_database_url(),
        echo=settings.DEBUG,
        pool_size=settings.DB_POOL_MAX_SIZE,
        max_overflow=0,
    )

    state_store = _create_state_store(settings)

    token_service = JWTTokenService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    oauth_provider = GoogleOAuthProvider(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.GOOGLE_SCOPES,
    )

    _container = _DefaultContainer(
        db_provider=db_provider,
        state_store=state_store,
        token_service=token_service,
        oauth_provider=oauth_provider,
    )


def _create_state_store(settings):
    """Create state store based on STATE_STORE_BACKEND."""
    from infrastructure.services.redis_state_store import RedisStateStore

    if settings.STATE_STORE_BACKEND == "redis" and settings.REDIS_URL:
        return RedisStateStore(
            redis_url=settings.REDIS_URL,
            key_prefix=settings.REDIS_KEY_PREFIX,
        )
    return InMemoryStateStore()


def _get_container() -> AppContainer:
    if _container is None:
        raise RuntimeError(
            "Bootstrap not initialized. Call bootstrap.init() before starting the application."
        )
    return _container


async def get_db():
    """
    Async generator: yield session per request. FastAPI Depends(get_db) injects the session.
    Must be an async generator so FastAPI iterates it; a sync function returning the generator
    would inject the generator object instead of the session.
    """
    container = _get_container()
    inner_gen = container.get_db()()
    try:
        session = await inner_gen.__anext__()
        yield session
    finally:
        await inner_gen.aclose()


def get_state_store() -> IStateStore:
    return _get_container().get_state_store()


def get_token_service() -> ITokenService:
    return _get_container().get_token_service()


def get_oauth_provider() -> IOAuthProvider:
    return _get_container().get_oauth_provider()
