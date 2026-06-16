"""Payment Schemas"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    user_id: int
    amount: Decimal
    status: str
    provider: str
    provider_payment_id: str | None = None
    provider_status: str | None = None
    provider_reference: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime
