"""Payment provider webhooks router.

Separated router to keep provider callbacks distinct from public API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status

from backend.app.application.use_cases.webhook.payment_webhook import (
    process_provider_webhook,
)
from backend.app.modules.payment.gateway.base import PaymentGateway
from backend.app.uow.dependencies import get_payment_gateway, get_uow
from backend.app.uow.unit_of_work import UnitOfWork

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook_endpoint(
    request: Request,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    gateway: Annotated[PaymentGateway, Depends(get_payment_gateway)],
    stripe_sig: Annotated[
        str | None,
        Header(alias="Stripe-Signature"),
    ] = None,
) -> dict[str, bool]:
    process_provider_webhook(
        gateway=gateway,
        payload_bytes=await request.body(),
        signature=stripe_sig,
        uow=uow,
    )

    return {"received": True}
