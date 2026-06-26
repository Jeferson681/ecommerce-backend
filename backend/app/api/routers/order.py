"""Order API router.

Responsibility: expose HTTP endpoints for checkout and order queries.
"""

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status

from backend.app.application.use_cases.checkout.checkout import checkout
from backend.app.application.use_cases.retry_payment.retry_payment import retry_payment
from backend.app.modules.auth.deps import get_current_user_id
from backend.app.modules.order.schemas import OrderRead, PaymentMethodRequest
from backend.app.modules.order.services import get_order, list_orders
from backend.app.modules.payment.gateway.base import PaymentGateway
from backend.app.uow.dependencies import get_payment_gateway, get_uow
from backend.app.uow.unit_of_work import UnitOfWork

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def checkout_endpoint(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    gateway: Annotated[PaymentGateway, Depends(get_payment_gateway)],
    body: PaymentMethodRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> OrderRead:
    """Complete checkout: convert cart items into an order."""
    body_bytes = await request.body()
    # compute request hash from method+path+body for determinism
    request_hash = hashlib.sha256()
    request_hash.update(request.method.encode())
    request_hash.update(request.url.path.encode())
    request_hash.update(body_bytes)
    rh = request_hash.hexdigest()

    return checkout(
        user_id,
        body.payment_method_id,
        uow,
        gateway=gateway,
        idempotency_key=idempotency_key,
        request_hash=rh,
    )


@router.post(
    "/{order_id}/retry-payment",
    response_model=OrderRead,
)
async def retry_payment_endpoint(
    request: Request,
    order_id: int,
    payload: PaymentMethodRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    gateway: Annotated[PaymentGateway, Depends(get_payment_gateway)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
):
    body_bytes = await request.body()
    request_hash = hashlib.sha256()
    request_hash.update(request.method.encode())
    request_hash.update(request.url.path.encode())
    request_hash.update(body_bytes)
    rh = request_hash.hexdigest()

    return retry_payment(
        user_id=user_id,
        order_id=order_id,
        payment_method_id=payload.payment_method_id,
        gateway=gateway,
        uow=uow,
        idempotency_key=idempotency_key,
        request_hash=rh,
    )


@router.get("", response_model=list[OrderRead])
def list_orders_endpoint(
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[OrderRead]:
    """List all orders for the authenticated user."""
    return list_orders(user_id, uow)


@router.get("/{order_id}", response_model=OrderRead)
def get_order_endpoint(
    order_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OrderRead:
    """Return details of a specific order.

    Access: owner or admin (enforced in use case).
    """
    return get_order(order_id, user_id, uow)
