# Architecture

## Folder structure

Snapshot: 2026-05-15 (working tree), branch: feat/auth

```
backend/app/
├── main.py
│
├── api/
│   └── routers/
│       ├── auth.py
│       ├── user.py
│       ├── product.py
│       ├── cart.py
│       ├── order.py
│       └── payment.py
│
├── application/
│   └── uow/
│       ├── unit_of_work.py
│       └── dependencies.py
│
├── core/
│   ├── config.py
│   ├── database.py
│   ├── exceptions.py
│   └── security.py
│
├── infrastructure/
│   └── db/
│       ├── session.py
│       └── dependencies.py
│
├── idempotency/
│   └── service.py
│
├── modules/
│   ├── auth/
│   │   ├── schemas.py
│   │   ├── tokens.py
│   │   ├── use_cases.py
│   │   ├── security.py
│   │   ├── validators.py
│   │   └── deps.py
│   │
│   ├── user/
│   │   ├── use_cases.py
│   │   ├── repositories/
│   │   │   └── user_repository.py
│   │   └── domain/
│   │       └── models.py
│   │
│   ├── product/
│   │   ├── use_cases.py
│   │   ├── repositories/
│   │   │   └── product_repository.py
│   │   └── domain/
│   │       └── models.py
│   │
│   ├── cart/
│   │   ├── use_cases.py
│   │   ├── repositories/
│   │   │   └── cart_repository.py
│   │   └── domain/
│   │       └── models.py
│   │
│   ├── order/
│   │   ├── use_cases.py
│   │   ├── repositories/
│   │   │   └── order_repository.py
│   │   └── domain/
│   │       └── models.py
│   │
│   └── payment/
│       ├── use_cases.py
│       ├── repositories/
│       │   └── payment_repository.py
│       └── domain/
│           └── models.py
│
└── observability/
    └── request_logging.py
```

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
- product: product catalog with CRUD operations (create, read, update, delete).
- cart: cart aggregate root and its CartItem collection.
- order: checkout and order retrieval.
- payment: payment processing orchestration and retrieval.
- inventory (optional): stock tracking for products.
