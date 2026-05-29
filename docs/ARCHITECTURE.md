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
|       └── webhook.py
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
|       ├── gateways/
|       ├── ├── base.py
|       ├── └── stripe_gateway.py
│       ├── schemas.py
│       ├── use_cases.py
|       ├── payment_service.py
|
|

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

## Idempotency handling

- Idempotency records are stored under `backend/app/idempotency`.
- Helpers in `idempotency/helpers.py` return the raw stored payload (no Pydantic validation) to avoid double-validation and format mismatches during replay.
- Validation of replayed payloads is the responsibility of the calling use-case (`use_cases`) which performs a single `*.model_validate(raw)` step.
- Repositories handle persistence only; `service.py` contains pure business helpers while orchestration and validation live in module use-cases.
- inventory (optional): stock tracking for products.
