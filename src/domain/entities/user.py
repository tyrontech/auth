from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    name: str
    picture: Optional[str]
    created_at: datetime
    updated_at: datetime