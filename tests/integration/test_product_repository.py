from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.database import Base
from backend.app.modules.product.domain.models import Product
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)

SessionLocal: sessionmaker[Session]


def setup_module(module):
    # create an in-memory sqlite for tests
    module.engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=module.engine)
    global SessionLocal
    SessionLocal = sessionmaker(bind=module.engine, future=True)


def teardown_module(module):
    Base.metadata.drop_all(bind=module.engine)


def test_create_and_get_and_list_and_delete():
    session = SessionLocal()
    repo = ProductRepository(session)

    p = Product(name="t", description="d", price=Decimal("1.0"))
    repo.create(p)
    session.commit()

    fetched = repo.get_by_id(p.id)
    assert fetched is not None

    all_products = repo.list()
    assert len(all_products) >= 1

    # update
    p.name = "updated"
    repo.update(p)
    session.commit()

    updated = repo.get_by_id(p.id)
    assert updated is not None
    assert updated.name == "updated"

    # delete
    repo.delete(p)
    session.commit()

    deleted = repo.get_by_id(p.id)
    assert deleted is None
