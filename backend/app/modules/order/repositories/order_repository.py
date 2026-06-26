"""Order repository for managing order data.

Responsibility: expose persistence operations for order data access.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.modules.order.domain.models import Order, OrderItem


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, order_id: int) -> Order | None:
        statement = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.payments))
        )

        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def list_by_user(self, user_id: int) -> list[Order]:
        statement = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.id)
            .options(selectinload(Order.items), selectinload(Order.payments))
        )

        result = self.session.execute(statement)
        return list(result.scalars().all())

    def list(self) -> list[Order]:
        statement = (
            select(Order)
            .order_by(Order.id)
            .options(selectinload(Order.items), selectinload(Order.payments))
        )

        result = self.session.execute(statement)
        return list(result.scalars().all())

    def create(self, order: Order) -> Order:
        self.session.add(order)
        self.session.flush()
        self.session.refresh(order)

        return order

    def update(self, order: Order) -> Order:
        self.session.flush()
        self.session.refresh(order)

        return order

    def delete(self, order: Order) -> None:
        self.session.delete(order)
        self.session.flush()

    def create_item(self, item: OrderItem) -> OrderItem:
        """Create an order item."""
        self.session.add(item)
        self.session.flush()
        self.session.refresh(item)
        return item
