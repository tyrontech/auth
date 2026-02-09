"""Request DTO for refresh token endpoint."""

from pydantic import BaseModel, Field


class RefreshRequest(BaseModel):
    """Body for POST /api/auth/refresh."""

    refresh_token: str = Field(..., min_length=1, description="Refresh token to exchange")
