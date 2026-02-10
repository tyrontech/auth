"""
Dependencias HTTP específicas de FastAPI.
Solo contiene funciones de validación, autenticación y extracción de datos HTTP.
NO construye objetos de aplicación (use cases, repositorios) - eso lo hace container.py
"""
from fastapi import Depends, Header, HTTPException, Query

from container import (
    get_authenticate_google_use_case,
    get_db,
    get_oauth_provider,
    get_refresh_tokens_use_case,
    get_state_store,
    get_token_service,
    get_user_repository,
)
from domain.ports.database_session import IDatabaseSession

# Re-exportar get_oauth_provider para que los endpoints lo usen directamente
__all__ = [
    "get_google_redirect_uri",
    "get_oauth_state",
    "require_oauth_state",
    "get_current_user",
    "get_authenticate_google_use_case_dep",
    "get_refresh_tokens_use_case_dep",
    "get_oauth_provider",  # Re-exportado desde container
]
from config.settings import get_settings, Settings
from domain.entities.user import User
from domain.ports.state_store import IStateStore
from domain.ports.token_service import ITokenService
from domain.ports.user_repository import UserRepository
from application.use_cases.authenticate_with_google import AuthenticateWithGoogle
from application.use_cases.refresh_tokens import RefreshTokens


# ============================================================================
# Configuración y Settings
# ============================================================================


def get_google_redirect_uri(
    settings: Settings = Depends(get_settings),
) -> str:
    """Extrae el redirect URI de Google desde configuración."""
    return settings.GOOGLE_REDIRECT_URI


# ============================================================================
# OAuth State Management (CSRF Protection)
# ============================================================================


def get_oauth_state(
    state_store: IStateStore = Depends(get_state_store),
    settings: Settings = Depends(get_settings),
) -> str:
    """Genera y almacena un state OAuth para protección CSRF."""
    return state_store.generate_and_store(
        ttl_seconds=settings.OAUTH_STATE_TTL_SECONDS
    )


def require_oauth_state(
    state: str = Query(..., description="State devuelto por Google"),
    state_store: IStateStore = Depends(get_state_store),
) -> str:
    """
    Valida y consume el state OAuth del request.
    Lanza HTTPException si el state es inválido o expirado.
    """
    if not state_store.consume(state):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state. Restart the login flow.",
        )
    return state


# ============================================================================
# Autenticación y Autorización
# ============================================================================


def _get_user_repository_dep(session: IDatabaseSession = Depends(get_db)) -> UserRepository:
    """
    Helper function para obtener UserRepository desde el container.
    Usa IDatabaseSession (protocolo del dominio) en lugar de tipos concretos de infraestructura.
    """
    return get_user_repository(session)


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
    token_service: ITokenService = Depends(get_token_service),
    user_repository: UserRepository = Depends(_get_user_repository_dep),
) -> User:
    """
    Valida el token JWT del header Authorization y retorna el usuario autenticado.
    Lanza HTTPException si el token es inválido, expirado o el usuario no existe.
    
    Nota: user_repository se construye desde el container usando IDatabaseSession.
    La capa de presentación usa el protocolo del dominio, no conoce detalles de infraestructura.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization"
        )
    token = authorization.removeprefix("Bearer ").strip()
    user_id = token_service.validate_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ============================================================================
# Use Cases (delegados al container)
# ============================================================================


def get_authenticate_google_use_case_dep(
    session: IDatabaseSession = Depends(get_db),
) -> AuthenticateWithGoogle:
    """
    Dependency function para obtener AuthenticateWithGoogle use case.
    Delega la construcción al container.
    
    Nota: session es IDatabaseSession (protocolo del dominio), no un tipo concreto de infraestructura.
    """
    return get_authenticate_google_use_case(session)


def get_refresh_tokens_use_case_dep(
    session: IDatabaseSession = Depends(get_db),
) -> RefreshTokens:
    """
    Dependency function para obtener RefreshTokens use case.
    Delega la construcción al container.
    
    Nota: session es IDatabaseSession (protocolo del dominio), no un tipo concreto de infraestructura.
    """
    return get_refresh_tokens_use_case(session)
