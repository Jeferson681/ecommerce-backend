"""Use cases for product management."""

from app.application.uow.unit_of_work import UnitOfWork
from app.core.exceptions import Messages, NotFoundError
from app.modules.product.domain.models import Product
from app.modules.product.repositories.product_repository import ProductRepository
from app.modules.product.schemas import ProductCreate, ProductRead, ProductUpdate


def create_product(product_data: ProductCreate, uow: UnitOfWork) -> ProductRead:
    product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock_quantity=product_data.stock_quantity,
    )

    repository = ProductRepository(uow.session)

    try:
        repository.create(product)
        uow.commit()
    except Exception:
        uow.rollback()
        raise

    return ProductRead.model_validate(product)


def get_product(product_id: int, uow: UnitOfWork) -> ProductRead | None:
    """Retrieve a product by its ID."""
    repository = ProductRepository(uow.session)
    product = repository.get_by_id(product_id)
    return ProductRead.model_validate(product) if product else None


def list_products(uow: UnitOfWork) -> list[ProductRead]:
    """List all products."""
    repository = ProductRepository(uow.session)
    products = repository.list()
    return [ProductRead.model_validate(product) for product in products]


def update_product(
    product_id: int, product_data: ProductUpdate, uow: UnitOfWork
) -> ProductRead:
    """Update an existing product."""
    repository = ProductRepository(uow.session)
    product = repository.get_by_id(product_id)

    if not product:
        raise NotFoundError(Messages.PRODUCT_NOT_FOUND)

    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        uow.commit()
    except Exception:
        uow.rollback()
        raise

    return ProductRead.model_validate(product)


def delete_product(product_id: int, uow: UnitOfWork) -> None:
    """Delete a product by its ID."""
    repository = ProductRepository(uow.session)
    product = repository.get_by_id(product_id)

    if not product:
        raise NotFoundError(Messages.PRODUCT_NOT_FOUND)

    try:
        repository.delete(product)
        uow.commit()
        return None
    except Exception:
        uow.rollback()
        raise
