from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.user.schemas import UserChangePassword, UserCreate, UserUpdate


@pytest.mark.parametrize(
    "data",
    [
        {"first_name": "", "last_name": "Silva", "email": "a@b.com", "password": "Abcd1234!"},
        {"first_name": "A", "last_name": "Silva", "email": "a@b.com", "password": "Abcd1234!"},
        {"first_name": "Ana", "last_name": "", "email": "a@b.com", "password": "Abcd1234!"},
        {"first_name": "Ana", "last_name": "S", "email": "a@b.com", "password": "Abcd1234!"},
        {"first_name": "Ana", "last_name": "Silva", "email": "not-an-email", "password": "Abcd1234!"},
        {"first_name": "Ana", "last_name": "Silva", "email": "a@b.com", "password": "short"},
    ],
)
def test_user_create_invalid(data: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        UserCreate(**data)


@pytest.mark.parametrize(
    "data",
    [
        {"first_name": ""},
        {"first_name": "A"},
        {"last_name": ""},
        {"email": "invalid-email"},
        {"first_name": " "},
    ],
)
def test_user_update_invalid(data: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        UserUpdate(**data)


@pytest.mark.parametrize("new_password", ["short", "123", ""])
def test_change_password_schema_invalid(new_password: str) -> None:
    with pytest.raises(ValidationError):
        UserChangePassword(new_password=new_password)


def test_user_create_normalizes_fields() -> None:
    data = UserCreate(
        first_name="  Ana  ",
        last_name="  Silva  ",
        email="  ANA@MAIL.COM  ",
        password="Abcd1234!",
    )

    assert data.first_name == "Ana"
    assert data.last_name == "Silva"
    assert data.email == "ana@mail.com"
