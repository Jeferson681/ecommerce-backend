"""Product router."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from backend.app.modules.auth.deps import require_admin
from backend.app.modules.product.schemas import (
    ProductCreate,
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


@router.get("", response_model=list[ProductRead])
def list_products_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    q: Annotated[str | None, Query(min_length=1)] = None,
    category: Annotated[str | None, Query(min_length=1)] = None,
    sort: Annotated[
        Literal["price_asc", "price_desc", "newest"] | None,
        Query(),
    ] = None,
    page: Annotated[int | None, Query(ge=1)] = None,
    per_page: Annotated[int | None, Query(ge=1, le=100)] = None,
) -> list[ProductRead]:
    """Endpoint to list products. Supports optional pagination via `page` and `per_page` query params."""
    return list_products(
        uow,
        page=page,
        per_page=per_page,
        query=q,
        category=category,
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
    try:
        return create_product(product_data, uow)

    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error while creating product.",
        ) from e


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
    try:
        return update_product(product_id, product_data, uow)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error while updating product.",
        ) from e


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_endpoint(
    product_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _admin_id: Annotated[int, Depends(require_admin)],
) -> None:
    """Remove or deactivate a product.

    Access: admin only.
    """
    try:
        delete_product(product_id, uow)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product cannot be deleted because it has associated orders.",
        ) from e
