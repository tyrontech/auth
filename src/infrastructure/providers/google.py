from google_auth_oauthlib.flow import Flow

from domain.ports.oauth_provider import IOAuthProvider, ProviderUser

class GoogleOAuthProvider(IOAuthProvider):
    def __init__(self, client_id: str, client_secret: str, scopes: list[str]):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes
    
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
    
    def get_user_info(self, access_token: str) -> ProviderUser:
        import requests as http_requests
        
        response = http_requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        data = response.json()
        
        return ProviderUser(
            provider_id=data.get("id"),  # Google v2 userinfo uses 'id'
            email=data["email"],
            name=data.get("name", ""),
            picture=data.get("picture"),
            email_verified=data.get("verified_email", False),
            extra_data=data
        )
    
