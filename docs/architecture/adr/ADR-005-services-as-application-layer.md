# ADR-005: Services as Application Layer

## Status

Accepted

## Context

The project needed to decide where to place use case orchestration logic. A separate Application layer was considered, but the project has a closed scope (MVP) and the team evaluated the cost-benefit of adding another abstraction layer.

## Problem

Where should use case orchestration live:
- In a dedicated Application layer (separate from domain Services)
- Within the existing Services layer
- In the Routers directly

## Decision

Keep use cases within the **Services layer**:
- No separate Application layer was created
- Services orchestrate domain operations and coordinate repositories
- Use cases are implemented as functions within service modules
- This avoids creating contracts and complexity without proportional gain for an MVP

## Justification

- **Appropriate scope**: The project is an MVP with closed scope; additional layers add complexity without immediate benefit
- **Single responsibility**: Services already have clear responsibilities (orchestration, not business rules)
- **Simplicity**: Fewer layers mean less boilerplate and easier navigation
- **Not DDD purism**: The decision is pragmatic, not a rejection of DDD principles
- **Future flexibility**: If the project grows, services can be refactored into a proper Application layer

## Consequences

- Services contain orchestration logic (e.g., checkout, retry_payment)
- Domain logic remains in domain models and services
- Routers remain thin, delegating to services
- No Application/UseCase classes or interfaces
- The pattern is consistent across all modules
