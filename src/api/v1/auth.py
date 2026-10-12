"""REST-эндпоинты аутентификации и профиля пользователя."""

import asyncio

from fastapi import APIRouter, HTTPException, status

from src.api.deps import CurrentUser, SessionDep
from src.core.exceptions import AlreadyExistsException
from src.core.security import create_access_token, hash_password, verify_password
from src.repositories import (
    create_audit_event,
    create_user,
    get_user_by_email,
)
from src.schemas import TokenResponse, UserLogin, UserRead, UserRegister

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    credentials: UserRegister,
    session: SessionDep,
) -> TokenResponse:
    """Регистрирует нового пользователя и возвращает access token."""
    hashed_password = await asyncio.to_thread(hash_password, credentials.password)
    try:
        user = await create_user(
            session,
            email=str(credentials.email),
            hashed_password=hashed_password,
        )
        await create_audit_event(
            session,
            "user.created.success",
            actor_id=user.id,
            metadata={"email": user.email},
        )
    except AlreadyExistsException as error:
        await create_audit_event(
            session,
            "user.created.fail",
            actor_id=None,
            metadata={"email": str(credentials.email)},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с текущей почтой уже зарегистрирован.",
        ) from error

    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    session: SessionDep,
) -> TokenResponse:
    """Аутентифицирует пользователя и возвращает access token."""
    user = await get_user_by_email(session, str(credentials.email))
    if user is None:
        await create_audit_event(
            session,
            event_type="user.login.fail",
            actor_id=None,
            metadata={"email": str(credentials.email)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные данные для входа.",
        )
    is_valid_pass = await asyncio.to_thread(
        verify_password, credentials.password, user.hashed_password
    )
    if not is_valid_pass:
        await create_audit_event(
            session,
            event_type="user.login.fail",
            actor_id=None,
            metadata={"email": str(credentials.email)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные данные для входа.",
        )

    access_token = create_access_token(user.id)
    await create_audit_event(
        session,
        event_type="user.login.success",
        actor_id=user.id,
        metadata={"email": str(credentials.email)},
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def get_current_profile(current_user: CurrentUser) -> UserRead:
    """Возвращает данные текущего пользователя."""
    return UserRead.model_validate(current_user)
