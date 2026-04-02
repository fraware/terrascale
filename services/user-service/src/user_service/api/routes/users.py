from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from user_service.api.schemas import UserCreate, UserGetResponse, UserResponse
from user_service.db.session import get_db_session
from user_service.models.user import User

router = APIRouter()
log = structlog.get_logger()


def get_session(request: Request):
    factory = request.app.state.session_factory
    yield from get_db_session(factory)


def get_redis(request: Request):
    return request.app.state.redis


SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    request: Request,
    session: SessionDep,
) -> UserResponse:
    redis_client = get_redis(request)
    settings = request.app.state.settings
    user = User(username=body.username)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        log.warning("user_create_conflict", username=body.username)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Username already exists"},
        ) from None
    session.refresh(user)
    cache_key = f"user:{user.id}"
    redis_client.set(cache_key, user.username, ex=settings.cache_ttl_seconds)
    return UserResponse(id=user.id, username=user.username)


@router.get("/{user_id}", response_model=UserGetResponse)
def get_user(
    user_id: int,
    request: Request,
    session: SessionDep,
) -> UserGetResponse:
    redis_client = get_redis(request)
    settings = request.app.state.settings
    cache_key = f"user:{user_id}"
    cached_name = redis_client.get(cache_key)
    if cached_name is not None:
        return UserGetResponse(id=user_id, username=cached_name, cached=True)

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found"},
        )
    redis_client.set(cache_key, user.username, ex=settings.cache_ttl_seconds)
    return UserGetResponse(id=user_id, username=user.username, cached=False)
