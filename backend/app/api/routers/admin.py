"""Admin-only API router.

Responsibility: expose administrative endpoints for platform-wide operations.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.modules.auth.deps import require_admin
from backend.app.modules.order.repositories.order_repository import OrderRepository
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.modules.payment.schemas import PaymentRead
from backend.app.uow.dependencies import get_uow
from backend.app.uow.unit_of_work import UnitOfWork

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/orders", response_model=list[OrderRead])
def list_all_orders_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _admin_id: Annotated[int, Depends(require_admin)],
) -> list[OrderRead]:
    """List all orders across the platform.

    Access: admin only.
    """
    repository = OrderRepository(uow.session)
    orders = repository.list()
    return [OrderRead.model_validate(order) for order in orders]


@router.get("/payments", response_model=list[PaymentRead])
def list_all_payments_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _admin_id: Annotated[int, Depends(require_admin)],
) -> list[PaymentRead]:
    """List all payments across the platform.

    Access: admin only.
    """
    repository = PaymentRepository(uow.session)
    payments = repository.list()
    return [PaymentRead.model_validate(payment) for payment in payments]
