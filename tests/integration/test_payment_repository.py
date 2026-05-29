from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.database import Base
from backend.app.modules.order.domain.models import Order, OrderItem
from backend.app.modules.payment.domain.models import Payment
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.modules.product.domain.models import Product
from backend.app.modules.user.domain.models import User

SessionLocal: sessionmaker[Session]


def setup_module(module: object) -> None:
    module.engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=module.engine)
    global SessionLocal
    SessionLocal = sessionmaker(bind=module.engine, future=True)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=module.engine)


def test_payment_repository_crud_flow() -> None:
    session = SessionLocal()

    # create supporting rows: user, product, order
    user = User(first_name="A", last_name="B", email="a@b.com", password_hash="x")
    session.add(user)
    session.commit()
    session.refresh(user)

    product = Product(
        name="p", description="d", price=Decimal("5.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    order = Order(user_id=user.id)
    session.add(order)
    session.commit()
    session.refresh(order)

    item = OrderItem(
        order_id=order.id, product_id=product.id, quantity=1, price=Decimal("5.00")
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    repo = PaymentRepository(session)

    p = Payment(
        order_id=order.id,
        user_id=user.id,
        amount=Decimal("5.00"),
        status="pending",
        provider="stripe",
    )
    repo.create(p)
    session.commit()

    fetched = repo.get_by_id(p.id)
    assert fetched is not None

    all_payments = repo.list()
    assert len(all_payments) >= 1

    # update
    p.status = "approved"
    repo.update(p)
    session.commit()

    updated = repo.get_by_id(p.id)
    assert updated is not None
    assert updated.status == "approved"

    # get by provider_payment_id (none yet) -> None
    assert repo.get_by_provider_payment_id("nope") is None

    # set provider_payment_id and test lookup
    p.provider_payment_id = "pi_123"
    repo.update(p)
    session.commit()

    found = repo.get_by_provider_payment_id("pi_123")
    assert found is not None

    # delete
    repo.delete(p)
    session.commit()

    deleted = repo.get_by_id(p.id)
    assert deleted is None
