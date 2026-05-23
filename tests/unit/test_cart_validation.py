import pytest
from pydantic import ValidationError

from backend.app.modules.cart.schemas import CartItemCreate, CartItemUpdate


def test_cart_item_create_invalid_values():
    with pytest.raises(ValidationError):
        CartItemCreate(product_id=0, quantity=1)

    with pytest.raises(ValidationError):
        CartItemCreate(product_id=1, quantity=0)


def test_cart_item_update_invalid():
    with pytest.raises(ValidationError):
        CartItemUpdate(quantity=0)
