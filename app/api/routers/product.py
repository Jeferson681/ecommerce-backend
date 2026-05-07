"""Product router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_uow
from app.application.uow.unit_of_work import UnitOfWork
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
        product = create_product(product_data, uow)
        return ProductRead.model_validate(product)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error while creating product.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        ) from e


@router.get("/{product_id}", response_model=ProductRead)
def get_product_endpoint(
    product_id: int, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> ProductRead:
    """Endpoint to retrieve a product by its ID."""
    product = get_product(product_id, uow)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    return ProductRead.model_validate(product)


@router.get("", response_model=list[ProductRead])
def list_products_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[ProductRead]:
    """Endpoint to list all products."""
    products = list_products(uow)
    return [ProductRead.model_validate(product) for product in products]


@router.patch("/{product_id}", response_model=ProductRead)
def update_product_endpoint(
    product_id: int,
    product_data: ProductUpdate,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ProductRead:
    """Endpoint to update an existing product."""
    try:
        product = update_product(product_id, product_data, uow)
        return ProductRead.model_validate(product)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error while updating product.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        ) from e


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_endpoint(
    product_id: int, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> None:
    """Endpoint to delete a product."""
    try:
        delete_product(product_id, uow)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error while deleting product.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        ) from e
