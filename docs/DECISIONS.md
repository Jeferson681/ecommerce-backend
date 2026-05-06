# Decisions

- Modular monolith: keeps clear boundaries per aggregate root with low operational overhead.
- No separate ORM/domain models: a single domain model per module reduces duplication and drift.
- Centralized use_cases: orchestration stays explicit and testable, separating HTTP from domain concerns.
- No messaging/queues: synchronous API flow matches the current scope and avoids extra infrastructure.
- Sub-entities not exposed: CartItem and OrderItem remain internal to their aggregate roots for consistency.
