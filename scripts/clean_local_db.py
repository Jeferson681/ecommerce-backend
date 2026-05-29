"""
Cleans test data from local SQLite database.

Safety: this script will refuse to run if the configured DATABASE_URL is not a local SQLite file.
It deletes users matching common test patterns and seeded products.
"""

import os
import sys

# Adiciona a raiz do projeto ao sys.path ANTES dos imports do backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import or_

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.modules.product.domain.models import Product
from backend.app.modules.user.domain.models import User


def main() -> None:
    db_url = settings.DATABASE_URL
    print(f"Configured DATABASE_URL={db_url}")

    if not db_url.startswith("sqlite"):
        raise SystemExit("Refusing to run: DATABASE_URL is not a sqlite local DB")

    # extra safety: require local file path
    if ":memory:" in db_url or db_url.count("/") < 1:
        raise SystemExit("Refusing to run against in-memory or ambiguous sqlite URL")

    session = SessionLocal()
    try:
        # Users to delete: emails containing '+' (user+123@example.com), emails ending with @example.com,
        # and first_names used in smoke scripts like 'User' or 'Hdr'.
        q = session.query(User).filter(
            or_(
                User.email.ilike("%+%@%"),
                User.email.ilike("%@example.com"),
                User.first_name.in_(["User", "Hdr"]),
            )
        )

        users_to_delete = q.all()
        print(f"Found {len(users_to_delete)} user(s) matching test patterns.")
        for u in users_to_delete:
            print(f"Deleting user id={u.id} email={u.email}")
            session.delete(u)

        # Products seeded earlier
        seed_names = [
            "Wireless Mouse",
            "Mechanical Keyboard",
            "USB-C Charger",
            "Bluetooth Speaker",
            "Webcam Full HD",
            "Laptop Stand",
            "Gaming Headset",
            "Portable SSD 1TB",
            "Ceramic Coffee Mug",
            "Electric Kettle",
            "Desk Lamp",
            "Memory Foam Pillow",
            "Air Fryer",
            "Water Bottle",
            "Storage Basket Set",
            "Basic Cotton T-Shirt",
            "Running Shoes",
            "Classic Hoodie",
            "Leather Wallet",
            "Baseball Cap",
            "Notebook Set",
            "Gel Pen Pack",
            "Monitor Arm",
            "Office Chair",
            "Yoga Mat",
            "Resistance Bands",
            "Protein Shaker Bottle",
            "Gaming Mouse Pad",
            "Controller Charging Dock",
            "Scented Candle",
            "Pet Feeding Bowl",
            "Basic Tee",
            "Coffee Mug",
            "Sticker Pack",
        ]
        pq = session.query(Product).filter(Product.name.in_(seed_names))
        products_to_delete = pq.all()
        print(f"Found {len(products_to_delete)} seed product(s).")
        for p in products_to_delete:
            print(f"Deleting product id={p.id} name={p.name}")
            session.delete(p)

        session.commit()
        print("Cleanup committed.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
