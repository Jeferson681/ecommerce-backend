"""Cart repository for managing cart data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.modules.cart.domain.models import Cart, CartItem


class CartRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, cart: Cart) -> Cart:
        self.session.add(cart)
        self.session.flush()
        self.session.refresh(cart)

        return cart

    def get_by_id(self, cart_id: int) -> Cart | None:
        statement = select(Cart).where(Cart.id == cart_id)

        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def delete(self, cart: Cart) -> None:
        self.session.delete(cart)
        self.session.flush()

    def get_by_user_id(self, user_id: int) -> Cart | None:
        """Return the cart associated with a user."""
        statement = select(Cart).where(Cart.user_id == user_id)

        result = self.session.execute(statement)

        return result.scalar_one_or_none()


class CartItemRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, cart_item_id: int) -> CartItem | None:
        statement = select(CartItem).where(CartItem.id == cart_item_id)

        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def get_by_cart_id(self, cart_id: int) -> list[CartItem]:
        """Return all items belonging to a `cart_id`."""
        statement = select(CartItem).where(CartItem.cart_id == cart_id)

        result = self.session.execute(statement)

        return list(result.scalars().all())

    def create(self, item: CartItem) -> CartItem:
        """Create a new CartItem."""
        self.session.add(item)
        self.session.flush()
        self.session.refresh(item)

        return item

    def update(self, cart_item: CartItem) -> CartItem:
        self.session.flush()
        self.session.refresh(cart_item)

        return cart_item

    def delete(self, cart_item: CartItem) -> None:
        self.session.delete(cart_item)
        self.session.flush()

    def get_by_cart_and_product(self, cart_id: int, product_id: int) -> CartItem | None:
        """Return a `CartItem` by the pair (cart_id, product_id)."""
        statement = select(CartItem).where(
            CartItem.cart_id == cart_id, CartItem.product_id == product_id
        )

        result = self.session.execute(statement)

        return result.scalar_one_or_none()
