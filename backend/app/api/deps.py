from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.core.security import decode_access_token
from app.models.user import UserModel
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> UserModel:
    unauthorized = HTTPException(status_code=401, detail="Требуется авторизация")

    # Браузер присылает токен в httpOnly cookie; заголовок Bearer оставлен для Swagger и API-клиентов
    token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if token is None and credentials is not None:
        token = credentials.credentials
    if token is None:
        raise unauthorized

    user_id = decode_access_token(token)
    if user_id is None:
        raise unauthorized

    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user
