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
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "env": settings.APP_ENV}

# Entrypoint para desarrollo
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG
    )
