# Architectural Decisions

> **Navigation note:** This document is the **consolidated summary** of the project's architectural decisions. Each decision has detailed documentation in [`docs/architecture/adr/`](./architecture/adr/) — the ADRs are the detailed reference for context, justification, alternatives, and consequences. This file exists to allow a quick reading of the main decisions without opening every ADR.

This document records the major architectural decisions that shape the system.

Each decision captures:

- Context
- Decision
- Consequences

The goal is to document the reasoning behind the architecture and the trade-offs accepted during development.

---

# 1. Modular Monolith

## Context

The system contains multiple business domains:

- Users
- Products
- Cart
- Orders
- Payments
- Idempotency

The project required clear domain boundaries without introducing the operational complexity of distributed systems.

## Decision

The application is implemented as a modular monolith.

Each domain owns its:

- Models
- Schemas
- Repositories
- Use Cases

Cross-domain workflows are coordinated through application-level use cases.

## Consequences

### Benefits

- Simple deployment model
- Low operational overhead
- Clear domain ownership
- Easier local development and testing

### Trade-offs

- Entire system is deployed as a single unit
- Module boundaries rely on architectural discipline
- Domains cannot scale independently

---

# 2. Layered Architecture

## Context

Business rules, HTTP concerns, persistence, and external integrations should evolve independently.

## Decision

The application follows a layered architecture:

```text
Presentation
    ↓
Application
    ↓
Domain
    ↓
Infrastructure
```

Dependencies flow inward.

Higher layers depend on abstractions exposed by lower layers rather than implementation details.

## Consequences

### Benefits

- Clear separation of responsibilities
- Easier testing
- Lower coupling between concerns
- Better maintainability

### Trade-offs

- Additional abstractions increase project structure complexity
- New features require traversing multiple layers

---

# 3. Single Domain and Persistence Model

## Context

Many systems maintain separate domain entities and ORM models.

While this increases separation, it also introduces duplication and mapping overhead.

## Decision

SQLAlchemy models are used directly as domain entities.

No separate mapping layer exists between persistence and domain objects.

## Consequences

### Benefits

- Reduced code duplication
- Simpler repositories
- Faster development
- Domain structure remains aligned with the database schema

### Trade-offs

- Domain entities are coupled to SQLAlchemy
- Replacing the ORM would require broader refactoring
- Complex domain behavior may become harder to isolate as the system grows

---

# 4. Repository Pattern

## Context

Business workflows should not depend directly on ORM queries or database access details.

## Decision

All persistence operations are encapsulated behind repositories.

Repositories are responsible for:

- Aggregate retrieval
- Query execution
- Persistence operations

Use cases interact with repositories rather than SQLAlchemy directly.

## Consequences

### Benefits

- Cleaner business logic
- Better testability
- Centralized persistence rules

### Trade-offs

- Additional abstraction layer
- More classes and files to maintain

---

# 5. Unit of Work Pattern

## Context

Checkout and payment workflows modify multiple aggregates within a single business operation.

These updates must succeed or fail together.

## Decision

Write operations are coordinated through a Unit of Work.

The Unit of Work owns the database transaction and exposes:

- `commit()`
- `rollback()`
- `flush()`

Repositories never manage transactions directly.

## Consequences

### Benefits

- Consistent transaction boundaries
- Atomic business operations within a transaction boundary
- Centralized transaction management

### Trade-offs

- Use cases must explicitly coordinate transactional flow
- Transaction management becomes an application-level responsibility

---

# 6. Payment Gateway Abstraction

## Context

Payment processing should not depend directly on a specific provider.

The business workflow should remain stable even if payment providers change.

## Decision

Payment providers are accessed through a gateway abstraction.

The application defines a payment gateway contract and provides a Stripe implementation.

Business workflows depend on the abstraction rather than the concrete provider.

## Consequences

### Benefits

- Easier testing
- Reduced coupling to Stripe
- Simplified provider replacement
- Clear separation between business rules and external services

### Trade-offs

- Additional abstraction for a single provider
- Gateway contracts must evolve as provider capabilities expand

---

# 7. Idempotent Checkout

## Context

Network retries, client failures, and duplicate requests can cause the same checkout operation to be executed multiple times.

Duplicate order creation must be prevented.

## Decision

Checkout operations require an idempotency key.

The key is stored and validated before the business workflow proceeds.

Repeated requests with the same key return the previously generated result.

## Consequences

### Benefits

- Prevents duplicate orders
- Prevents duplicate payment attempts
- Improves resilience during retries
- Provides predictable behavior under failure scenarios

### Trade-offs

- Additional persistence requirements
- Key lifecycle management and cleanup become necessary
- Increased complexity in checkout orchestration

---

# 8. Inventory Managed by Product

## Context

The system requires inventory tracking and stock validation during checkout.

Inventory data could be modeled as a separate domain or remain part of the product aggregate.

## Decision

Stock ownership belongs to the Product aggregate.

Inventory is represented directly through product stock information.

Checkout workflows validate and update stock through the Product domain.

## Consequences

### Benefits

- Simpler domain model
- Straightforward inventory queries
- Reduced operational complexity
- Easier implementation for a transactional ecommerce workflow

### Trade-offs

- Product and inventory concerns remain coupled
- Future reservation-based inventory models would require refactoring
- High-scale inventory scenarios may benefit from a dedicated inventory domain

---

# 9. Checkout Transaction Boundary

## Context

Checkout coordinates multiple aggregates (Cart, Order, Payment, Product) and requires idempotency to prevent duplicate execution.

The idempotency key is claimed before the main operation to prevent concurrent execution of the same checkout request.

Using a single database transaction would keep the transaction open during the Stripe API call, holding database connections and locks for the duration of a network round-trip.

## Decision

Checkout executes in two phases.

**Phase 1 (reservation)**

- Reserve the idempotency key in a dedicated transaction.
- If the key already exists, return the cached response when available.
- Commit.

**Phase 2 (execution)**

- Create the order.
- Decrement stock.
- Process payment.
- Clear the cart.
- Persist the idempotency response.
- Commit.

If phase two fails, the reserved key is released through a compensating transaction.

## Consequences

### Benefits

- Concurrent requests with the same idempotency key are serialized at the database level
- Replay can be served without re-executing checkout logic
- Consistent write operations within each phase
- Supports safe retries after transient failures

### Trade-offs

- The two-phase approach is not fully atomic across the entire checkout workflow
- Phase one can succeed while phase two fails
- Compensating cleanup requires an additional transaction
- Orphaned keys require periodic cleanup
- Database connections remain allocated during the Stripe API call
- Error handling is more complex than a single-transaction design

---

# Decision Summary

| Decision | Primary Goal |
|-----------|-------------|
| Modular Monolith | Clear domain boundaries with low operational complexity |
| Layered Architecture | Separation of concerns |
| Single Domain and Persistence Model | Reduced duplication |
| Repository Pattern | Persistence isolation |
| Unit of Work Pattern | Transaction consistency |
| Payment Gateway Abstraction | Provider independence |
| Idempotent Checkout | Protection against duplicate execution |
| Inventory Managed by Product | Simplified inventory management |
| Checkout Transaction Boundary | Idempotent checkout execution |
