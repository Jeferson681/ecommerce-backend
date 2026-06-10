"""Checkout application services.

Responsibility: orchestrate checkout workflows.
"""

from decimal import Decimal

from backend.app.application.use_cases.checkout.services import (
    clear_cart,
    create_order_from_cart,
    get_cart_items_or_raise,
    validate_stock_and_build_product_map,
)
from backend.app.idempotency.helpers import (
    reserve_idempotency_if_needed,
    validate_idempotency_input,
)
from backend.app.idempotency.repositories import IdempotencyRepository
from backend.app.modules.cart.repositories.cart_repository import (
    CartItemRepository,
    CartRepository,
)
from backend.app.modules.cart.use_cases import get_cart_or_raise
from backend.app.modules.order.domain.models import OrderStatus
from backend.app.modules.order.repositories.order_repository import (
    OrderItemRepository,
    OrderRepository,
)
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.order.use_cases import (
    persist_idempotent_response_if_needed,
    try_order_response_replay,
)
from backend.app.modules.payment.domain.models import PaymentStatus
from backend.app.modules.payment.gateway.base import PaymentGateway
from backend.app.modules.payment.use_cases import (
    create_payment,
    process_payment,
)
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)
from backend.app.uow.unit_of_work import UnitOfWork


def checkout(
    user_id: int,
    payment_method_id: str,
    uow: UnitOfWork,
    *,
    gateway: PaymentGateway,
    idempotency_key: str | None = None,
    request_hash: str | None = None,
) -> OrderRead:
    """Complete checkout for the authenticated user."""

    validate_idempotency_input(idempotency_key, request_hash)

    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)
    product_repository = ProductRepository(uow.session)
    order_repository = OrderRepository(uow.session)
    order_item_repository = OrderItemRepository(uow.session)
    idempotency_repository = IdempotencyRepository(uow.session)

    replay = try_order_response_replay(
        repository=idempotency_repository,
        idempotency_key=idempotency_key,
        user_id=user_id,
    )

    if replay is not None:
        return replay

    cart = get_cart_or_raise(cart_repository, user_id)

    cart_items = get_cart_items_or_raise(
        cart_item_repository,
        cart.id,
    )

    product_map = validate_stock_and_build_product_map(
        cart_items,
        product_repository,
    )

    reserve_idempotency_if_needed(
        repository=idempotency_repository,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        user_id=user_id,
    )

    if idempotency_key is not None:
        uow.commit()

        replay_after_reserve = try_order_response_replay(
            repository=idempotency_repository,
            idempotency_key=idempotency_key,
            user_id=user_id,
        )
        if replay_after_reserve is not None:
            return replay_after_reserve

    order = create_order_from_cart(
        cart_items=cart_items,
        product_map=product_map,
        order_repository=order_repository,
        order_item_repository=order_item_repository,
        product_repository=product_repository,
        user_id=user_id,
    )

    total_amount = sum(
        product_map[item.product_id].price * item.quantity for item in cart_items
    )

    payment = create_payment(
        order_id=order.id,
        user_id=user_id,
        amount=Decimal(str(total_amount)),
        uow=uow,
    )

    payment = process_payment(
        payment_id=payment.id,
        payment_method_id=payment_method_id,
        uow=uow,
        gateway=gateway,
    )

    if payment.status == PaymentStatus.APPROVED:
        order.status = OrderStatus.PAID

    clear_cart(
        cart_repository,
        cart,
    )

    uow.flush()

    persist_idempotent_response_if_needed(
        repository=idempotency_repository,
        order_repository=order_repository,
        order_id=order.id,
        idempotency_key=idempotency_key,
        user_id=user_id,
    )

    uow.commit()
    return OrderRead.model_validate(order)
