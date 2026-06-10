"""Product repository for managing product data."""

from sqlalchemy import desc, or_, select, update as sa_update
from sqlalchemy.orm import Session

from backend.app.modules.product.domain.models import Product


class ProductRepository:
    """Repository for managing product data."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, product: Product) -> Product:
        self.session.add(product)
        self.session.flush()

        return product

    def get_by_id(self, product_id: int) -> Product | None:
        statement = select(Product).where(Product.id == product_id)

        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def list(
        self,
        offset: int | None = None,
        limit: int | None = None,
        query: str | None = None,
        category: str | None = None,
        sort: str | None = None,
    ) -> list[Product]:
        """Return products optionally filtered, sorted and paginated.

        If `offset`/`limit` are None the full list is returned.
        """
        statement = select(Product)

        if query:
            query_value = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    Product.name.ilike(query_value),
                    Product.description.ilike(query_value),
                )
            )

        if category:
            statement = statement.where(Product.category == category.strip())

        if sort == "price_asc":
            statement = statement.order_by(Product.price.asc(), Product.id.asc())
        elif sort == "price_desc":
            statement = statement.order_by(desc(Product.price), Product.id.asc())
        elif sort == "newest":
            statement = statement.order_by(desc(Product.created_at), desc(Product.id))
        else:
            statement = statement.order_by(Product.id)

        if offset is not None:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)

        result = self.session.execute(statement)
        return list(result.scalars().all())

    def delete(self, product: Product) -> None:
        self.session.delete(product)
        self.session.flush()

    def decrement_stock_if_enough(self, product_id: int, quantity: int) -> bool:
        """Atomically decrement stock if enough quantity exists.

        Returns True if the stock was decremented, False otherwise.
        """
        stmt = (
            sa_update(Product)
            .where(Product.id == product_id, Product.stock_quantity >= quantity)
            .values(stock_quantity=Product.stock_quantity - quantity)
            .returning(Product.stock_quantity)
        )

        result = self.session.execute(stmt)
        row = result.fetchone()
        # No row returned -> condition not met (insufficient stock)
        return row is not None
