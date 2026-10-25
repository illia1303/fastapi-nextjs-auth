from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserModel


class UserAlreadyExistsError(Exception):
    pass


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> UserModel | None:
        return await self.session.get(UserModel, user_id)

    async def get_by_email(self, email: str) -> UserModel | None:
        query = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, email: str, hashed_password: str) -> UserModel:
        user = UserModel(email=email, hashed_password=hashed_password)
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise UserAlreadyExistsError(f"Пользователь с email '{email}' уже существует")
        await self.session.refresh(user)
        return user
