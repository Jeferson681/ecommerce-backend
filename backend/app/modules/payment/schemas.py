"""Payment Schemas"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    order_id: int = Field(..., gt=0)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    user_id: int
    amount: Decimal
    status: str
    provider: str
    provider_payment_id: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime
