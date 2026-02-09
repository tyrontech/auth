import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from domain.entities.oauth_connection import OAuthProvider
from infrastructure.database.base import Base

OAUTH_PROVIDER_ENUM = ENUM(
    OAuthProvider,
    name="oauth_provider_enum",
    create_type=False,
)


class OAuthConnectionModel(Base):
    __tablename__ = "auth_oauth_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_auth_oauth_user_provider"),
        UniqueConstraint(
            "provider", "provider_user_id", name="uq_auth_oauth_provider_user"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[OAuthProvider] = mapped_column(
        OAUTH_PROVIDER_ENUM, nullable=False
    )
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str] = mapped_column(String(255), nullable=False)

    access_token_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
