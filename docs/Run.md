# Run Guide

Step-by-step instructions to run the project locally on Windows.

---

## 1. Prerequisites

- Python 3.13+
- Git
- Node.js (18+) and npm or pnpm — required to run the frontend
- (Optional) Stripe account for payment testing

## 2. Setup

```powershell
# Clone
git clone <repository>
cd ecommerce-backend

# Create virtual environment
python -m venv .venv

# Activate
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for development
```

## 3. Configure

Create a `.env` file in the project root:

```env
# Required for payment processing (get yours from Stripe dashboard)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
# Optional for webhook signature verification
STRIPE_WEBHOOK_SECRET=whsec_...
```

JWT settings have secure defaults — override only if needed:

```env
JWT_SECRET_KEY=dev-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7
```

## 4. Run Migrations

```powershell
alembic upgrade head
```

## 5. Start the Backend

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend available at:

```
http://127.0.0.1:8000
http://127.0.0.1:8000/docs   (Swagger UI)
```

## 6. Run Tests

```powershell
# All tests
python -m pytest

# Unit tests only
python -m pytest tests/unit -q

# Integration tests only
python -m pytest tests/integration -q

# With coverage
python -m pytest --cov=backend.app --cov-report=html
```

## 7. Code Quality

```powershell
pre-commit run --all-files
```

## 8. (Optional) Start the Frontend

```powershell
Set-Location frontend
 npm ci
 npm run dev

```

Frontend available at `http://localhost:3000`.
