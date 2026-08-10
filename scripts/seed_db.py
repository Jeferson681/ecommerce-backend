import os
import sys
from decimal import Decimal

# Adjusts the path to recognize the 'backend' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.modules.product.domain.models import Product


def seed_products():
    print("Starting direct persistence in SQLite (ecommerce.db)...")

    # Show which DATABASE_URL is being used and the real path of the SQLite file
    print(f"DATABASE_URL used: {settings.DATABASE_URL}")
    if settings.DATABASE_URL.startswith("sqlite"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        print(f"Absolute DB path: {Path(db_path).resolve()}")

    # Ensures the tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    products_data = [
        {
            "name": "Wireless Mouse",
            "description": "Ergonomic wireless mouse with precise optical tracking.",
            "price": 24.90,
            "stock_quantity": 120,
        },
        {
            "name": "Mechanical Keyboard",
            "description": "Compact mechanical keyboard with RGB backlighting.",
            "price": 79.90,
            "stock_quantity": 60,
        },
        {
            "name": "USB-C Charger",
            "description": "Fast charging USB-C wall adapter for compatible devices.",
            "price": 18.50,
            "stock_quantity": 200,
        },
        {
            "name": "Bluetooth Speaker",
            "description": "Portable Bluetooth speaker with wireless connectivity.",
            "price": 49.90,
            "stock_quantity": 80,
        },
        {
            "name": "Webcam Full HD",
            "description": "1080p webcam with built-in microphone for calls and streaming.",
            "price": 39.90,
            "stock_quantity": 45,
        },
        {
            "name": "Laptop Stand",
            "description": "Adjustable aluminum laptop stand for comfortable desk setups.",
            "price": 32.00,
            "stock_quantity": 90,
        },
        {
            "name": "Gaming Headset",
            "description": "Over-ear gaming headset with integrated microphone.",
            "price": 69.90,
            "stock_quantity": 55,
        },
        {
            "name": "Portable SSD 1TB",
            "description": "High-speed external SSD with 1TB of portable storage.",
            "price": 119.90,
            "stock_quantity": 35,
        },
        {
            "name": "Wireless Earbuds",
            "description": "Compact wireless earbuds with charging case and touch controls.",
            "price": 59.90,
            "stock_quantity": 75,
        },
        {
            "name": "USB-C Hub 7-in-1",
            "description": "Multi-port USB-C hub with HDMI, USB and card reader connectivity.",
            "price": 44.90,
            "stock_quantity": 65,
        },
        {
            "name": '27" QHD Monitor',
            "description": "27-inch QHD monitor with sharp image quality for work and entertainment.",
            "price": 249.90,
            "stock_quantity": 25,
        },
        {
            "name": '24" Full HD Monitor',
            "description": "24-inch Full HD monitor designed for everyday productivity.",
            "price": 149.90,
            "stock_quantity": 40,
        },
        {
            "name": "Mechanical Keyboard 75%",
            "description": "75% mechanical keyboard with hot-swappable switches and RGB lighting.",
            "price": 99.90,
            "stock_quantity": 40,
        },
        {
            "name": "Wireless Gaming Mouse",
            "description": "Low-latency wireless gaming mouse with adjustable DPI.",
            "price": 74.90,
            "stock_quantity": 50,
        },
        {
            "name": "Laptop Backpack",
            "description": "Water-resistant backpack with padded laptop compartment.",
            "price": 54.90,
            "stock_quantity": 70,
        },
        {
            "name": "Power Bank 20,000mAh",
            "description": "High-capacity portable power bank with USB-C charging.",
            "price": 64.90,
            "stock_quantity": 85,
        },
        {
            "name": "Smart LED Desk Lamp",
            "description": "Adjustable LED desk lamp with multiple brightness levels.",
            "price": 39.90,
            "stock_quantity": 60,
        },
        {
            "name": "Wi-Fi 6 Router",
            "description": "Dual-band Wi-Fi 6 router designed for fast and reliable home networks.",
            "price": 129.90,
            "stock_quantity": 30,
        },
        {
            "name": "External HDD 2TB",
            "description": "Portable 2TB external hard drive for backups and file storage.",
            "price": 89.90,
            "stock_quantity": 45,
        },
        {
            "name": "Gaming Controller",
            "description": "Wireless gaming controller compatible with PC and supported devices.",
            "price": 79.90,
            "stock_quantity": 50,
        },
        {
            "name": "USB-C Cable 2m",
            "description": "Durable 2-meter USB-C cable for charging and data transfer.",
            "price": 14.90,
            "stock_quantity": 180,
        },
        {
            "name": "Noise Cancelling Headphones",
            "description": "Over-ear headphones with active noise cancellation and wireless connectivity.",
            "price": 149.90,
            "stock_quantity": 35,
        },
        {
            "name": "1080p Streaming Camera",
            "description": "Full HD camera designed for video calls, streaming and content creation.",
            "price": 89.90,
            "stock_quantity": 30,
        },
        {
            "name": "RGB Gaming Desk Mat",
            "description": "Extended gaming desk mat with RGB edge lighting.",
            "price": 34.90,
            "stock_quantity": 70,
        },
    ]

    try:
        # Optional: Clear existing products to avoid duplicates
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
        print(f"Success! {len(products_data)} products persisted in ecommerce.db")
    except Exception as e:
        db.rollback()
        print(f"Error seeding the database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_products()
