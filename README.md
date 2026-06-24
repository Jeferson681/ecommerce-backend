# E-commerce Backend API

A modular FastAPI backend for e-commerce with domain-driven design, SQLAlchemy 2.x ORM, and comprehensive automated testing.

Authentication · Checkout · Payment Processing · Stripe Integration · Idempotent Requests

---

## What it is

An e-commerce backend API that handles the complete purchase flow:

- Product catalog
- Shopping cart management
- Checkout processing
- Order management
- Stripe payments
- Payment retry for failed transactions

---

## Features

- **JWT Authentication** — access and refresh tokens with configurable expiration
- **Product Catalog** — CRUD, search, pagination, filtering, and sorting
- **Shopping Cart** — add, update, remove, and merge cart items
- **Checkout Flow** — idempotent checkout with transactional order creation
- **Payment Processing** — Stripe integration with status mapping and failure handling
- **Payment Retry** — retry failed payments without recreating orders
- **Stripe Webhooks** — asynchronous payment synchronization
- **Idempotency** — duplicate checkout protection through idempotency keys

---

## Engineering Highlights

- **Unit of Work Pattern** for transactional consistency
- **Gateway Pattern** for payment provider abstraction
- **Layered Architecture** with clear separation of concerns
- **Comprehensive Test Suite** covering unit, integration, and workflow scenarios
- **Real Purchase Flow Validation** including checkout, payments, retries, and webhooks

---

## Technologies

Python 3.13 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · Alembic · Stripe API · JWT · Pytest

---

## Running the Project

See:

```text
docs/RUN.md
```

for complete instructions on:

- Installation
- Configuration
- Database migrations
- Backend execution
- Frontend execution
- Test execution
- Development workflow

---

## Documentation

- `docs/RUN.md` — setup and execution guide
- `docs/ARCHITECTURE.md` — architecture overview
- `docs/DECISIONS.md` — architectural decisions
- `docs/ENDPOINTS.md` — API reference
- `docs/PROJECT_STRUCTURE.md` — project structure
- `docs/README-TECH.md` — technical documentation index
