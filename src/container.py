"""
Container: Composition Root y Container Manager en un solo módulo.
- Crea toda la infraestructura (composition root)
- Gestiona la instancia única de forma thread-safe
- Expone funciones de dependencia para FastAPI
- Gestiona el ciclo de vida completo de recursos (shutdown)

Este módulo es el único que debe importarse desde la capa de presentación.
"""
import logging
import threading
from typing import Any, Protocol, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine

from config.settings import get_database_url, get_settings
from domain.ports.database_session import IDatabaseSession
from domain.ports.oauth_connection_repository import OAuthConnectionRepository
from domain.ports.oauth_provider import IOAuthProvider
from domain.ports.refresh_token_repository import RefreshTokenRepository
from domain.ports.state_store import IStateStore
from domain.ports.token_service import ITokenService
from domain.ports.user_repository import UserRepository
from infrastructure.database.session import create_db_provider
from infrastructure.providers.google import GoogleOAuthProvider
from infrastructure.services.jwt_service import JWTTokenService
from infrastructure.services.oauth_state_store import InMemoryStateStore

# Import use cases for type hints only
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.use_cases.authenticate_with_google import AuthenticateWithGoogle
    from application.use_cases.refresh_tokens import RefreshTokens

logger = logging.getLogger(__name__)


# ============================================================================
# Protocol y Container Implementation
# ============================================================================


class AppContainer(Protocol):
    """Protocol for the app container. Tests can provide a substitute."""

    def get_db(self) -> Any:
        """
        Returns the async generator function for session per request.
        The generator yields IDatabaseSession (not AsyncSession directly).
        """
        ...

    def get_state_store(self) -> IStateStore:
        ...

    def get_token_service(self) -> ITokenService:
        ...

    def get_oauth_provider(self) -> IOAuthProvider:
        ...

    def get_db_engine(self) -> AsyncEngine:
        """
        Retorna el engine de base de datos para gestión de ciclo de vida.
        Útil para validación de conexión y shutdown.
        """
        ...

    def create_user_repository(self, session: IDatabaseSession) -> UserRepository:
        """Factory method to create user repository. Returns domain port."""
        ...

    def create_oauth_repository(self, session: IDatabaseSession) -> OAuthConnectionRepository:
        """Factory method to create oauth repository. Returns domain port."""
        ...

    def create_refresh_token_repository(self, session: IDatabaseSession) -> RefreshTokenRepository:
        """Factory method to create refresh token repository. Returns domain port."""
        ...

    def create_authenticate_google_use_case(
        self, session: IDatabaseSession
    ) -> "AuthenticateWithGoogle":
        """Factory method to create AuthenticateWithGoogle use case."""
        ...

    def create_refresh_tokens_use_case(self, session: IDatabaseSession) -> "RefreshTokens":
        """Factory method to create RefreshTokens use case."""
        ...

    async def shutdown(self) -> None:
        """
        Cierra todos los recursos del container (DB connections, Redis, etc).
        Debe ser llamado durante el shutdown de la aplicación.
        """
        ...


