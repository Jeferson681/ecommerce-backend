"""Order schemas for request and response contracts.

Responsibility: declare request and response contracts for the order module.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: int
    quantity: int
    price: Decimal
    created_at: datetime
    updated_at: datetime


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = Field(default_factory=list)


class PaymentMethodRequest(BaseModel):
    """Checkout request body.

    Frontend sends payment_method_id obtained from Stripe Elements.
    The backend never receives raw card data.
    """

    payment_method_id: str
