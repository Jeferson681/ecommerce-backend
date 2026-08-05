# ADR-004: Repository Pattern

## Status

Accepted

## Context

The project needs a data access layer that isolates business logic from database operations. Services already have significant responsibilities and should not directly handle SQL queries or ORM sessions.

## Problem

How to structure data access to:
- Avoid coupling business logic to the persistence mechanism
- Centralize query logic in a single location
- Make services testable without database dependencies
- Maintain consistency across all modules

## Decision

Implement the **Repository Pattern**:
- Each module has its own repository (e.g., `ProductRepository`, `OrderRepository`)
- Repositories encapsulate all data access logic
- Services depend on repository interfaces, not ORM details
- Unit of Work coordinates all repositories in a transaction

## Justification

- **Separation of concerns**: Services focus on business rules, repositories on data access
- **Testability**: Repositories can be mocked in service tests
- **Consistency**: All data access follows the same pattern across modules
- **Maintainability**: Query logic is centralized and easier to refactor
- **Domain alignment**: Each repository corresponds to an aggregate root

## Consequences

- Services receive repositories as dependencies (via UoW)
- Repositories use SQLAlchemy Session from the UoW
- Query logic is isolated from business logic
- Each module defines its own repository interface
- Changes to the database schema require updates in repositories only
