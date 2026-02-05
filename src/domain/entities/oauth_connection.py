from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class OAuthProvider(str, Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"


@dataclass
class OAuthConnection:
    id: UUID
    user_id: UUID
    provider: OAuthProvider
    provider_user_id: str
    provider_email: str
    access_token_hash: Optional[str]
    refresh_token_hash: Optional[str]
    token_expires_at: Optional[datetime]
    created_at: datetime
    last_used_at: datetime