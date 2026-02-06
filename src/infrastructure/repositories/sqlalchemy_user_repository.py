from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from domain.ports.user_repository import UserRepository
from domain.entities.user import User
from infrastructure.database.models.user import UserModel

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        user_model = result.scalar_one_or_none()
        return self._to_entity(user_model) if user_model else None

    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        user_model = result.scalar_one_or_none()
        return self._to_entity(user_model) if user_model else None

    async def save(self, user: User) -> User:
        # Check if exists (upsert logic or just save)
        # For simplicity in this Clean Arch example, we assume we might need to update if ID exists, 
        # or separate create/update methods. The generic 'save' usually implies create or update.
        
        # Check if it exists in DB to decide between add or merge
        # Since domain User is immutable-ish, we map to model
        user_model = await self._find_model_by_id(user.id)
        
        if not user_model:
            user_model = UserModel(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.picture,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            self.session.add(user_model)
        else:
            user_model.name = user.name
            user_model.picture = user.picture
            user_model.updated_at = user.updated_at
            # email usually doesn't change easily in this flow, but if needed:
            user_model.email = user.email
            
        await self.session.commit()
        await self.session.refresh(user_model)
        return self._to_entity(user_model)

    async def _find_model_by_id(self, user_id: UUID) -> Optional[UserModel]:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalar_one_or_none()

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            name=model.name,
            picture=model.picture,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
