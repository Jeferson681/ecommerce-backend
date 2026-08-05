# ADR-008: Single Database

## Status

Accepted

## Context

The project is a modular monolith with multiple bounded contexts (auth, product, cart, order, payment, user). The team evaluated whether to use a single database or separate databases/schemas for each module.

## Problem

How to structure database persistence for a modular monolith:
- Should each module have its own database or schema?
- Should all modules share a single database?
- How to maintain module isolation while keeping deployment simple?

## Decision

Use a **single database** for all modules:
- All modules share the same PostgreSQL database
- Tables are organized by module through naming conventions
- No schema separation or database-per-module
- Module isolation is maintained through code organization, not infrastructure

## Justification

- **Simplicity**: Single database is simpler to manage, backup, and migrate
- **No justification for separation**: As a monolith, there is no operational need for separate databases
- **Development velocity**: Easier local development and testing
- **Cost effective**: Single database connection pool, single backup strategy
- **Sufficient isolation**: Code organization provides adequate module boundaries

## Consequences

- All modules share the same database connection and session
- Migrations are managed centrally by Alembic
- Module isolation is enforced by code organization, not database schemas
- Foreign keys can exist between module tables if needed
- Database backups include all modules
