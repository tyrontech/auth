from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from domain.entities.user_credentials import UserCredentials
from domain.ports.user_credentials_repository import UserCredentialsRepository
from infrastructure.database.models.user_credentials import UserCredentialsModel


class SQLAlchemyUserCredentialsRepository(UserCredentialsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_user_id(
        self, user_id: UUID
    ) -> Optional[UserCredentials]:
        stmt = select(UserCredentialsModel).where(
            UserCredentialsModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, credentials: UserCredentials) -> UserCredentials:
        model = await self._find_model(credentials.id)
        if not model:
            model = UserCredentialsModel(
                id=credentials.id,
                user_id=credentials.user_id,
                password_hash=credentials.password_hash,
                last_password_change=credentials.last_password_change,
                failed_login_attempts=credentials.failed_login_attempts,
                locked_until=credentials.locked_until,
                created_at=credentials.created_at,
                updated_at=credentials.updated_at,
            )
            self.session.add(model)
        else:
            model.password_hash = credentials.password_hash
            model.last_password_change = credentials.last_password_change
            model.failed_login_attempts = credentials.failed_login_attempts
            model.locked_until = credentials.locked_until
            model.updated_at = credentials.updated_at
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def _find_model(
        self, credentials_id: UUID
    ) -> Optional[UserCredentialsModel]:
        result = await self.session.execute(
            select(UserCredentialsModel).where(
                UserCredentialsModel.id == credentials_id
            )
        )
        return result.scalar_one_or_none()

    def _to_entity(
        self, model: UserCredentialsModel
    ) -> UserCredentials:
        return UserCredentials(
            id=model.id,
            user_id=model.user_id,
            password_hash=model.password_hash,
            last_password_change=model.last_password_change,
            failed_login_attempts=model.failed_login_attempts,
            locked_until=model.locked_until,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
