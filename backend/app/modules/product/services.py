"""Services for product management."""

from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.product.domain.models import Product
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)
from backend.app.modules.product.schemas import (
    ProductCreate,
    ProductPage,
    ProductRead,
    ProductUpdate,
)
from backend.app.uow.unit_of_work import UnitOfWork

DEFAULT_PRODUCTS_PER_PAGE = 24


def create_product(product_data: ProductCreate, uow: UnitOfWork) -> ProductRead:
    product = Product(
        name=product_data.name,
        description=product_data.description,
        category=product_data.category,
        image_url=product_data.image_url,
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
    min_price: float | None = None,
    max_price: float | None = None,
    sort: str | None = None,
) -> list[ProductRead] | ProductPage:
    """List products with optional filtering, sorting and pagination.

    All filters (`query`, `category`, `min_price`, `max_price`) are applied
    before counting, so the envelope metadata always reflects the filtered
    set. When `page` and/or `per_page` are provided a paginated envelope with
    metadata (total, page, per_page, total_pages) is returned. The missing
    parameter defaults to page=1 and per_page=24. Otherwise the full list is
    returned, preserving the non-paginated contract.
    """
    repository = ProductRepository(uow.session)

    if page is not None or per_page is not None:
        resolved_page = page if page is not None else 1
        resolved_per_page = (
            per_page if per_page is not None else DEFAULT_PRODUCTS_PER_PAGE
        )
        # convert to zero-based offset
        offset = (resolved_page - 1) * resolved_per_page
        products = repository.list(
            offset=offset,
            limit=resolved_per_page,
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
        )
        total = repository.count(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
        )
        total_pages = (
            (total + resolved_per_page - 1) // resolved_per_page if total else 0
        )
        return ProductPage(
            items=[ProductRead.model_validate(product) for product in products],
            total=total,
            page=resolved_page,
            per_page=resolved_per_page,
            total_pages=total_pages,
        )

    products = repository.list(
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
    )

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
