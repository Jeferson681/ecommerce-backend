# E-commerce Backend API

A modular FastAPI backend for e-commerce with domain-driven design, SQLAlchemy 2.x ORM, and comprehensive automated testing.

Authentication · Checkout · Payment Processing · Stripe Integration · Idempotent Requests

---

## What it is

An e-commerce backend API that handles the complete purchase flow:

- Product Catalog
- Shopping Cart management
- Checkout Processing
- Order Management
- Stripe Payments
- Payment Retry for failed transactions

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


## UX Evidence Gallery

The gallery presents a curated set of screenshots that illustrate the application's primary functional flow. The included evidences represent the user's Happy Path and show key interactions such as searching, checkout and payment confirmation. This is intended to help recruiters, clients and evaluators quickly understand the product without needing to run the project locally.

➡️ **[View complete UX Evidence Gallery](docs/UX_EVIDENCE_GALLERY.md)**

### Gallery Preview

<table>
<tr>
<td align="center" width="33%">
<a href="docs/assets/UX-Gallery/01_home.png">
<img src="docs/assets/UX-Gallery/01_home.png" width="250" alt="Home">
</a><br>
<b>Home</b>
</td>

<td align="center" width="33%">
<a href="docs/assets/UX-Gallery/02_product_search.png">
<img src="docs/assets/UX-Gallery/02_product_search.png" width="250" alt="Product Search">
</a><br>
<b>Product Search</b>
</td>

<td align="center" width="33%">
<a href="docs/assets/UX-Gallery/03_product_detail.png">
<img src="docs/assets/UX-Gallery/03_product_detail.png" width="250" alt="Product Detail">
</a><br>
<b>Product Detail</b>
</td>
</tr>

<tr>
<td align="center">
<a href="docs/assets/UX-Gallery/08_shopping_cart.png">
<img src="docs/assets/UX-Gallery/08_shopping_cart.png" width="250" alt="Shopping Cart">
</a><br>
<b>Shopping Cart</b>
</td>

<td align="center">
<a href="docs/assets/UX-Gallery/09_checkout.png">
<img src="docs/assets/UX-Gallery/09_checkout.png" width="250" alt="Checkout">
</a><br>
<b>Checkout</b>
</td>

<td align="center">
<a href="docs/assets/UX-Gallery/10_payment_approved.png">
<img src="docs/assets/UX-Gallery/10_payment_approved.png" width="250" alt="Payment Approved">
</a><br>
<b>Payment Approved</b>
</td>
</tr>
</table>

The complete functional flow—including authentication, validations, account management and order history—is documented in the **UX Evidence Gallery**.


## Running the Project

See:

```text
docs/Run.md
```

for complete instructions on:

- Installation
- Configuration
- Database migrations
- Backend execution
- Demo frontend (optional)
- Test execution
- Development workflow

---

## Documentation

- `docs/Run.md` — setup and execution guide
- `docs/ARCHITECTURE.md` — architecture overview
- `docs/DECISIONS.md` — architectural decisions
- `docs/ENDPOINTS.md` — API reference
- `docs/PROJECT_STRUCTURE.md` — project structure
- `docs/README-TECH.md` — technical documentation index
