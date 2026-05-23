from __future__ import annotations

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.database import Base
from backend.app.modules.cart.domain.models import Cart, CartItem
from backend.app.modules.cart.repositories.cart_repository import (
    CartItemRepository,
    CartRepository,
)
from backend.app.modules.product.domain.models import Product

SessionLocal: sessionmaker[Session]


def setup_module(module: object) -> None:
    module.engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=module.engine)
    global SessionLocal
    SessionLocal = sessionmaker(bind=module.engine, future=True)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=module.engine)


def _create_product(session: Session, name: str = "Produto 1") -> Product:
    product = Product(
        name=name, description="d", price=Decimal("10.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def test_cart_repository_crud_flow() -> None:
    session = SessionLocal()
    cart_repo = CartRepository(session)
    item_repo = CartItemRepository(session)

    cart = Cart(user_id=1)
    cart_repo.create(cart)
    session.commit()

    fetched = cart_repo.get_by_id(cart.id)
    assert fetched is not None
    assert fetched.user_id == 1

    fetched_by_user = cart_repo.get_by_user_id(1)
    assert fetched_by_user is not None
    assert fetched_by_user.id == cart.id

    product = _create_product(session)

    item = item_repo.create(
        CartItem(cart_id=cart.id, product_id=product.id, quantity=2)
    )
    session.commit()

    fetched_item = item_repo.get_by_id(item.id)
    assert fetched_item is not None
    assert fetched_item.quantity == 2

    fetched_items = item_repo.get_by_cart_id(cart.id)
    assert len(fetched_items) == 1

    by_pair = item_repo.get_by_cart_and_product(cart.id, product.id)
    assert by_pair is not None
    assert by_pair.product_id == product.id

    item.quantity = 4
    item_repo.update(item)
    session.commit()

    updated = item_repo.get_by_id(item.id)
    assert updated is not None
    assert updated.quantity == 4

    item_repo.delete(item)
    session.commit()

    deleted = item_repo.get_by_id(item.id)
    assert deleted is None

    cart_repo.delete(cart)
    session.commit()

    deleted_cart = cart_repo.get_by_id(cart.id)
    assert deleted_cart is None
