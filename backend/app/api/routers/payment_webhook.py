"""Payment provider webhooks router.

Separated router to keep provider callbacks distinct from public payment
endpoints (security and routing concerns differ).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import ValidationError as PydanticValidationError

from backend.app.application.uow.dependencies import get_uow
from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.config import settings
from backend.app.core.exceptions import NotFoundError
from backend.app.modules.payment.gateway.stripe_gateway import verify_stripe_signature
from backend.app.modules.payment.schemas import PaymentWebhookPayload
from backend.app.modules.payment.use_cases import process_provider_webhook

router = APIRouter(prefix="/payments/webhook", tags=["webhooks", "payments"])


@router.post("", status_code=status.HTTP_200_OK)
async def payment_webhook_endpoint(
    request: Request,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    provider: Annotated[str | None, Header(alias="X-Payment-Provider")] = None,
    stripe_sig: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> dict:
    """Generic payment provider webhook endpoint.

    Expects a JSON body containing at least `provider_payment_id` and `status`.
    In production you should verify provider signatures and authenticate the webhook.
    """
    body_bytes = await request.body()

    # Verify Stripe signature if secret is configured
    try:
        verify_stripe_signature(
            body_bytes, stripe_sig, getattr(settings, "STRIPE_WEBHOOK_SECRET", None)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    # parse json after signature validated
    try:
        payload = PaymentWebhookPayload.model_validate_json(body_bytes)
    except PydanticValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    prov = provider or "stripe"

    try:
        payment = process_provider_webhook(prov, payload, uow)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    return {"id": payment.id, "status": payment.status}
