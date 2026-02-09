from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from domain.entities.oauth_connection import OAuthConnection, OAuthProvider
from domain.ports.oauth_connection_repository import OAuthConnectionRepository
from infrastructure.database.models.oauth_connection import OAuthConnectionModel


class SQLAlchemyOAuthConnectionRepository(OAuthConnectionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_user_and_provider(
        self,
        user_id: UUID,
        provider: OAuthProvider
    ) -> Optional[OAuthConnection]:
        stmt = select(OAuthConnectionModel).where(
            OAuthConnectionModel.user_id == user_id,
            OAuthConnectionModel.provider == provider,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_provider_user_id(
        self,
        provider: OAuthProvider,
        provider_user_id: str
    ) -> Optional[OAuthConnection]:
        stmt = select(OAuthConnectionModel).where(
            OAuthConnectionModel.provider == provider,
            OAuthConnectionModel.provider_user_id == provider_user_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_all_by_user(
        self,
        user_id: UUID
    ) -> List[OAuthConnection]:
        stmt = select(OAuthConnectionModel).where(OAuthConnectionModel.user_id == user_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, connection: OAuthConnection) -> OAuthConnection:
        model = await self._find_model(connection.id)
        if not model:
            model = OAuthConnectionModel(
                id=connection.id,
                user_id=connection.user_id,
                provider=connection.provider,
                provider_user_id=connection.provider_user_id,
                provider_email=connection.provider_email,
                access_token_hash=connection.access_token_hash,
                refresh_token_hash=connection.refresh_token_hash,
                token_expires_at=connection.token_expires_at,
                created_at=connection.created_at,
                last_used_at=connection.last_used_at
            )
            self.session.add(model)
        else:
            # Update fields
            model.last_used_at = connection.last_used_at
            model.access_token_hash = connection.access_token_hash
            model.refresh_token_hash = connection.refresh_token_hash
            model.token_expires_at = connection.token_expires_at
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, connection_id: UUID) -> bool:
        model = await self._find_model(connection_id)
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False

    async def _find_model(self, connection_id: UUID) -> Optional[OAuthConnectionModel]:
        result = await self.session.execute(select(OAuthConnectionModel).where(OAuthConnectionModel.id == connection_id))
        return result.scalar_one_or_none()

    def _to_entity(self, model: OAuthConnectionModel) -> OAuthConnection:
        provider = (
            model.provider
            if isinstance(model.provider, OAuthProvider)
            else OAuthProvider(model.provider)
        )
        return OAuthConnection(
            id=model.id,
            user_id=model.user_id,
            provider=provider,
            provider_user_id=model.provider_user_id,
            provider_email=model.provider_email,
            access_token_hash=model.access_token_hash,
            refresh_token_hash=model.refresh_token_hash,
            token_expires_at=model.token_expires_at,
            created_at=model.created_at,
            last_used_at=model.last_used_at
        )
