"""Product schemas for API requests and responses."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = Field(None, min_length=1, max_length=1000)
    category: str | None = Field(None, min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)

    @field_validator("name", "description", "category", mode="before")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    description: str | None = Field(None, min_length=1, max_length=1000)
    category: str | None = Field(None, min_length=1, max_length=100)
    price: Decimal | None = Field(None, gt=0)
    stock_quantity: int | None = Field(None, ge=0)
    is_active: bool | None = None

    @field_validator("name", "description", "category", mode="before")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    category: str | None
    price: Decimal
    stock_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
