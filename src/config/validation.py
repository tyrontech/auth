"""
Validación robusta de configuración al inicio de la aplicación.
Verifica que todos los recursos críticos estén disponibles y funcionando.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class ConfigurationValidationError(Exception):
    """Excepción lanzada cuando la validación de configuración falla."""
    pass


async def validate_database_connection(engine: AsyncEngine) -> None:
    """
    Valida que la conexión a la base de datos funcione correctamente.
    
    Args:
        engine: Engine de SQLAlchemy para probar la conexión.
        
    Raises:
        ConfigurationValidationError: Si la conexión falla.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection validated successfully")
    except Exception as e:
        logger.error(f"❌ Database connection validation failed: {e}")
        raise ConfigurationValidationError(
            f"Failed to connect to database: {e}. "
            "Please check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME in your .env file."
        ) from e


async def validate_redis_connection(redis_url: str) -> None:
    """
    Valida que la conexión a Redis funcione correctamente.
    
    Args:
        redis_url: URL de conexión a Redis.
        
    Raises:
        ConfigurationValidationError: Si la conexión falla.
    """
    try:
        import redis
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        # Test connection with ping
        client.ping()
        client.close()
        logger.info("✅ Redis connection validated successfully")
    except ImportError:
        raise ConfigurationValidationError(
            "Redis backend selected but 'redis' package is not installed. "
            "Install it with: pip install redis"
        ) from None
    except Exception as e:
        logger.error(f"❌ Redis connection validation failed: {e}")
        raise ConfigurationValidationError(
            f"Failed to connect to Redis at {redis_url}: {e}. "
            "Please check REDIS_URL in your .env file or use STATE_STORE_BACKEND=memory."
        ) from e


def validate_settings(settings: Settings | None = None) -> None:
    """
    Valida la configuración básica de Settings.
    Pydantic ya valida tipos y campos requeridos, pero esta función
    añade validaciones de negocio adicionales.
    
    Args:
        settings: Instancia de Settings a validar. Si es None, usa get_settings().
        
    Raises:
        ConfigurationValidationError: Si alguna validación falla.
    """
    if settings is None:
        settings = get_settings()
    
    # Validar que SECRET_KEY no sea el valor por defecto en producción
    default_secret = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    if settings.APP_ENV == "production" and settings.SECRET_KEY == default_secret:
        raise ConfigurationValidationError(
            "SECRET_KEY must be changed from default value in production. "
            "Generate a secure key and set it in your .env file."
        )
    
    # Validar que los tiempos de expiración sean razonables
    if settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        raise ConfigurationValidationError(
            f"ACCESS_TOKEN_EXPIRE_MINUTES must be positive, got {settings.ACCESS_TOKEN_EXPIRE_MINUTES}"
        )
    
    if settings.REFRESH_TOKEN_EXPIRE_MINUTES <= 0:
        raise ConfigurationValidationError(
            f"REFRESH_TOKEN_EXPIRE_MINUTES must be positive, got {settings.REFRESH_TOKEN_EXPIRE_MINUTES}"
        )
    
    if settings.REFRESH_TOKEN_EXPIRE_MINUTES <= settings.ACCESS_TOKEN_EXPIRE_MINUTES:
        raise ConfigurationValidationError(
            f"REFRESH_TOKEN_EXPIRE_MINUTES ({settings.REFRESH_TOKEN_EXPIRE_MINUTES}) "
            f"must be greater than ACCESS_TOKEN_EXPIRE_MINUTES ({settings.ACCESS_TOKEN_EXPIRE_MINUTES})"
        )
    
    # Validar pool de conexiones
    if settings.DB_POOL_MAX_SIZE < settings.DB_POOL_MIN_SIZE:
        raise ConfigurationValidationError(
            f"DB_POOL_MAX_SIZE ({settings.DB_POOL_MAX_SIZE}) "
            f"must be >= DB_POOL_MIN_SIZE ({settings.DB_POOL_MIN_SIZE})"
        )
    
    logger.info("✅ Settings validation passed")


async def validate_all_configuration(
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
) -> None:
    """
    Ejecuta todas las validaciones de configuración.
    
    Args:
        settings: Instancia de Settings. Si es None, usa get_settings().
        engine: Engine de SQLAlchemy para validar DB. Si es None, crea uno temporal.
        
    Raises:
        ConfigurationValidationError: Si alguna validación falla.
    """
    if settings is None:
        settings = get_settings()
    
    # Validar Settings primero (validaciones síncronas)
    validate_settings(settings)
    
    # Validar conexión a base de datos
    if engine is None:
        # Crear engine temporal solo para validación
        from config.settings import get_database_url
        temp_engine = create_async_engine(
            get_database_url(),
            echo=False,
            pool_size=1,
            max_overflow=0,
        )
        try:
            await validate_database_connection(temp_engine)
        finally:
            await temp_engine.dispose()
    else:
        await validate_database_connection(engine)
    
    # Validar Redis si está configurado
    if settings.STATE_STORE_BACKEND == "redis" and settings.REDIS_URL:
        await validate_redis_connection(settings.REDIS_URL)
    
    logger.info("✅ All configuration validations passed")
