from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.infrastructure.db.dependencies import get_db
from backend.app.modules.payment.gateway.base import PaymentGateway
from backend.app.modules.payment.gateway.stripe_gateway import StripeGateway
from backend.app.uow.unit_of_work import UnitOfWork


def get_payment_gateway() -> PaymentGateway:
    return StripeGateway()


def get_uow(
    session: Annotated[Session, Depends(get_db)],
) -> Generator[UnitOfWork]:
    with UnitOfWork(lambda: session) as uow:
        yield uow
