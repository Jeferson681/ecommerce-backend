# ADR-006: Routers Without Business Logic

## Status

Accepted

## Context

The project needed to define the responsibility boundary for API routers. There was a risk of routers accumulating business logic, which would create coupling between HTTP concerns and domain rules.

## Problem

What should be the responsibility of API routers:
- Should they contain business logic and validation?
- Should they be thin HTTP adapters only?
- How to maintain consistency across all endpoints?

## Decision

Routers have **exclusively HTTP responsibilities**:
- Routers handle HTTP-specific concerns (request/response, status codes, headers)
- Business rules remain outside the API layer
- Routers delegate to services for all business logic
- This reduces coupling and maintains architectural consistency

## Justification

- **Separation of concerns**: HTTP layer should not contain business rules
- **Testability**: Business logic can be tested without HTTP context
- **Reusability**: Services can be called from routers, webhooks, or CLI without duplication
- **Consistency**: All endpoints follow the same pattern
- **Maintainability**: Changes to business logic don't affect HTTP contracts

## Consequences

- Routers are thin wrappers around service calls
- All validation and business rules are in services or domain models
- Routers only handle HTTP-specific concerns (headers, status codes, response models)
- Error handling is centralized in exception handlers
- The pattern is consistent across all routers (auth, product, cart, order, payment)