class _DefaultContainer:
    """
    Default container built from config.
    Gestiona el ciclo de vida completo de todos los recursos.
    """

    def __init__(
        self,
        db_engine: AsyncEngine,
        db_provider,
        state_store: IStateStore,
        token_service: ITokenService,
        oauth_provider: IOAuthProvider,
    ):
        self._db_engine = db_engine
        self._db_provider = db_provider
        self._state_store = state_store
        self._token_service = token_service
        self._oauth_provider = oauth_provider
        self._shutdown_called = False

    def get_db(self):
        """Returns the async generator function (FastAPI will call it and iterate)."""
        return self._db_provider

    def get_state_store(self) -> IStateStore:
        return self._state_store

    def get_token_service(self) -> ITokenService:
        return self._token_service

    def get_oauth_provider(self) -> IOAuthProvider:
        return self._oauth_provider

    def get_db_engine(self) -> AsyncEngine:
        """
        Retorna el engine de base de datos para gestión de ciclo de vida.
        Útil para validación de conexión y shutdown.
        """
        return self._db_engine

    def create_user_repository(self, session: IDatabaseSession) -> UserRepository:
        """Factory method to create user repository."""
        from infrastructure.repositories.sqlalchemy_user_repository import (
            SQLAlchemyUserRepository,
        )

        return SQLAlchemyUserRepository(session)

    def create_oauth_repository(self, session: IDatabaseSession) -> OAuthConnectionRepository:
        """Factory method to create oauth repository."""
        from infrastructure.repositories.sqlalchemy_oauth_connection_repository import (
            SQLAlchemyOAuthConnectionRepository,
        )

        return SQLAlchemyOAuthConnectionRepository(session)

    def create_refresh_token_repository(self, session: IDatabaseSession) -> RefreshTokenRepository:
        """Factory method to create refresh token repository."""
        from infrastructure.repositories.sqlalchemy_refresh_token_repository import (
            SQLAlchemyRefreshTokenRepository,
        )

        return SQLAlchemyRefreshTokenRepository(session)

    def create_authenticate_google_use_case(
        self, session: IDatabaseSession
    ) -> "AuthenticateWithGoogle":
        """Factory method to create AuthenticateWithGoogle use case."""
        from application.use_cases.authenticate_with_google import (
            AuthenticateWithGoogle,
        )

        return AuthenticateWithGoogle(
            oauth_provider=self._oauth_provider,
            user_repository=self.create_user_repository(session),
            oauth_connection_repository=self.create_oauth_repository(session),
            token_service=self._token_service,
            refresh_token_repository=self.create_refresh_token_repository(session),
        )

    def create_refresh_tokens_use_case(self, session: IDatabaseSession) -> "RefreshTokens":
        """Factory method to create RefreshTokens use case."""
        from application.use_cases.refresh_tokens import RefreshTokens

        return RefreshTokens(
            token_service=self._token_service,
            refresh_token_repository=self.create_refresh_token_repository(session),
            user_repository=self.create_user_repository(session),
        )

    async def shutdown(self) -> None:
        """
        Cierra todos los recursos del container de forma ordenada.
        - Cierra el pool de conexiones de la base de datos
        - Cierra conexiones Redis si están activas
        - Marca el container como cerrado para prevenir uso después del shutdown
        """
        if self._shutdown_called:
            logger.warning("shutdown() called multiple times, ignoring")
            return

        logger.info("Shutting down container resources...")

        try:
            # Cerrar pool de conexiones de base de datos
            if self._db_engine is not None:
                logger.info("Closing database connection pool...")
                await self._db_engine.dispose()
                logger.info("✅ Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database engine: {e}", exc_info=True)

        try:
            # Cerrar conexión Redis si es RedisStateStore
            if hasattr(self._state_store, "_client"):
                # RedisStateStore tiene un cliente Redis
                client = getattr(self._state_store, "_client", None)
                if client is not None:
                    logger.info("Closing Redis connection...")
                    # Redis client síncrono usa close(), async usa aclose()
                    if hasattr(client, "aclose"):
                        await client.aclose()
                    elif hasattr(client, "close"):
                        client.close()
                    logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}", exc_info=True)

        self._shutdown_called = True
        logger.info("✅ Container shutdown completed")


def _create_state_store(settings):
    """Create state store based on STATE_STORE_BACKEND."""
    from infrastructure.services.redis_state_store import RedisStateStore

    if settings.STATE_STORE_BACKEND == "redis" and settings.REDIS_URL:
        return RedisStateStore(
            redis_url=settings.REDIS_URL,
            key_prefix=settings.REDIS_KEY_PREFIX,
        )
    return InMemoryStateStore()


