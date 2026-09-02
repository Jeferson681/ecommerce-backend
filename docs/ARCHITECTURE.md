# Architecture

> **Navigation note:** This document describes the current architecture of the system.
> Detailed architectural decisions have their own ADRs — [`docs/architecture/adr/`](./architecture/adr/) is the detailed source for the history and rationale of each decision, and [`docs/DECISIONS.md`](./DECISIONS.md) provides a consolidated summary of those decisions.

## Overview

The system follows a layered architecture organized around domain modules.

Simple business workflows execute entirely inside their owning module.

Only workflows that coordinate multiple business domains introduce the Application layer.

Dependencies always flow inward.

```
Presentation
      │
      ├───────────────┐
      ▼               ▼
Application      Domain Modules
 (cross-domain)    (single-domain)
      │               │
      └───────┬───────┘
              ▼
      Infrastructure
```

The architecture intentionally avoids introducing orchestration layers for simple CRUD operations.

---

## Layer Responsibilities

### Presentation

Responsible for:

- HTTP endpoints
- Dependency resolution
- Request parsing
- Response serialization
- Delegating execution

Presentation never contains business rules.

---

### Application

Exists only for cross-domain workflows.

Responsible for:

- Coordinating multiple domain modules
- Defining transaction boundaries across domains
- Sequencing business workflows
- Calling external services when orchestration is required

Application does not own domain rules.

Examples:

- Checkout
- Retry Payment
- Provider Webhook Processing

---

### Domain Modules

Each module owns its own business workflows.

Each module contains its own:

- Models
- Schemas
- Repositories
- Use Cases

Simple CRUD operations execute entirely inside their owning module.

Examples:

- create_user()
- update_product()
- add_cart_item()

Module use cases may:

- instantiate repositories
- use UnitOfWork
- define transaction scope
- commit
- rollback

---

### Infrastructure

Infrastructure provides implementation details such as:

- SQLAlchemy
- FastAPI
- Stripe SDK
- bcrypt
- JWT

Business logic depends on abstractions rather than infrastructure implementations whenever appropriate.

---

## Key Rules

- Routers never contain business rules.
- Routers delegate execution to module or application use cases.
- CRUD operations remain inside their owning module.
- Application exists only for cross-domain workflows.
- Repositories only perform persistence.
- Repositories never manage transactions.
- UnitOfWork owns the transaction lifecycle.
- Domain modules communicate through exposed module contracts whenever appropriate.
- Business layers raise semantic exceptions.
- HTTP translation occurs through centralized exception handlers.

---

## System Guarantees

All architectural guarantees are documented in
[DECISIONS.md](./DECISIONS.md).

These include:

- Checkout consistency
- Retry payment consistency
- Idempotency
- Cart merge consistency
- Stripe webhook verification
- Rollback strategy

Refer to DECISIONS.md for implementation rationale.

---

## Transaction Boundaries

| Operation | Owner | Repositories involved |
|-----------|-------|-----------------------|
| Checkout | Application | Cart, CartItem, Order, OrderItem, Payment, Product, Idempotency |
| Retry payment | Application | Order, Payment, Idempotency |
| Provider webhook | Application | Payment, Order |
| Create user | User module | User |
| Update user | User module | User |
| Add cart item | Cart module | Cart, CartItem |
| Merge cart | Cart module | Cart, CartItem |
| Update product | Product module | Product |

Every transaction is coordinated through UnitOfWork.

Repositories never call:

- commit()
- rollback()

Checkout and Retry Payment span multiple domain modules and are therefore owned by the Application layer. The Provider Webhook flow is Application-owned for the same reason.

All other operations listed above are owned by their domain module and execute within a single UnitOfWork transaction.
