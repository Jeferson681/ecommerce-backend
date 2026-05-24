from fastapi.testclient import TestClient

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.auth.tokens import create_access_token
from backend.app.modules.user.domain.models import User, UserRole

client = TestClient(app)


def _admin_headers() -> dict[str, str]:
    session = SessionLocal()
    admin = User(
        first_name="Admin",
        last_name="User",
        email="admin-product-api@example.com",
        password_hash="x",
        role=UserRole.ADMIN,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    token = create_access_token({"sub": str(admin.id)})
    return {"Authorization": f"Bearer {token}"}


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_post_products_creates_and_returns_201():
    payload = {"name": "p1", "description": "d", "price": 9.99, "stock_quantity": 5}
    resp = client.post("/products", json=payload, headers=_admin_headers())
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
