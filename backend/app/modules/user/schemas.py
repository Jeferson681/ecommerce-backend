"""User schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=24)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def normalize_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()


class UserUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    email: EmailStr | None = Field(None, max_length=255)
    is_active: bool | None = None

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.lower().strip()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: str | None = "user"
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserChangePassword(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=24)
