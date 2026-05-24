"""Order API router.

Responsibility: expose HTTP endpoints for checkout and order queries.
"""

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from backend.app.application.uow.dependencies import get_uow
from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.auth.deps import get_current_user_id
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.order.use_cases import checkout, get_order, list_orders

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def checkout_endpoint(
    request: Request,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> OrderRead:
    """Complete checkout: convert cart items into an order."""
    try:
        body_bytes = await request.body()
        # compute request hash from method+path+body for determinism
        request_hash = hashlib.sha256()
        request_hash.update(request.method.encode())
        request_hash.update(request.url.path.encode())
        request_hash.update(body_bytes)
        rh = request_hash.hexdigest()

        return checkout(user_id, uow, idempotency_key=idempotency_key, request_hash=rh)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_SERVER_ERROR,
        ) from e


@router.get("", response_model=list[OrderRead])
def list_orders_endpoint(
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[OrderRead]:
    """List all orders for the authenticated user."""
    try:
        return list_orders(user_id, uow)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_SERVER_ERROR,
        ) from e


@router.get("/{order_id}", response_model=OrderRead)
def get_order_endpoint(
    order_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OrderRead:
    """Return details of a specific order.

    Access: owner or admin (enforced in use case).
    """
    try:
        return get_order(order_id, user_id, uow, requesting_user_id=user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_SERVER_ERROR,
        ) from e
