import os
import sys
from decimal import Decimal

# Ajusta o path para reconhecer o módulo 'backend'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.modules.product.domain.models import Product


def seed_products():
    print("Iniciando persistência direta no SQLite (ecommerce.db)...")

    # Mostrar qual DATABASE_URL está sendo usada e o caminho real do arquivo SQLite
    print(f"DATABASE_URL usada: {settings.DATABASE_URL}")
    if settings.DATABASE_URL.startswith("sqlite"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        print(f"Caminho absoluto do DB: {Path(db_path).resolve()}")

    # Garante que as tabelas existam
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    products_data = [
        {
            "name": "Wireless Mouse",
            "description": "Ergonomic wireless mouse.",
            "price": 24.90,
            "stock_quantity": 120,
        },
        {
            "name": "Mechanical Keyboard",
            "description": "Compact mechanical keyboard with RGB.",
            "price": 79.90,
            "stock_quantity": 60,
        },
        {
            "name": "USB-C Charger",
            "description": "Fast charging USB-C wall adapter.",
            "price": 18.50,
            "stock_quantity": 200,
        },
        {
            "name": "Bluetooth Speaker",
            "description": "Portable Bluetooth speaker.",
            "price": 49.90,
            "stock_quantity": 80,
        },
        {
            "name": "Webcam Full HD",
            "description": "1080p webcam with built-in microphone.",
            "price": 39.90,
            "stock_quantity": 45,
        },
        {
            "name": "Laptop Stand",
            "description": "Adjustable aluminum laptop stand.",
            "price": 32.00,
            "stock_quantity": 90,
        },
        {
            "name": "Gaming Headset",
            "description": "Over-ear gaming headset.",
            "price": 69.90,
            "stock_quantity": 55,
        },
        {
            "name": "Portable SSD 1TB",
            "description": "High-speed external SSD.",
            "price": 119.90,
            "stock_quantity": 35,
        },
    ]

    try:
        # Opcional: Limpar produtos existentes para evitar duplicatas
        # db.query(Product).delete()

        for item in products_data:
            product = Product(
                name=item["name"],
                description=item["description"],
                price=Decimal(str(item["price"])),
                stock_quantity=item["stock_quantity"],
            )
            db.add(product)

        db.commit()
        print(f"Sucesso! {len(products_data)} produtos persistidos em ecommerce.db")
    except Exception as e:
        db.rollback()
        print(f"Erro ao semear o banco: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_products()
