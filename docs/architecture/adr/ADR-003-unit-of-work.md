# ADR-003: Unit of Work

## Status

Accepted

## Context

The project requires a mechanism to manage database transactions across multiple repositories. Operations like checkout involve multiple repositories (cart, order, payment, product) that must succeed or fail together.

## Problem

How to ensure transactional consistency when:
- Multiple repositories need to participate in the same transaction
- Services orchestrate operations across different aggregates
- Rollback must be centralized and reliable
- The Session lifecycle should be managed without tight coupling

## Decision

Implement a **Unit of Work (UoW)** pattern:
- UoW encapsulates a SQLAlchemy Session
- Commit and rollback remain centralized in the UoW
- All repositories use the same Session from the UoW
- Services do not control transactions directly
- Session lifecycle is managed by the UoW context manager

## Justification

- **Transactional consistency**: Ensures all operations in a workflow succeed or fail together
- **Single responsibility**: Services orchestrate business logic, UoW manages transactions
- **Testability**: UoW can be mocked or replaced in tests
- **Explicit control**: Clear entry and exit points for transactions via context manager
- **Industry pattern**: Well-understood pattern in DDD and enterprise applications

## Consequences

- All database operations go through the UoW
- Repositories receive the Session from the UoW, not created independently
- Services call `uow.commit()` or `uow.rollback()` explicitly
- Session is closed by its creator (get_db dependency), not by the UoW
- Transaction boundaries are explicit in the code
