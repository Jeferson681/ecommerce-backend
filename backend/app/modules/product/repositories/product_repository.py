"""Product repository for managing product data."""

from sqlalchemy import select
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

    def list(self) -> list[Product]:
        statement = select(Product).order_by(Product.id)

        result = self.session.execute(statement)
        return list(result.scalars().all())

    def update(self, product: Product) -> Product:
        self.session.add(product)
        self.session.flush()

        return product

    def delete(self, product: Product) -> None:
        self.session.delete(product)
        self.session.flush()