def _create_container(container: AppContainer | None = None) -> AppContainer:
    """
    Crea y retorna el container con toda la infraestructura (Composition Root).
    
    Args:
        container: Container opcional para tests. Si se provee, se retorna directamente.
        
    Returns:
        AppContainer inicializado con toda la infraestructura.
        
    Note:
        La validación de configuración se realiza en el startup event de FastAPI
        (ver main.py lifespan) porque requiere código asíncrono y un event loop activo.
    """
    if container is not None:
        return container

    settings = get_settings()

    # Crear engine y provider de base de datos
    db_engine, db_provider = create_db_provider(
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

    return _DefaultContainer(
        db_engine=db_engine,
        db_provider=db_provider,
        state_store=state_store,
        token_service=token_service,
        oauth_provider=oauth_provider,
    )


# ============================================================================
# Container Manager (Thread-safe Singleton)
# ============================================================================


class ContainerNotInitializedError(RuntimeError):
    """Raised when container methods are called before initialization."""

    def __init__(self):
        super().__init__(
            "Container not initialized. Call container.initialize() before using the application."
        )


class ContainerManager:
    """
    Thread-safe singleton que gestiona la instancia del container.
    Usa un lock para asegurar inicialización única en entornos concurrentes.
    Implementa mejoras de thread-safety para lecturas concurrentes.
    """

    _instance: AppContainer | None = None
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def initialize(cls, container: AppContainer | None = None) -> None:
        """
        Inicializa el container. Debe llamarse una vez al arranque de la aplicación.
        
        Args:
            container: Container opcional para tests. Si no se provee, se crea uno por defecto.
            
        Raises:
            RuntimeError: Si se intenta inicializar más de una vez.
            
        Note:
            La validación de configuración se realiza en el startup event de FastAPI
            (ver main.py lifespan) después de la inicialización del container.
        """
        with cls._lock:
            if cls._initialized:
                raise RuntimeError(
                    "Container already initialized. Cannot initialize twice."
                )
            cls._instance = _create_container(container)
            cls._initialized = True
            logger.info("Container initialized successfully")

    @classmethod
    def get_instance(cls) -> AppContainer:
        """
        Obtiene la instancia del container de forma thread-safe.
        
        Usa lectura atómica de la referencia para evitar race conditions
        entre la verificación y el retorno.
        
        Returns:
            AppContainer inicializado.
            
        Raises:
            ContainerNotInitializedError: Si el container no ha sido inicializado.
        """
        # Lectura atómica de la referencia (thread-safe en Python)
        instance = cls._instance
        
        # Verificar estado después de leer la referencia
        if not cls._initialized or instance is None:
            raise ContainerNotInitializedError()
        
        return instance

    @classmethod
    async def shutdown(cls) -> None:
        """
        Cierra todos los recursos del container de forma ordenada.
        Debe ser llamado durante el shutdown de la aplicación (ej: FastAPI shutdown event).
        
        Thread-safe: usa lock para prevenir shutdown concurrente.
        """
        with cls._lock:
            if not cls._initialized or cls._instance is None:
                logger.warning("shutdown() called but container is not initialized")
                return
            
            try:
                await cls._instance.shutdown()
            except Exception as e:
                logger.error(f"Error during container shutdown: {e}", exc_info=True)
            finally:
                cls._instance = None
                cls._initialized = False
                logger.info("Container reset after shutdown")

    @classmethod
    def reset(cls) -> None:
        """
        Resetea el container (útil para tests).
        NO usar en producción. Para producción, usar shutdown().
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False


# Funciones de dependencia para FastAPI
# Estas son las únicas funciones que debe importar la capa de presentación


async def get_db():
    """
    Async generator: yield session per request. FastAPI Depends(get_db) injects the session.
    Must be an async generator so FastAPI iterates it; a sync function returning the generator
    would inject the generator object instead of the session.
    """
    container = ContainerManager.get_instance()
    inner_gen = container.get_db()()
    try:
        session = await inner_gen.__anext__()
        yield session
    finally:
        await inner_gen.aclose()


def get_state_store() -> IStateStore:
    """Obtiene el state store para OAuth."""
    return ContainerManager.get_instance().get_state_store()


def get_token_service() -> ITokenService:
    """Obtiene el servicio de tokens JWT."""
    return ContainerManager.get_instance().get_token_service()


def get_oauth_provider() -> IOAuthProvider:
    """Obtiene el proveedor OAuth."""
    return ContainerManager.get_instance().get_oauth_provider()


def get_user_repository(session: IDatabaseSession) -> UserRepository:
    """
    Factory function para crear un UserRepository.
    La capa de presentación no conoce implementaciones concretas.
    """
    return ContainerManager.get_instance().create_user_repository(session)


def get_oauth_repository(session: IDatabaseSession) -> OAuthConnectionRepository:
    """
    Factory function para crear un OAuthConnectionRepository.
    La capa de presentación no conoce implementaciones concretas.
    """
    return ContainerManager.get_instance().create_oauth_repository(session)


def get_refresh_token_repository(session: IDatabaseSession) -> RefreshTokenRepository:
    """
    Factory function para crear un RefreshTokenRepository.
    La capa de presentación no conoce implementaciones concretas.
    """
    return ContainerManager.get_instance().create_refresh_token_repository(session)


def get_authenticate_google_use_case(session: IDatabaseSession) -> "AuthenticateWithGoogle":
    """
    Factory function para crear el use case AuthenticateWithGoogle.
    La capa de presentación no conoce cómo se construye el use case.
    """
    from application.use_cases.authenticate_with_google import AuthenticateWithGoogle

    return ContainerManager.get_instance().create_authenticate_google_use_case(
        session
    )


def get_refresh_tokens_use_case(session: IDatabaseSession) -> "RefreshTokens":
    """
    Factory function para crear el use case RefreshTokens.
    La capa de presentación no conoce cómo se construye el use case.
    """
    from application.use_cases.refresh_tokens import RefreshTokens

    return ContainerManager.get_instance().create_refresh_tokens_use_case(session)
