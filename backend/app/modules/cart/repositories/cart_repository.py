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

    def get_or_create_by_user(self, user_id: int) -> Cart:
        """Return the cart associated with a user, creating a new one if it doesn't exist."""
        cart = self.get_by_user_id(user_id)

        if cart:
            return cart

        cart = Cart(user_id=user_id)
        self.session.add(cart)
        self.session.flush()
        self.session.refresh(cart)

        return cart


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

    def update(self, cart_item: CartItem) -> CartItem:
        self.session.add(cart_item)
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

    def add_or_increment(
        self, cart_id: int, product_id: int, quantity: int = 1
    ) -> CartItem:
        """Add an item to the cart or increment its quantity if it already exists."""
        cart_item = self.get_by_cart_and_product(cart_id, product_id)

        if cart_item:
            cart_item.quantity += quantity
            self.session.add(cart_item)
            self.session.flush()
            self.session.refresh(cart_item)
            return cart_item

        cart_item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
        self.session.add(cart_item)
        self.session.flush()
        self.session.refresh(cart_item)

        return cart_item
