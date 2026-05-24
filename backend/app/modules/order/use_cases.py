"""Order use cases.

Responsibility: coordinate checkout and order retrieval workflows.
"""

from sqlalchemy.exc import IntegrityError

from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.cart.repositories.cart_repository import (
    CartItemRepository,
    CartRepository,
)
from backend.app.modules.order.domain.models import Order, OrderItem
from backend.app.modules.order.repositories.order_repository import (
    OrderItemRepository,
    OrderRepository,
)
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)
from backend.app.modules.user.repositories.user_repository import UserRepository


def checkout(user_id: int, uow: UnitOfWork) -> OrderRead:
    """Complete a checkout for the authenticated user.

    1. Retrieve the user's cart items.
    2. Validate stock availability for each product.
    3. Create an Order with OrderItems.
    4. Decrease stock quantities.
    5. Clear the cart.
    """
    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)
    product_repository = ProductRepository(uow.session)
    order_repository = OrderRepository(uow.session)
    order_item_repository = OrderItemRepository(uow.session)

    # Validate cart exists and has items
    cart = cart_repository.get_by_user_id(user_id)
    if cart is None:
        raise NotFoundError(Messages.CART_NOT_FOUND)

    cart_items = cart_item_repository.get_by_cart_id(cart.id)
    if not cart_items:
        raise ValidationError(Messages.ORDER_CART_EMPTY)

    # Validate stock and calculate total
    product_map = {}
    for cart_item in cart_items:
        product = product_repository.get_by_id(cart_item.product_id)
        if product is None:
            raise NotFoundError(Messages.PRODUCT_NOT_FOUND)
        if product.stock_quantity < cart_item.quantity:
            raise ValidationError(
                f"{Messages.ORDER_INSUFFICIENT_STOCK} "
                f"(product_id={cart_item.product_id})"
            )
        product_map[cart_item.product_id] = product

    # Create the order
    try:
        order = Order(user_id=user_id)
        order = order_repository.create(order)

        # Create order items and decrement stock
        for cart_item in cart_items:
            product = product_map[cart_item.product_id]
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=product.price,
            )
            order_item_repository.create(order_item)

            # Decrease stock atomically via repository helper. If it fails,
            # raise a ValidationError to abort the transaction.
            success = product_repository.decrement_stock_if_enough(
                product.id, cart_item.quantity
            )
            if not success:
                raise ValidationError(
                    f"{Messages.ORDER_INSUFFICIENT_STOCK} (product_id={cart_item.product_id})"
                )

        # Clear the cart
        cart_repository.delete(cart)

        uow.commit()

    except IntegrityError:
        uow.rollback()
        raise

    except Exception:
        uow.rollback()
        raise

    # Refresh order to load relationships
    refreshed = order_repository.get_by_id(order.id)
    if refreshed is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    return OrderRead.model_validate(refreshed)


def get_order(
    order_id: int, user_id: int, uow: UnitOfWork, requesting_user_id: int | None = None
) -> OrderRead:
    """Retrieve a single order by ID, scoped to the authenticated user.

    Access: owner or admin.
    When `requesting_user_id` is provided, determines admin status internally.
    """
    repository = OrderRepository(uow.session)
    order = repository.get_by_id(order_id)

    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    # Determine if requesting user is the owner or an admin
    is_owner = order.user_id == user_id
    is_admin = False

    if not is_owner and requesting_user_id is not None:
        user_repo = UserRepository(uow.session)
        requester = user_repo.get_by_id(requesting_user_id)
        is_admin = requester is not None and requester.role == "admin"

    if not is_owner and not is_admin:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    return OrderRead.model_validate(order)


def list_orders(user_id: int, uow: UnitOfWork) -> list[OrderRead]:
    """List all orders for the authenticated user."""
    repository = OrderRepository(uow.session)
    orders = repository.get_by_user_id(user_id)

    return [OrderRead.model_validate(order) for order in orders]
