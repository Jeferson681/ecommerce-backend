"""Payment Repository"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.modules.payment.domain.models import Payment


class PaymentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, payment: Payment) -> Payment:
        self.session.add(payment)
        self.session.flush()
        self.session.refresh(payment)

        return payment

    def get_by_id(self, payment_id: int) -> Payment | None:
        statement = select(Payment).where(Payment.id == payment_id)

        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def get_by_order_id(self, order_id: int) -> list[Payment]:
        statement = select(Payment).where(Payment.order_id == order_id)

        result = self.session.execute(statement)
        return list(result.scalars().all())

    def get_by_provider_payment_id(self, provider_payment_id: str) -> Payment | None:
        statement = select(Payment).where(
            Payment.provider_payment_id == provider_payment_id
        )

        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def list(self) -> list[Payment]:
        statement = select(Payment).order_by(Payment.id)

        result = self.session.execute(statement)
        return list(result.scalars().all())

    def update(self, payment: Payment) -> Payment:
        self.session.flush()
        self.session.refresh(payment)

        return payment

    def delete(self, payment: Payment) -> None:
        self.session.delete(payment)
        self.session.flush()
