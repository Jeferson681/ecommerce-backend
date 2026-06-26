"""Checkout services.

Responsibility: provide reusable operations for checkout workflows.
"""

from backend.app.core.exceptions import Messages, ValidationError
from backend.app.modules.cart.domain.models import CartItem
from backend.app.modules.product.domain.models import Product
from backend.app.modules.product.services import get_product_or_raise


def validate_stock_and_build_product_map(
    cart_items: list[CartItem],
    product_repository,
) -> dict[int, Product]:
    product_map: dict[int, Product] = {}

    for cart_item in cart_items:
        product = get_product_or_raise(product_repository, cart_item.product_id)

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
