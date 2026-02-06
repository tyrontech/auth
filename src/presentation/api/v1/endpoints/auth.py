from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from application.use_cases.authenticate_with_google import AuthenticateWithGoogle
from application.dtos.auth_response import AuthResponse
from presentation.api import deps
from config.settings import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/login/google")
def login_google(
    oauth_provider = Depends(deps.get_oauth_provider)
):
    """
    Redirects the user to the Google OAuth2 consent screen.
    """
    # Simply using a random state for now, in prod use a secure random string associated with session
    authorization_url = oauth_provider.get_authorization_url(
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        state="random_state_string" 
    )
    return RedirectResponse(url=authorization_url)

@router.get("/callback/google", response_model=AuthResponse)
async def callback_google(
    code: str = Query(..., description="The authorization code returned by Google"),
    state: str = Query(..., description="The state parameter returned by Google"),
    use_case: AuthenticateWithGoogle = Depends(deps.get_authenticate_google_use_case)
):
    """
    Handles the Google OAuth2 callback, creates/logs in the user, and returns tokens.
    """
    # Verify state matches (omitted for brevity, but critical for security)
    
    auth_response = await use_case.execute(
        code=code,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    return auth_response
