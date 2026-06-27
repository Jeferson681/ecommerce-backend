# scripts/seed_admin.py

from backend.app.modules.auth.security import hash_password

from backend.app.core.database import SessionLocal
from backend.app.modules.user.domain.models import User, UserRole


def seed_admin():
    db = SessionLocal()

    admin = db.query(User).filter(User.email == "admin@ecommerce.com").first()

    if admin:
        print("Admin já existe.")
        return

    admin = User(
        first_name="Admin",
        last_name="Root",
        email="admin@ecommerce.com",
        password_hash=hash_password("Admin123!"),
        role=UserRole.ADMIN,
    )

    db.add(admin)
    db.commit()

    print("Admin criado.")


if __name__ == "__main__":
    seed_admin()
