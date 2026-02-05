from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class RefreshToken:
    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked_at: Optional[datetime]
    created_at: datetime

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now