from datetime import datetime
from uuid import uuid4
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests
from google.oauth2 import id_token
from config.settings import get_settings
from domain.ports.oauth_provider import IOAuthProvider
from domain.entities.user import User

class GoogleOAuthProvider(IOAuthProvider):
    def __init__(self):
        settings = get_settings()
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.scopes = settings.GOOGLE_SCOPES
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.scopes,
            redirect_uri=redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state
        )
        return auth_url
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.scopes,
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(code=code)
        
        return {
            "access_token": flow.credentials.token,
            "refresh_token": flow.credentials.refresh_token,
            "id_token": flow.credentials.id_token
        }
    
    def get_user_info(self, access_token: str) -> User:
        import requests as http_requests
        
        response = http_requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        data = response.json()
        now = datetime.utcnow()
        
        # Mapeamos a la Entidad de Dominio real (User)
        return User(
            id=uuid4(), # ID temporal, el caso de uso decidirá si busca uno existente o usa este
            email=data["email"],
            name=data.get("name", ""),
            picture=data.get("picture"),
            created_at=now,
            updated_at=now
        )
    
