# E-commerce Backend API

A modular FastAPI backend for e-commerce with domain-driven design, SQLAlchemy 2.x ORM, and comprehensive integration tests.

Authentication · Checkout · Payment Processing · Stripe Integration · Idempotent Requests

---

## What it is

An e-commerce backend API that handles the complete purchase flow: product catalog, shopping cart management, payment processing via Stripe, order management, and payment retry for failed transactions.

## Features

- **JWT Authentication** — access + refresh tokens with configurable expiry
- **Product Catalog** — CRUD with search, pagination, category filtering, and sorting
- **Shopping Cart** — add, update, remove items; merge anonymous carts after login
- **Checkout Flow** — idempotent checkout with order + payment creation in a single transaction
- **Payment Processing** — Stripe gateway integration with status mapping and failure handling
- **Payment Retry** — retry failed payments without creating a new order or cart
- **Stripe Webhooks** — signature-verified webhook receiver for async payment synchronization
- **Idempotency** — key-based deduplication prevents duplicate checkouts on retries

## Engineering Highlights

- **Unit of Work pattern** for atomic transactions across multiple repositories
- **Gateway pattern** decouples payment processing from Stripe implementation
- **Layered architecture** with clear separation between presentation, application, and domain
- **224 tests** (unit + integration) with real database on each run
- **Integration tests** cover checkout, payment, webhook, retry, and idempotency flows

## Technologies

Python 3.13 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · Alembic · Stripe API · JWT (python-jose) · pytest

## Quick start

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn backend.app.main:app --reload
```

Create `.env` with `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` (get from Stripe dashboard).

API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

## Documentation

- [Architecture](./docs/ARCHITECTURE.md) — layers, guarantees, transaction boundaries, flows
- [Decisions](./docs/DECISIONS.md) — architectural decision records
- [Endpoints](./docs/ENDPOINTS.md) — complete API reference
- [Project Structure](./docs/PROJECT_STRUCTURE.md) — directory tree
- [Run Guide](./docs/Run.md) — local setup instructions
