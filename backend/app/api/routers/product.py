"""Product router."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status

from backend.app.modules.auth.deps import require_admin
from backend.app.modules.product.schemas import (
    ProductCreate,
    ProductPage,
    ProductRead,
    ProductUpdate,
)
from backend.app.modules.product.services import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)
from backend.app.uow.dependencies import get_uow
from backend.app.uow.unit_of_work import UnitOfWork

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}", response_model=ProductRead)
def get_product_endpoint(
    product_id: int, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> ProductRead:
    """Endpoint to retrieve a product by its ID."""
    return get_product(product_id, uow)


@router.get("", response_model=list[ProductRead] | ProductPage)
def list_products_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    q: Annotated[str | None, Query(min_length=1)] = None,
    category: Annotated[str | None, Query(min_length=1)] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    sort: Annotated[
        Literal["price_asc", "price_desc", "newest"] | None,
        Query(),
    ] = None,
    page: Annotated[int | None, Query(ge=1)] = None,
    per_page: Annotated[int | None, Query(ge=1, le=100)] = None,
) -> list[ProductRead] | ProductPage:
    """List products.

    Supports filtering via `q`, `category`, `min_price`/`max_price` and
    `sort`. Price filters are applied before counting, so `total` and
    `total_pages` always reflect the filtered set. When `page` and/or
    `per_page` are provided, returns a paginated envelope with metadata
    (`items`, `total`, `page`, `per_page`, `total_pages`); otherwise returns
    the full list.
    """
    return list_products(
        uow,
        page=page,
        per_page=per_page,
        query=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
    )


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product_endpoint(
    product_data: ProductCreate,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _admin_id: Annotated[int, Depends(require_admin)],
) -> ProductRead:
    """Create a new product.

    Access: admin only.
    """
    return create_product(product_data, uow)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product_endpoint(
    product_id: int,
    product_data: ProductUpdate,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _admin_id: Annotated[int, Depends(require_admin)],
) -> ProductRead:
    """Update an existing product.

    Access: admin only.
    """
    return update_product(product_id, product_data, uow)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_endpoint(
    product_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _admin_id: Annotated[int, Depends(require_admin)],
) -> None:
    """Remove or deactivate a product.

    Access: admin only.
    """
    delete_product(product_id, uow)
