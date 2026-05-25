"""Payment API router."""

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from backend.app.application.uow.dependencies import get_uow
from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.exceptions import NotFoundError
from backend.app.modules.auth.deps import get_current_user_id
from backend.app.modules.payment.schemas import PaymentCreate, PaymentRead
from backend.app.modules.payment.use_cases import (
    get_payment,
    process_payment,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def process_payment_endpoint(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    payload: PaymentCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PaymentRead:
    """Process a payment for an order.

    The scaffold keeps idempotency support in place but defers business rules.
    """
    request_hash = hashlib.sha256()
    body_bytes = await request.body()
    request_hash.update(request.method.encode())
    request_hash.update(request.url.path.encode())
    request_hash.update(body_bytes)

    return process_payment(
        payload,
        uow,
        requesting_user_id=user_id,
        idempotency_key=idempotency_key,
        request_hash=request_hash.hexdigest(),
    )


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment_endpoint(
    payment_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> PaymentRead:
    """Return payment details for the current authenticated user."""
    try:
        return get_payment(payment_id, uow, requesting_user_id=user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
