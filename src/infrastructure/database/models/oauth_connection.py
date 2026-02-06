from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from infrastructure.database.base import Base

class OAuthConnectionModel(Base):
    __tablename__ = "oauth_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    provider = Column(String, nullable=False) # e.g. "google"
    provider_user_id = Column(String, nullable=False)
    provider_email = Column(String, nullable=False)
    
    access_token_hash = Column(String, nullable=True)
    refresh_token_hash = Column(String, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())
