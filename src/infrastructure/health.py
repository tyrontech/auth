"""
Validación de conectividad a recursos de infraestructura (DB, Redis, etc.).
Recibe recursos ya construidos; no crea engines ni clientes propios.
Escalable: cada nuevo recurso añade una función validate_* aquí.
"""
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class ConnectivityValidationError(Exception):
    """Falló la comprobación de conectividad a un recurso (DB, Redis, etc.)."""
    pass


async def validate_database_connection(engine: AsyncEngine) -> None:
    """
    Comprueba que el engine de base de datos permita ejecutar una query.

    Args:
        engine: Engine ya creado (p. ej. por el container).

    Raises:
        ConnectivityValidationError: Si la conexión falla.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection validated successfully")
    except Exception as e:
        logger.error("❌ Database connection validation failed: %s", e)
        raise ConnectivityValidationError(
            f"Failed to connect to database: {e}. "
            "Please check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME in your .env file."
        ) from e


async def validate_redis_connection(redis_url: str) -> None:
    """
    Comprueba que Redis sea alcanzable en la URL dada.

    Args:
        redis_url: URL de Redis ya configurada (p. ej. desde Settings).

    Raises:
        ConnectivityValidationError: Si la conexión falla o el paquete no está instalado.
    """
    try:
        import redis
    except ImportError:
        raise ConnectivityValidationError(
            "Redis backend selected but 'redis' package is not installed. "
            "Install it with: pip install redis"
        ) from None

    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        client.close()
        logger.info("✅ Redis connection validated successfully")
    except Exception as e:
        logger.error("❌ Redis connection validation failed: %s", e)
        raise ConnectivityValidationError(
            f"Failed to connect to Redis at {redis_url}: {e}. "
            "Please check REDIS_URL in your .env file or use STATE_STORE_BACKEND=memory."
        ) from e
