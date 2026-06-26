from decimal import Decimal

from backend.app.modules.payment.domain.models import Payment
from backend.app.modules.payment.gateway.base import (
    PaymentGateway,
    PaymentGatewayResult,
    PaymentRequest,
    PaymentWebhookPayload,
)


def build_payment_request(
    amount: Decimal,
    payment_method_id: str,
) -> PaymentRequest:
    return PaymentRequest(
        amount=amount,
        method="card",
        provider_data={
            "payment_method_id": payment_method_id,
        },
    )


def process_gateway_payment(
    gateway: PaymentGateway,
    request: PaymentRequest,
    idempotency_key: str | None = None,
) -> PaymentGatewayResult:
    return gateway.process_payment(
        request=request,
        idempotency_key=idempotency_key,
    )


def process_gateway_webhook(
    gateway: PaymentGateway,
    payload_bytes: bytes,
    signature: str | None = None,
) -> PaymentWebhookPayload:
    return gateway.process_webhook(
        payload_bytes=payload_bytes,
        signature=signature,
    )


def apply_gateway_result(
    payment: Payment,
    gateway_result: PaymentGatewayResult,
) -> None:
    payment.provider_payment_id = gateway_result.provider_payment_id
    payment.provider_status = gateway_result.provider_status
    payment.provider_reference = gateway_result.provider_reference
    payment.failure_reason = gateway_result.failure_reason
    payment.status = gateway_result.status
