from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación.
    Lee automáticamente desde .env
    """
    
    # ==================== DATABASE ====================
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str | None = None
    DB_NAME: str = "auth_db"
    
    # Pool de conexiones
    DB_POOL_MIN_SIZE: int = 5
    DB_POOL_MAX_SIZE: int = 20
    
    # ==================== GOOGLE OAUTH ====================
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback/google"
    GOOGLE_SCOPES: list[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    
    # ==================== JWT (Standard) ====================
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # ==================== APP ====================
    APP_NAME: str = "Auth Service"
    APP_ENV: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # ==================== SEGURIDAD ====================
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # ==================== VALIDACIONES ====================
    @field_validator("DB_PASSWORD", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    @classmethod
    def check_required_fields(cls, v: str | None, info) -> str:
        """Valida que los campos críticos estén configurados"""
        if v is None or v == "":
            raise ValueError(
                f"❌ {info.field_name} es requerido. "
                f"Agrégalo al archivo .env"
            )
        return v
    
    # ==================== CONFIGURACIÓN PYDANTIC ====================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignora variables extra en .env
    )


# ==================== SINGLETON ====================
@lru_cache()
def get_settings() -> Settings:
    """
    Singleton: solo se carga una vez en memoria.
    En producción, si cambias el .env, reinicia la app.
    """
    return Settings()


# ==================== HELPER: Conexión DB ====================
def get_database_url() -> str:
    """Genera URL de conexión PostgreSQL Asíncrona (asyncpg)"""
    settings = get_settings()
    return (
        f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )