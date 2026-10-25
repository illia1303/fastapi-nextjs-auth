from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import UserModel
from app.repositories.user import UserAlreadyExistsError
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth import AuthService, InvalidCredentialsError, get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    payload: UserCreate,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return await service.register(payload)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login", response_model=UserResponse)
async def login(
    payload: UserLogin,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    try:
        user, token = await service.login(payload)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))

    # Токен кладём в httpOnly cookie — JavaScript на странице его не видит.
    # Без max_age/expires это сессионная cookie: браузер удалит её при закрытии.
    # Сам JWT при этом всё равно истекает через ACCESS_TOKEN_EXPIRE_MINUTES.
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return user


@router.post("/logout", status_code=204)
async def logout():
    response = Response(status_code=204)
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/me", response_model=UserResponse)
async def me(user: UserModel = Depends(get_current_user)):
    return user
