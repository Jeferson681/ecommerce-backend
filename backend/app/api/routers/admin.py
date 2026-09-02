"""Admin-only API router.

Responsibility: expose administrative endpoints for platform-wide operations.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.modules.auth.deps import require_admin
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.order.services import list_all_orders
from backend.app.modules.payment.schemas import PaymentRead
from backend.app.modules.payment.services import list_all_payments
from backend.app.uow.dependencies import get_uow
from backend.app.uow.unit_of_work import UnitOfWork

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/orders")
def list_all_orders_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _admin_id: Annotated[int, Depends(require_admin)],
) -> list[OrderRead]:
    """List all orders across the platform.

    Access: admin only.
    """
    return list_all_orders(uow)


@router.get("/payments")
def list_all_payments_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _admin_id: Annotated[int, Depends(require_admin)],
) -> list[PaymentRead]:
    """List all payments across the platform.

    Access: admin only.
    """
    return list_all_payments(uow)
