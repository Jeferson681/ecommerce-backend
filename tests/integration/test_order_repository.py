from __future__ import annotations

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.database import Base
from backend.app.modules.order.domain.models import Order, OrderItem
from backend.app.modules.order.repositories.order_repository import (
    OrderItemRepository,
    OrderRepository,
)
from backend.app.modules.product.domain.models import Product

ENGINE = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, future=True
)
SessionLocal = sessionmaker(bind=ENGINE, future=True)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=ENGINE)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=ENGINE)


def _create_product(session: Session, name: str = "Produto 1") -> Product:
    product = Product(
        name=name, description="d", price=Decimal("10.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def test_order_repository_crud_flow() -> None:
    session = SessionLocal()
    order_repo = OrderRepository(session)
    item_repo = OrderItemRepository(session)

    order = Order(user_id=1)
    order_repo.create(order)
    session.commit()

    fetched = order_repo.get_by_id(order.id)
    assert fetched is not None
    assert fetched.user_id == 1

    fetched_by_user = order_repo.get_by_user_id(1)
    assert fetched_by_user is not None
    assert isinstance(fetched_by_user, list)
    assert fetched_by_user[0].id == order.id

    product = _create_product(session)

    item = OrderItem(
        order_id=order.id, product_id=product.id, quantity=2, price=Decimal("10.00")
    )
    item_repo.create(item)
    session.commit()

    fetched_item = item_repo.get_by_id(item.id)
    assert fetched_item is not None
    assert fetched_item.quantity == 2

    fetched_items = item_repo.get_by_order_id(order.id)
    assert len(fetched_items) == 1

    item.quantity = 4
    item_repo.create(item)
    session.commit()

    updated = item_repo.get_by_id(item.id)
    assert updated is not None
    assert updated.quantity == 4

    item_repo.delete(item)
    session.commit()

    deleted = item_repo.get_by_id(item.id)
    assert deleted is None

    order_repo.delete(order)
    session.commit()

    deleted_order = order_repo.get_by_id(order.id)
    assert deleted_order is None
