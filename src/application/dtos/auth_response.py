from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class UserDTO:
    id: UUID
    email: str
    name: str
    picture: Optional[str]

@dataclass(frozen=True)
class AuthResponse:
    user: UserDTO
    access_token: str
    refresh_token: str
    is_new_user: bool
    token_type: str = "bearer"
