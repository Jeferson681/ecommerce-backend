# Architecture

## Folder structure

app/
├── main.py
│
├── core/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   └── exceptions.py
│
├── modules/
│   ├── user/
│   │   ├── domain/
│   │   │   └── models.py
│   │   ├── repositories/
│   │   │   └── user_repository.py
│   │   ├── use_cases.py
│   │   └── schemas.py
│   │
│   ├── product/
│   │   ├── domain/
│   │   │   └── models.py
│   │   ├── repositories/
│   │   │   └── product_repository.py
│   │   ├── use_cases.py
│   │   └── schemas.py
│   │
│   ├── cart/
│   │   ├── domain/
│   │   │   └── models.py
│   │   ├── repositories/
│   │   │   └── cart_repository.py
│   │   ├── use_cases.py
│   │   └── schemas.py
│   │
│   ├── order/
│   │   ├── domain/
│   │   │   └── models.py
│   │   ├── repositories/
│   │   │   └── order_repository.py
│   │   ├── use_cases.py
│   │   └── schemas.py
│   │
│   ├── payment/
│   │   ├── domain/
│   │   │   └── models.py
│   │   ├── repositories/
│   │   │   └── payment_repository.py
│   │   ├── use_cases.py
│   │   └── schemas.py
│   │
│   └── inventory/                # optional
│       ├── domain/
│       │   └── models.py
│       ├── repositories/
│       │   └── inventory_repository.py
│       ├── use_cases.py
│       └── schemas.py
│
├── api/
│   ├── deps.py
│   └── routers/
│       ├── user.py
│       ├── auth.py
│       ├── product.py
│       ├── cart.py
│       ├── order.py
│       ├── payment.py
│       └── inventory.py           # optional
│
├── application/
│   └── uow/
│       └── unit_of_work.py
│
├── infrastructure/
│   └── db/
│       └── session.py
│
├── observability/
│   └── request_logging.py
│
└── idempotency/
    └── service.py

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
- product: product catalog read access.
- cart: cart aggregate root and its CartItem collection.
- order: checkout and order retrieval.
- payment: payment processing orchestration.
- inventory (optional): stock tracking for products.
- user: user aggregate root lifecycle.
- auth: token login/logout orchestration.
- product: product catalog with CRUD operations (create, read, update, delete).
- cart: cart aggregate root and its CartItem collection.
- order: checkout and order retrieval.
- payment: payment processing orchestration and retrieval.
- inventory (optional): stock tracking for products.
