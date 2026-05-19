import pytest
from pydantic import ValidationError

from backend.app.modules.product.schemas import ProductCreate, ProductUpdate


@pytest.mark.parametrize(
    "data",
    [
        # name empty
        {"name": "", "description": "d", "price": 1.0, "stock_quantity": 1},
        # name whitespace only (normalized -> empty)
        {"name": "   ", "description": "d", "price": 1.0, "stock_quantity": 1},
        # price zero
        {"name": "p", "description": "d", "price": 0, "stock_quantity": 1},
        # negative price
        {"name": "p", "description": "d", "price": -1.0, "stock_quantity": 1},
        # negative stock
        {"name": "p", "description": "d", "price": 1.0, "stock_quantity": -5},
    ],
)
def test_product_create_invalid(data):
    with pytest.raises(ValidationError):
        ProductCreate(**data)


@pytest.mark.parametrize(
    "data",
    [
        # provided empty name
        {"name": ""},
        # provided whitespace-only name
        {"name": "   "},
        # price zero
        {"price": 0},
        # negative stock
        {"stock_quantity": -1},
        # description too long (>1000)
        {"description": "x" * 1001},
    ],
)
def test_product_update_invalid(data):
    with pytest.raises(ValidationError):
        ProductUpdate(**data)
