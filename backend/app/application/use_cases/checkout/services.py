"""Checkout services.

Responsibility: provide reusable operations for checkout workflows.
"""

from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.cart.domain.models import Cart, CartItem
from backend.app.modules.cart.repositories.cart_repository import (
    CartItemRepository,
    CartRepository,
)
from backend.app.modules.order.domain.models import Order, OrderItem
from backend.app.modules.order.repositories.order_repository import (
    OrderItemRepository,
    OrderRepository,
)
from backend.app.modules.product.domain.models import Product
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)


def get_cart_or_raise(
    repository: CartRepository,
    user_id: int,
) -> Cart:
    cart = repository.get_by_user_id(user_id)

    if cart is None:
        raise NotFoundError(Messages.CART_NOT_FOUND)

    return cart


def get_cart_items_or_raise(
    repository: CartItemRepository,
    cart_id: int,
) -> list[CartItem]:
    cart_items = repository.get_by_cart_id(cart_id)

    if not cart_items:
        raise ValidationError(Messages.ORDER_CART_EMPTY)

    return cart_items


def validate_stock_and_build_product_map(
    cart_items: list[CartItem],
    repository: ProductRepository,
) -> dict[int, Product]:
    product_map: dict[int, Product] = {}

    for cart_item in cart_items:
        product = repository.get_by_id(cart_item.product_id)

        if product is None:
            raise NotFoundError(Messages.PRODUCT_NOT_FOUND)

        if product.stock_quantity < cart_item.quantity:
            raise ValidationError(
                f"{Messages.ORDER_INSUFFICIENT_STOCK} "
                f"(product_id={cart_item.product_id})"
            )

        product_map[cart_item.product_id] = product

    return product_map


def create_order_from_cart(
    cart_items: list[CartItem],
    product_map: dict[int, Product],
    order_repository: OrderRepository,
    order_item_repository: OrderItemRepository,
    product_repository: ProductRepository,
    user_id: int,
) -> Order:
    order = order_repository.create(Order(user_id=user_id))

    for cart_item in cart_items:
        product = product_map[cart_item.product_id]

        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=product.price,
        )

        order.items.append(order_item)

        order_item_repository.create(order_item)

        success = product_repository.decrement_stock_if_enough(
            product.id,
            cart_item.quantity,
        )

        if not success:
            raise ValidationError(
                f"{Messages.ORDER_INSUFFICIENT_STOCK} "
                f"(product_id={cart_item.product_id})"
            )

    return order


def clear_cart(
    repository: CartRepository,
    cart: Cart,
) -> None:
    repository.delete(cart)
