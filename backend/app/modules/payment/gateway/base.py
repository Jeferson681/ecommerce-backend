"""Payment gateway abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol

from backend.app.modules.payment.domain.models import PaymentStatus

PaymentMethod = Literal[
    "card",
    "pix",
    "boleto",
]


@dataclass(slots=True)
class PaymentRequest:
    amount: Decimal
    method: PaymentMethod

    # Dados específicos do provedor/meio de pagamento.
    # Ex:
    # Stripe     -> payment_method_id
    # Pix        -> None
    # MercadoPago-> token
    # PayPal     -> payer_id
    provider_data: dict[str, str] | None = None


@dataclass(slots=True)
class PaymentGatewayResult:
    provider_payment_id: str | None
    status: PaymentStatus
    failure_reason: str | None = None
    provider_status: str | None = None
    provider_reference: str | None = None


@dataclass(slots=True)
class PaymentWebhookPayload:
    provider_payment_id: str | None
    status: PaymentStatus
    failure_reason: str | None = None
    provider_status: str | None = None


class PaymentGateway(Protocol):
    """Contract implemented by payment providers."""

    name: str

    def process_payment(
        self,
        *,
        request: PaymentRequest,
        idempotency_key: str | None = None,
    ) -> PaymentGatewayResult:
        """Process a payment through an external provider."""
        ...

    def process_webhook(
        self,
        *,
        payload_bytes: bytes,
        signature: str | None = None,
    ) -> PaymentWebhookPayload:
        """Process a webhook callback from the provider."""
        ...
