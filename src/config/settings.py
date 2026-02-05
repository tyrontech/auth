from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación.
    Lee automáticamente desde .env
    """
    
    # ==================== DATABASE ====================
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str
    DB_NAME: str = "auth_db"
    
    # Pool de conexiones
    DB_POOL_MIN_SIZE: int = 5
    DB_POOL_MAX_SIZE: int = 20
    
    # ==================== GOOGLE OAUTH ====================
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    
    GOOGLE_SCOPES: list[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    
    # ==================== JWT (Ed25519) ====================
    JWT_ALGORITHM: str = "EdDSA"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Rutas a las llaves (Defaults para local, override en producción via .env)
    PRIVATE_KEY_PATH: str = "keys/ed25519_private.pem"
    PUBLIC_KEY_PATH: str = "keys/ed25519_public.pem"
    
    # ==================== APP ====================
    
    # ==================== APP ====================
    APP_NAME: str = "Auth Service"
    APP_ENV: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # ==================== SEGURIDAD ====================
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


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