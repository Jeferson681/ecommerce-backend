"""Product schemas for API requests and responses."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    price: Decimal = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    description: str | None = None
    price: Decimal | None = Field(None, gt=0)
    stock_quantity: int | None = Field(None, ge=0)
    is_active: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
