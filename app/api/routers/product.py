"""Product router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.application.uow.dependencies import get_uow
from app.application.uow.unit_of_work import UnitOfWork
from app.core.exceptions import Messages, NotFoundError
from app.modules.product.schemas import ProductCreate, ProductRead, ProductUpdate
from app.modules.product.use_cases import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product_endpoint(
    product_data: ProductCreate, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> ProductRead:
    """Endpoint to create a new product."""
    try:
        return create_product(product_data, uow)

    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error while creating product.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_SERVER_ERROR,
        ) from e


@router.get("/{product_id}", response_model=ProductRead)
def get_product_endpoint(
    product_id: int, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> ProductRead:
    """Endpoint to retrieve a product by its ID."""
    product = get_product(product_id, uow)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=Messages.PRODUCT_NOT_FOUND
        )

    return product


@router.get("", response_model=list[ProductRead])
def list_products_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[ProductRead]:
    """Endpoint to list all products."""
    return list_products(uow)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product_endpoint(
    product_id: int,
    product_data: ProductUpdate,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ProductRead:
    """Endpoint to update an existing product."""
    try:
        return update_product(product_id, product_data, uow)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error while updating product.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_SERVER_ERROR,
        ) from e


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_endpoint(
    product_id: int, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> None:
    """Endpoint to delete a product."""
    try:
        delete_product(product_id, uow)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error while deleting product.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_SERVER_ERROR,
        ) from e
