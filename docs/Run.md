# Run Guide

Step-by-step instructions to run the project locally on Windows.

---

## Prerequisites

Required:

- Python 3.13+
- Git
- Node.js 18+
- npm

Optional:

- Stripe account for payment testing

---

## Clone the Repository

```powershell
git clone <repository>
cd ecommerce-backend
```

---

## Create and Activate Virtual Environment

```powershell
python -m venv .venv

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

## Install Backend Dependencies

Install runtime dependencies:

```powershell
pip install -r requirements.txt
```

Install development dependencies:

```powershell
pip install -r requirements-dev.txt
```

---

## Configure Environment Variables

Create a `.env` file in the project root.

Stripe configuration:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

JWT configuration:

```env
JWT_SECRET_KEY=dev-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7
```

---

## Run Database Migrations

```powershell
python -m alembic upgrade head
```

---

## Start Backend

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
Application
http://127.0.0.1:8000

Swagger UI
http://127.0.0.1:8000/docs
```

---

## Start Frontend (Optional)

The integrated frontend provides a visual interface for API demonstration and manual validation of backend functionality.

Open a new terminal.

Navigate to the frontend directory:

```powershell
cd frontend
```

Install frontend dependencies:

```powershell
npm ci
```

Start the development server:

```powershell
npm run dev -- --webpack
```

Frontend:

```text
http://localhost:3000
```

Notes:

- Run `npm ci` during the initial setup.
- Run `npm ci` again whenever `package.json` or `package-lock.json` changes.
- For day-to-day development, `npm run dev` is usually sufficient.

---

## Run Tests

Run the full test suite:

```powershell
pytest
```

Run unit tests:

```powershell
pytest tests/unit -q
```

Run integration tests:

```powershell
pytest tests/integration -q
```

Generate terminal coverage:

```powershell
pytest --cov=backend.app
```

Generate HTML coverage report:

```powershell
pytest --cov=backend.app --cov-report=html
```

---

## Code Quality

Run all configured quality checks:

```powershell
pre-commit run --all-files
```

This executes all configured formatting, linting, and static analysis hooks.

---

## Next Steps

To understand the project architecture and organization, read the documentation in the following order:

1. `docs/README-TECH.md`
2. `docs/ARCHITECTURE.md`
3. `docs/DECISIONS.md`
4. `docs/PROJECT_STRUCTURE.md`
5. `docs/ENDPOINTS.md`
