import pytest
from pydantic import ValidationError

from user_service.api.schemas import UserCreate


def test_user_create_rejects_empty_username() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="")


def test_user_create_rejects_whitespace_only() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="   ")


def test_user_create_accepts_trimmed_username() -> None:
    u = UserCreate(username="  alice  ")
    assert u.username == "alice"
