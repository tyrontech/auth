from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from application.dtos.auth_response import AuthResponse
from application.dtos.refresh_request import RefreshRequest
from application.exceptions import InvalidRefreshTokenError
from application.use_cases.authenticate_with_google import AuthenticateWithGoogle
from application.use_cases.refresh_tokens import RefreshTokens
from presentation.api import deps

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/login/google")
def login_google(
    oauth_provider=Depends(deps.get_oauth_provider),
    redirect_uri: str = Depends(deps.get_google_redirect_uri),
    state: str = Depends(deps.get_oauth_state),
):
    """Redirige al usuario a la pantalla de consentimiento de Google OAuth2."""
    authorization_url = oauth_provider.get_authorization_url(
        redirect_uri=redirect_uri,
        state=state,
    )
    return RedirectResponse(url=authorization_url)


@router.get("/callback/google", response_model=AuthResponse)
async def callback_google(
    code: str = Query(..., description="Código de autorización devuelto por Google"),
    _state: str = Depends(deps.require_oauth_state),
    use_case: AuthenticateWithGoogle = Depends(
        deps.get_authenticate_google_use_case_dep
    ),
    redirect_uri: str = Depends(deps.get_google_redirect_uri),
):
    """Recibe el callback de Google, crea/loguea usuario y devuelve tokens."""
    auth_response = await use_case.execute(code=code, redirect_uri=redirect_uri)
    return auth_response


@router.post("/refresh", response_model=AuthResponse)
async def refresh_tokens(
    body: RefreshRequest,
    use_case: RefreshTokens = Depends(deps.get_refresh_tokens_use_case_dep),
):
    """Intercambia un refresh token válido por nuevos access y refresh tokens (rotation)."""
    try:
        return await use_case.execute(refresh_token=body.refresh_token)
    except InvalidRefreshTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))
