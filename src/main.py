import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from container import ContainerManager
from config.settings import get_settings
from config.validation import validate_settings, ConfigurationValidationError
from infrastructure.health import (
    ConnectivityValidationError,
    validate_database_connection,
    validate_redis_connection,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida completo de la aplicación:
    - Startup: Inicializa container y valida configuración
    - Shutdown: Cierra recursos de forma ordenada
    """
    # Startup
    logger.info("Starting application...")
    try:
        # 1) Validar Settings (config; sin infraestructura)
        logger.info("Validating settings...")
        validate_settings(settings)

        # 2) Inicializar container (composition root)
        ContainerManager.initialize()
        container = ContainerManager.get_instance()
        engine = container.get_db_engine()

        # 3) Validar conectividad a recursos (infrastructure.health)
        logger.info("Validating connectivity...")
        await validate_database_connection(engine)
        if settings.STATE_STORE_BACKEND == "redis" and settings.REDIS_URL:
            await validate_redis_connection(settings.REDIS_URL)

        logger.info("✅ Application started successfully")
    except (ConfigurationValidationError, ConnectivityValidationError) as e:
        logger.error("Startup validation failed: %s", e)
        raise
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        await ContainerManager.shutdown()
        logger.info("✅ Application shut down successfully")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}", exc_info=True)


# Inicialización limpia con lifespan management
app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Configuración de Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas básicas
from presentation.api.v1.endpoints import auth
app.include_router(auth.router)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "env": settings.APP_ENV}

# Entrypoint: reload solo desde Settings, directorio de código explícito
if __name__ == "__main__":
    from pathlib import Path

    _reload = settings.DEBUG
    _reload_dirs = [str(Path(__file__).resolve().parent)] if _reload else None
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=_reload,
        reload_dirs=_reload_dirs,
    )
