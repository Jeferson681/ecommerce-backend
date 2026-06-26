"""Services for product management."""

from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.product.domain.models import Product
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)
from backend.app.modules.product.schemas import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from backend.app.uow.unit_of_work import UnitOfWork


def create_product(product_data: ProductCreate, uow: UnitOfWork) -> ProductRead:
    product = Product(
        name=product_data.name,
        description=product_data.description,
        category=product_data.category,
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


def get_product(product_id: int, uow: UnitOfWork) -> ProductRead:
    """Retrieve a product by its ID."""
    product_repository = ProductRepository(uow.session)
    product = get_product_or_raise(product_repository, product_id)

    return ProductRead.model_validate(product)


def list_products(
    uow: UnitOfWork,
    page: int | None = None,
    per_page: int | None = None,
    query: str | None = None,
    category: str | None = None,
    sort: str | None = None,
) -> list[ProductRead]:
    """List products optionally paginated.

    If `page` and `per_page` are provided pagination is applied.
    """
    repository = ProductRepository(uow.session)

    if page is not None and per_page is not None:
        # convert to zero-based offset
        offset = (page - 1) * per_page
        products = repository.list(
            offset=offset,
            limit=per_page,
            query=query,
            category=category,
            sort=sort,
        )
    else:
        products = repository.list(query=query, category=category, sort=sort)

    return [ProductRead.model_validate(product) for product in products]


def update_product(
    product_id: int, product_data: ProductUpdate, uow: UnitOfWork
) -> ProductRead:
    """Update an existing product."""
    product_repository = ProductRepository(uow.session)

    product = get_product_or_raise(product_repository, product_id)

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
    product_repository = ProductRepository(uow.session)
    product = get_product_or_raise(product_repository, product_id)

    try:
        product_repository.delete(product)
        uow.commit()
    except Exception:
        uow.rollback()
        raise


def reserve_stock(
    repository: ProductRepository,
    product_id: int,
    quantity: int,
) -> None:
    """Reserve stock for a product if enough quantity exists."""

    success = repository.decrement_stock_if_enough(
        product_id=product_id, quantity=quantity
    )

    if not success:
        raise ValidationError(f"{Messages.ORDER_INSUFFICIENT_STOCK} ")


def restore_stock(
    repository: ProductRepository,
    product_id: int,
    quantity: int,
) -> None:
    """Restore previously reserved stock for a product."""
    repository.increment_stock(
        product_id=product_id,
        quantity=quantity,
    )


def get_product_or_raise(
    repository: ProductRepository,
    product_id: int,
) -> Product:
    """Retrieve a product or raise NotFoundError if it doesn't exist."""
    product = repository.get_by_id(product_id)
    if not product:
        raise NotFoundError(Messages.PRODUCT_NOT_FOUND)
    return product


def validate_product_for_purchase(
    repository: ProductRepository,
    product_id: int,
    quantity: int,
) -> Product:
    """Validate that a product is active and has enough stock for purchase."""
    product = get_product_or_raise(repository, product_id)

    if not product.is_active:
        raise ValidationError(Messages.PRODUCT_NOT_FOUND)

    if product.stock_quantity < quantity:
        raise ValidationError(
            f"{Messages.ORDER_INSUFFICIENT_STOCK} (product_id={product_id})"
        )
    return product
