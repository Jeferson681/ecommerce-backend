# Architectural Decision Records

Decisions documented here are observable in the current codebase.

---

## Modular Monolith

**Context:** The project needed to support multiple bounded contexts (cart, order, payment) without the operational overhead of microservices.

**Decision:** Keep all modules in a single deployment unit with clear package-level boundaries. Each module has its own domain models, repositories, schemas, and use cases. Cross-module orchestration (checkout, retry payment, webhook) lives in `application/use_cases/`.

**Consequence:** Clear separation per aggregate root with low operational overhead. Modules communicate through use cases, not direct repository access.

---

## Single Domain Model (No Separate ORM Layer)

**Context:** Many Python projects separate ORM models from domain models, creating duplication and drift risk.

**Decision:** Use the same SQLAlchemy model as both the ORM entity and the domain entity.

**Consequence:** Reduces duplication and ensures the domain model always reflects the actual database schema. The trade-off is that domain logic is coupled to SQLAlchemy.

---

## Unit of Work Pattern

**Context:** Checkout involves multiple repositories (cart, order, payment, product, idempotency) that must be updated atomically.

**Decision:** All write operations receive a `UnitOfWork` instance. The UoW wraps a SQLAlchemy `Session` and exposes `commit()`, `rollback()`, and `flush()`. Repositories never manage transactions.

**Consequence:** Atomic writes across aggregate roots. Exception handlers in use cases call `uow.rollback()` before cleanup.

---

## Gateway Pattern for Payments

**Context:** Payment processing should be decoupled from the payment provider.

**Decision:** Define a `PaymentGateway` protocol with `process_payment()` and `process_webhook()` methods. `StripeGateway` implements both. The checkout and retry use cases receive a `PaymentGateway` instance via dependency injection.

**Consequence:** Adding a new provider (e.g., PayPal, Pix) requires only a new class implementing the protocol.

---

## Idempotency via Dedicated Table

**Context:** Network retries can cause duplicate checkouts. The system needs to detect and reject duplicates without race conditions.

**Decision:** Store idempotency keys in a dedicated `idempotency_keys` table with a unique constraint on `(user_id, key)`. The `claim()` method uses a nested transaction to detect constraint violations. After claim, the use case commits before proceeding with checkout, making the reservation visible to concurrent requests.

**Consequence:** Duplicate requests return the same response (replay). Stuck keys after failures are released via `rollback()` + `delete_by_key()` in the exception handler.

---

## Payment Exposed Through Order Read

**Context:** The frontend needs payment status and transaction details when displaying an order.

**Decision:** Include `payments[]` in the `OrderRead` schema. The `OrderRepository` already loads payments via `selectinload(Order.payments)`.

**Consequence:** Single API call returns order items plus payment history. No additional endpoint needed for payment details.

---

## Retry Payment Through Order Endpoint

**Context:** Failed payments should be retryable without creating a new checkout or cart.

**Decision:** Expose `POST /orders/{order_id}/retry-payment`. The use case finds the pending order and failed payment, then calls `process_payment` with a new `payment_method_id`.

**Consequence:** Retry is a separate, simpler flow from checkout. No cart manipulation needed.

---

## Centralized Status Enums

**Context:** Payment and order status values are referenced across multiple modules.

**Decision:** Define `PaymentStatus` and `OrderStatus` as `StrEnum` classes in their respective domain models. All comparisons use enum members, not string literals.

**Consequence:** Type-safe status handling. Adding a new status updates a single location.

---

## Cart Merge Strategy

**Context:** Users may add items to a local cart before authenticating. After login, those items must merge with any existing server-side cart.

**Decision:** Expose `POST /cart/merge` that accepts a list of `(product_id, quantity)` pairs. The use case calls `get_or_create_cart()` then `_upsert_cart_item()` for each item (sums quantities for duplicates).

**Consequence:** The frontend is responsible for storing local cart state in localStorage and calling `/cart/merge` after login. The backend simply upserts the provided items.

---

## Transaction Rollback on Failure

**Context:** If checkout fails after creating an order or payment, partial writes must be reverted.

**Decision:** All write operations within checkout and retry-payment are wrapped in `try/except`. On exception:
1. `uow.rollback()` resets the session
2. If an idempotency key was claimed, `delete_by_key()` removes it
3. `uow.commit()` persists the deletion
4. The original exception is re-raised

**Consequence:** No stale orders, payments, or idempotency keys after failures.
