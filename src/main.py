import bootstrap

bootstrap.init()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from config.settings import get_settings

settings = get_settings()

# Inicialización limpia
app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
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
