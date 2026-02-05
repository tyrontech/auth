from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class UserCredentials:
    id: UUID
    user_id: UUID
    password_hash: str
    last_password_change: Optional[datetime]
    failed_login_attempts: int
    locked_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > now