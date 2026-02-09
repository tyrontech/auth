import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator

from domain.entities.oauth_connection import OAuthProvider
from infrastructure.database.base import Base

# Tipo en PostgreSQL: valores 'google', 'microsoft', 'github' (minúsculas)
_postgres_enum = ENUM(
    "google",
    "microsoft",
    "github",
    name="oauth_provider_enum",
    create_type=False,
)


def provider_to_db_value(provider: OAuthProvider | str | None) -> str | None:
    """
    Única fuente de verdad: valor que debe enviarse a PostgreSQL para provider.
    Usado por OAuthProviderType y por el repositorio en WHERE (asyncpg no usa el type en bind).
    """
    if provider is None:
        return None
    if isinstance(provider, OAuthProvider):
        return provider.value
    return str(provider)


class OAuthProviderType(TypeDecorator[OAuthProvider]):
    """
    Convierte OAuthProvider (dominio) ↔ valor en BD. Bind/result usan provider_to_db_value.
    """
    impl = _postgres_enum
    cache_ok = True

    def process_bind_param(self, value: OAuthProvider | str | None, dialect) -> str | None:
        return provider_to_db_value(value)

    def process_result_value(self, value: str | None, dialect) -> OAuthProvider | None:
        if value is None:
            return None
        return OAuthProvider(value)


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
        OAuthProviderType(), nullable=False
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
