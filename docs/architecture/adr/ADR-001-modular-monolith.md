# ADR-001: Modular Monolith

## Status

Accepted

## Context

The project requires a backend architecture that demonstrates professional software engineering practices while maintaining simplicity for an MVP. The system needs to handle e-commerce operations including authentication, products, cart, orders, and payments.

## Problem

How should the backend be structured to balance:
- Clear separation of concerns
- Maintainability without over-engineering
- Demonstrable architectural patterns for a portfolio
- Simple deployment and development workflow

## Decision

The system is designed as a **modular monolith**:
- All entities remain in a single repository
- Modules have independent responsibilities
- No physical separation of database or deployment
- Modularization is adopted for organization, maintainability, and low coupling

## Justification

- **Simplicity**: A single deployment unit avoids the complexity of microservices for an MVP
- **Clear boundaries**: Modules enforce domain boundaries through code organization
- **Easy refactoring**: Modules can be extracted into separate services later if needed
- **Development velocity**: Single codebase simplifies local development and testing
- **Portfolio value**: Demonstrates understanding of modular design without unnecessary complexity

## Consequences

- All code lives in one repository, which is appropriate for the project scope
- Modules are organized by domain (auth, product, cart, order, payment, user)
- Each module contains its own domain models, repositories, and services
- Shared concerns are extracted to a `core` package
- Future extraction to microservices is possible without rewriting business logic
- Database schema is shared across all modules in a single database
