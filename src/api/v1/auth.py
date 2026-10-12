"""REST-эндпоинты аутентификации и профиля пользователя."""

import asyncio

from fastapi import APIRouter, HTTPException, Request, status

from src.api.deps import CurrentUser, SessionDep
from src.core.exceptions import AlreadyExistsException
from src.core.security import create_access_token, hash_password, verify_password
from src.repositories import (
    create_user,
    get_user_by_email,
    write_event,
)
from src.schemas import TokenResponse, UserLogin, UserRead, UserRegister

router = APIRouter(prefix="/auth", tags=["Auth"])


def extract_client_info(request: Request) -> tuple[str | None, str | None]:
    """Извлекает IP-адрес клиента и User-Agent из HTTP-запроса."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    elif real_ip := request.headers.get("x-real-ip"):
        ip = real_ip.strip()
    else:
        ip = request.client.host if request.client else None

    user_agent = request.headers.get("user-agent")
    return ip, user_agent


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    credentials: UserRegister,
    session: SessionDep,
    request: Request,
) -> TokenResponse:
    """Регистрирует нового пользователя и возвращает access token."""
    ip, user_agent = extract_client_info(request)
    hashed_password = await asyncio.to_thread(hash_password, credentials.password)
    try:
        user = await create_user(
            session,
            email=str(credentials.email),
            hashed_password=hashed_password,
        )
        await write_event(
            session,
            event_type="user.created",
            actor_id=user.id,
            client_id=None,
            ip=ip,
            user_agent=user_agent,
            metadata={"email": user.email},
        )
    except AlreadyExistsException as error:
        await write_event(
            session,
            event_type="user.created.failure",
            actor_id=None,
            client_id=None,
            ip=ip,
            user_agent=user_agent,
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
    request: Request,
) -> TokenResponse:
    """Аутентифицирует пользователя и возвращает access token."""
    ip, user_agent = extract_client_info(request)
    user = await get_user_by_email(session, str(credentials.email))
    if user is None:
        await write_event(
            session,
            event_type="user.login.failure",
            actor_id=None,
            client_id=None,
            ip=ip,
            user_agent=user_agent,
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
        await write_event(
            session,
            event_type="user.login.failure",
            actor_id=user.id,
            client_id=None,
            ip=ip,
            user_agent=user_agent,
            metadata={"email": str(credentials.email)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные данные для входа.",
        )

    access_token = create_access_token(user.id)
    await write_event(
        session,
        event_type="user.login.success",
        actor_id=user.id,
        client_id=None,
        ip=ip,
        user_agent=user_agent,
        metadata={"email": str(credentials.email)},
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def get_current_profile(current_user: CurrentUser) -> UserRead:
    """Возвращает данные текущего пользователя."""
    return UserRead.model_validate(current_user)
