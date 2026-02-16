"""
Validación de configuración (Settings) al inicio de la aplicación.
Solo valida reglas de negocio sobre la configuración; no conoce DB ni Redis.
La conectividad a recursos se valida en infrastructure.health.
"""
import logging

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class ConfigurationValidationError(Exception):
    """Excepción lanzada cuando la validación de configuración falla."""
    pass


def validate_settings(settings: Settings | None = None) -> None:
    """
    Valida la configuración básica de Settings.
    Pydantic ya valida tipos y campos requeridos; esta función
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
