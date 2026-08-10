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
            "description": "Ergonomic wireless mouse with precise optical tracking for comfortable everyday use.",
            "price": 24.99,
            "stock_quantity": 120,
            "image_url": "/products/Wireless_Mouse.png",
        },
        {
            "name": "Mechanical Keyboard",
            "description": "Compact mechanical keyboard with responsive keys and RGB backlighting for work and gaming.",
            "price": 69.99,
            "stock_quantity": 60,
            "image_url": "/products/Mechanical_Keyboard.png",
        },
        {
            "name": "USB-C Charger",
            "description": "Fast-charging USB-C wall adapter designed for compatible phones, tablets, and other devices.",
            "price": 19.99,
            "stock_quantity": 200,
            "image_url": "/products/USB-C_Charger.png",
        },
        {
            "name": "Bluetooth Speaker",
            "description": "Portable Bluetooth speaker with wireless connectivity for music at home or on the go.",
            "price": 49.99,
            "stock_quantity": 80,
            "image_url": "/products/Bluetooth_Speaker.png",
        },
        {
            "name": "Webcam Full HD",
            "description": "1080p webcam with a built-in microphone for video calls, streaming, and online meetings.",
            "price": 39.99,
            "stock_quantity": 45,
            "image_url": "/products/Webcam_Full_HD.png",
        },
        {
            "name": "Laptop Stand",
            "description": "Adjustable aluminum laptop stand designed to improve screen height and desk ergonomics.",
            "price": 49.99,
            "stock_quantity": 90,
            "image_url": "/products/Laptop_Stand.png",
        },
        {
            "name": "Gaming Headset",
            "description": "Over-ear gaming headset with an integrated microphone for immersive audio and voice communication.",
            "price": 59.99,
            "stock_quantity": 55,
            "image_url": "/products/Gaming_Headset.png",
        },
        {
            "name": "Portable SSD 1TB",
            "description": "Portable 1TB external SSD providing fast storage for backups, file transfers, and everyday use.",
            "price": 199.99,
            "stock_quantity": 35,
            "image_url": "/products/Portable_SSD_1TB.png",
        },
        {
            "name": "Wireless Earbuds",
            "description": "Compact wireless earbuds with a charging case and touch controls for convenient everyday listening.",
            "price": 59.99,
            "stock_quantity": 75,
            "image_url": "/products/Wireless_Earbuds.png",
        },
        {
            "name": "USB-C Hub 7-in-1",
            "description": "7-in-1 USB-C hub with HDMI, USB ports, and card readers for expanded device connectivity.",
            "price": 44.99,
            "stock_quantity": 65,
            "image_url": "/products/USB-C_Hub_7-in-1.png",
        },
        {
            "name": '27" QHD Monitor',
            "description": "27-inch QHD monitor with sharp image quality for productivity, media, and everyday desktop use.",
            "price": 249.99,
            "stock_quantity": 25,
            "image_url": "/products/27_QHD_Monitor.png",
        },
        {
            "name": '24" Full HD Monitor',
            "description": "24-inch Full HD monitor designed for everyday productivity, browsing, and general desktop use.",
            "price": 139.99,
            "stock_quantity": 40,
            "image_url": "/products/24_Full_HD_Monitor.png",
        },
        {
            "name": "Mechanical Keyboard 75%",
            "description": "75% mechanical keyboard with hot-swappable switches and RGB lighting for a compact customizable setup.",
            "price": 119.99,
            "stock_quantity": 40,
            "image_url": "/products/Mechanical_Keyboard_75.png",
        },
        {
            "name": "Wireless Gaming Mouse",
            "description": "Low-latency wireless gaming mouse with adjustable DPI for precise and responsive control.",
            "price": 69.99,
            "stock_quantity": 50,
            "image_url": "/products/Wireless_Gaming_Mouse.png",
        },
        {
            "name": "Laptop Backpack",
            "description": "Water-resistant laptop backpack with a padded compartment for carrying a laptop and daily essentials.",
            "price": 54.99,
            "stock_quantity": 70,
            "image_url": "/products/Laptop_Backpack.png",
        },
        {
            "name": "Power Bank 20,000mAh",
            "description": "20,000mAh portable power bank with USB-C charging for convenient power on the go.",
            "price": 49.99,
            "stock_quantity": 85,
            "image_url": "/products/Power_Bank_20000mAh.png",
        },
        {
            "name": "Smart LED Desk Lamp",
            "description": "Adjustable LED desk lamp with multiple brightness levels for flexible workspace lighting.",
            "price": 39.99,
            "stock_quantity": 60,
            "image_url": "/products/Smart_LED_Desk_Lamp.png",
        },
        {
            "name": "Wi-Fi 6 Router",
            "description": "Dual-band Wi-Fi 6 router designed to provide fast and reliable connectivity for home networks.",
            "price": 99.99,
            "stock_quantity": 30,
            "image_url": "/products/Wi-Fi_6_Router.png",
        },
        {
            "name": "External HDD 2TB",
            "description": "Portable 2TB external hard drive for backups, file storage, and transferring everyday data.",
            "price": 79.99,
            "stock_quantity": 45,
            "image_url": "/products/External_HDD_2TB.png",
        },
        {
            "name": "Gaming Controller",
            "description": "Wireless gaming controller designed for PC and compatible devices, with familiar console-style controls.",
            "price": 69.99,
            "stock_quantity": 50,
            "image_url": "/products/Gaming_Controller.png",
        },
        {
            "name": "USB-C Cable 2m",
            "description": "Durable 2-meter USB-C cable designed for compatible charging and data-transfer applications.",
            "price": 14.99,
            "stock_quantity": 180,
            "image_url": "/products/USB-C_Cable_2m.png",
        },
        {
            "name": "Noise Cancelling Headphones",
            "description": "Over-ear wireless headphones with active noise cancellation for focused listening and everyday use.",
            "price": 149.99,
            "stock_quantity": 35,
            "image_url": "/products/Noise_Cancelling_Headphones.png",
        },
        {
            "name": "1080p Streaming Camera",
            "description": "Full HD 1080p camera designed for video calls, streaming, and content creation.",
            "price": 79.99,
            "stock_quantity": 30,
            "image_url": "/products/1080p_Streaming_Camera.png",
        },
        {
            "name": "RGB Gaming Desk Mat",
            "description": "Extended gaming desk mat with RGB edge lighting, providing a large surface for keyboard and mouse.",
            "price": 34.99,
            "stock_quantity": 70,
            "image_url": "/products/RGB_Gaming_Desk_Mat.png",
        },
    ]

    try:
        # Clear existing products to avoid duplicates
        db.query(Product).delete()

        for item in products_data:
            product = Product(
                name=item["name"],
                description=item["description"],
                price=Decimal(str(item["price"])),
                stock_quantity=item["stock_quantity"],
                image_url=item.get("image_url"),
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
