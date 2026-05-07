"""Use cases for product management."""

from app.application.uow.unit_of_work import UnitOfWork
from app.modules.product.domain.models import Product
from app.modules.product.repositories.product_repository import ProductRepository
from app.modules.product.schemas import ProductCreate, ProductUpdate


def create_product(product_data: ProductCreate, uow: UnitOfWork) -> Product:
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

    return product


def get_product(product_id: int, uow: UnitOfWork) -> Product | None:
    """Retrieve a product by its ID."""
    repository = ProductRepository(uow.session)
    return repository.get_by_id(product_id)


def list_products(uow: UnitOfWork) -> list[Product]:
    """List all products."""
    repository = ProductRepository(uow.session)
    return repository.list()


def update_product(
    product_id: int, product_data: ProductUpdate, uow: UnitOfWork
) -> Product:
    """Update an existing product."""
    repository = ProductRepository(uow.session)
    product = repository.get_by_id(product_id)

    if not product:
        raise ValueError("Product not found.")

    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        uow.commit()
    except Exception:
        uow.rollback()
        raise

    return product


def delete_product(product_id: int, uow: UnitOfWork) -> bool:
    """Delete a product by its ID."""
    repository = ProductRepository(uow.session)
    product = repository.get_by_id(product_id)

    if not product:
        raise ValueError("Product not found.")

    try:
        repository.delete(product)
        uow.commit()
        return True
    except Exception:
        uow.rollback()
        raise
