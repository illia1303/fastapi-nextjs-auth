from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import UserModel
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserLogin


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, payload: UserCreate) -> UserModel:
        # email храним в нижнем регистре, чтобы User@Mail.com и user@mail.com были одним аккаунтом
        return await self.repo.create(payload.email.lower(), hash_password(payload.password))

    async def login(self, payload: UserLogin) -> tuple[UserModel, str]:
        user = await self.repo.get_by_email(payload.email.lower())
        if user is None or not user.is_active or not verify_password(payload.password, user.hashed_password):
            raise InvalidCredentialsError("Неверный email или пароль")
        return user, create_access_token(user.id)


def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(UserRepository(session))
