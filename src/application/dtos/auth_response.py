from dataclasses import dataclass
from typing import Optional
from uuid import UUID

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
