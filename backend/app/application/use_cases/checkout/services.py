"""Checkout services.

Responsibility: provide reusable operations for checkout workflows.
"""

from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.cart.domain.models import CartItem
from backend.app.modules.product.domain.models import Product
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)


def validate_stock_and_build_product_map(
    cart_items: list[CartItem],
    repository: ProductRepository,
) -> dict[int, Product]:
    product_map: dict[int, Product] = {}

    for cart_item in cart_items:
        product = repository.get_by_id(cart_item.product_id)

        if product is None:
            raise NotFoundError(Messages.PRODUCT_NOT_FOUND)

        if not product.is_active:
            raise ValidationError(
                f"{Messages.PRODUCT_NOT_FOUND} (product_id={cart_item.product_id})"
            )

        if product.stock_quantity < cart_item.quantity:
            raise ValidationError(
                f"{Messages.ORDER_INSUFFICIENT_STOCK} "
                f"(product_id={cart_item.product_id})"
            )

        product_map[cart_item.product_id] = product

    return product_map
