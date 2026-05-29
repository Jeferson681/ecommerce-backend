"""Payment gateway abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol

PaymentStatus = Literal["pending", "approved", "failed", "cancelled", "refunded"]


@dataclass(slots=True)
class PaymentGatewayResult:
    provider_payment_id: str | None
    status: PaymentStatus
    failure_reason: str | None = None


class PaymentGateway(Protocol):
    name: str

    def process_payment(
        self,
        *,
        order_id: int,
        user_id: int,
        amount: Decimal,
        idempotency_key: str | None = None,
    ) -> PaymentGatewayResult: ...
