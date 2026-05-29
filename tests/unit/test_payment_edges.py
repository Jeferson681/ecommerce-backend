import pytest
from pydantic import ValidationError as PydanticValidationError

from backend.app.modules.payment.schemas import PaymentWebhookPayload


def test_process_provider_webhook_invalid_status_raises() -> None:
    # schema rejects invalid statuses before the use case runs
    with pytest.raises(PydanticValidationError):
        PaymentWebhookPayload(provider_payment_id="pp", status="invalid_status")
