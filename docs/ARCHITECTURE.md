# Architecture

## Overview

The system follows a **layered architecture** with four distinct layers. Dependencies flow inward: Presentation → Application → Domain. Infrastructure is shared across all layers.

```
┌──────────────────────────────────────────────────┐
│              Presentation Layer                   │
│        FastAPI routers (api/routers/)             │
│  Translates HTTP requests into use case calls     │
├──────────────────────────────────────────────────┤
│              Application Layer                    │
│   Use cases (application/use_cases/)              │
│   Orchestrates domain operations, manages UoW     │
├──────────────────────────────────────────────────┤
│               Domain Layer                        │
│   Entities, repositories, gateways (modules/)     │
│   Business logic, status transitions, value objs  │
├──────────────────────────────────────────────────┤
│           Infrastructure Layer                    │
│   SQLAlchemy, Alembic, Stripe SDK, JWT            │
│   Shared: config.py, database.py, exceptions.py   │
└──────────────────────────────────────────────────┘
```

**Key rules:**
- Presentation never accesses repositories directly
- Application never contains business logic — it orchestrates domain objects
- Domain never depends on infrastructure (gateway protocol, not implementation)
- All write operations go through `UnitOfWork`

---

## System Guarantees

All system guarantees are documented as Architectural Decision Records in [DECISIONS.md](./DECISIONS.md):

- **Atomic Checkout** — single transaction across 6 repositories, rollback on any failure
- **Atomic Retry Payment** — isolated transaction with stuck key cleanup
- **Idempotency** — key-based deduplication with database-level unique constraint
- **Cart Merge Consistency** — atomic upsert of local items into server cart
- **Stripe Webhook Verification** — HMAC-SHA256 signature verification before processing
- **Rollback Strategy** — `try/except` pattern with session reset and key release

For the detailed rationale behind each guarantee, see [DECISIONS.md](./DECISIONS.md).

---

## Transaction Boundaries

| Operation | Boundary | Repositories involved |
|---|---|---|
| Checkout | `checkout()` use case | Cart, CartItem, Order, OrderItem, Payment, Product, Idempotency |
| Retry payment | `retry_payment()` use case | Order, Payment, Idempotency |
| Webhook | `process_provider_webhook()` use case | Payment, Order |
| Cart add item | `add_item()` in module | Cart, CartItem |
| Cart merge | `merge_cart_items()` in module | Cart, CartItem |

Each boundary opens one `UnitOfWork` instance, performs reads and writes, then calls `commit()` or `rollback()`. Repositories never manage transactions.

---

## Flows

### Checkout

```
POST /orders/checkout
  │
  ├─ Presentation: validate PaymentMethodRequest, extract user_id, compute request_hash
  │
  ├─ Application (checkout()):
  │   ├─ 1. Validate idempotency input (both key + hash or neither)
  │   ├─ 2. Try replay — if stored response exists, return immediately
  │   ├─ 3. Load cart (404 if missing)
  │   ├─ 4. Load cart items (400 if empty)
  │   ├─ 5. Validate stock for all products (400 if insufficient)
  │   ├─ 6. Reserve idempotency key + commit
  │   ├─ 7. Try replay again — another request may have completed
  │   ├─ 8. Create Order from cart items, decrement stock
  │   ├─ 9. Create Payment (status = PENDING)
  │   ├─10. Process Payment via StripeGateway
  │   │     ├─ approved  → Order.status = PAID
  │   │     └─ failed    → Order.status stays PENDING
  │   ├─11. Clear cart (delete Cart + cascade CartItems)
  │   ├─12. Persist idempotency response (OrderRead JSON)
  │   └─13. Commit
  │
  └─ On exception: rollback, release key, re-raise
```

### Retry Payment

```
POST /orders/{order_id}/retry-payment
  │
  ├─ Presentation: validate PaymentMethodRequest, extract user_id
  │
  ├─ Application (retry_payment()):
  │   ├─ 1. Validate idempotency input
  │   ├─ 2. Try replay
  │   ├─ 3. Reserve idempotency key + commit
  │   ├─ 4. Find Order (must be PENDING, owned by user — 404/400 otherwise)
  │   ├─ 5. Find failed Payment for this order (400 if none)
  │   ├─ 6. Process Payment via StripeGateway
  │   │     └─ approved  → Order.status = PAID
  │   ├─ 7. Persist idempotency response
  │   └─ 8. Commit
  │
  └─ On exception: rollback, release key, re-raise
```

### Stripe Webhook

```
POST /webhooks/stripe
  │
  ├─ Presentation: parse raw body, extract Stripe-Signature header
  │
  ├─ Application (process_provider_webhook()):
  │   ├─ 1. Verify HMAC-SHA256 signature (400 if invalid)
  │   ├─ 2. Parse event JSON, extract payment_intent object
  │   ├─ 3. Find Payment by provider_payment_id (404 if missing)
  │   ├─ 4. Update Payment.status, provider_status, failure_reason
  │   ├─ 5. If approved → Order.status = PAID
  │   └─ 6. Commit
  │
  └─ Response: {"received": true}
```

---

> See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for the complete directory tree.
> See [DECISIONS.md](./DECISIONS.md) for the rationale behind each architectural choice.
