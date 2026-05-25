# Architecture

## Folder structure

Snapshot: current repo state

```
backend/app/
├── main.py
│
├── api/
│   └── routers/
│       ├── auth.py
│       ├── admin.py
│       ├── user.py
│       ├── product.py
│       ├── cart.py
│       ├── order.py
│       └── payment.py
│
├── application/
│   └── uow/
│       ├── dependencies.py
│       └── unit_of_work.py
│
├── core/
│   ├── config.py
│   ├── database.py
│   ├── exceptions.py
│   └── security.py
│
├── idempotency/
│   ├── helpers.py
│   ├── service.py
│   └── repositories/
│       └── idempotency_repository.py
|   └── domain/
│       └── models.py
│
├── infrastructure/
│   └── db/
│       ├── dependencies.py
│       └── session.py
│
├── modules/
│   ├── auth/
│   ├── user/
│   ├── product/
│   ├── cart/
│   ├── order/
│   └── payment/
│       ├── domain/
│       │   └── models.py
│       ├── repositories/
│       │   └── payment_repository.py
│       ├── schemas.py
│       └── use_cases.py
│
└── observability/
    └── request_logging.py

frontend/
├── app/
├── core/
├── shared/
├── modules/
├── public/
├── next.config.ts
├── package.json
└── ...
```

> The frontend is a Next.js storefront used for API validation and manual testing.
> The main focus remains the backend architecture and domain implementation.

## Modules

A module is a boundary around one aggregate root: domain models, repository, schemas, and use-cases.

## Entities

### Domain entities

- Aggregate roots: User, Product, Cart, Order, Payment, Inventory (optional)
- Sub-entities (no module): CartItem, OrderItem

### Usage entities

- Auth (no domain model, no repository)

## Module summary

- user: user aggregate root lifecycle.
- auth: token login/logout orchestration.
- product: product catalog with CRUD operations.
- cart: cart aggregate root and its CartItem collection.
- order: checkout and order retrieval.
- payment: payment processing orchestration and retrieval.
- inventory (optional): stock tracking for products.
