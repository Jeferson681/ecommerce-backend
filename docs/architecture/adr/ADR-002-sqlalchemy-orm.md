# ADR-002: SQLAlchemy ORM

## Status

Accepted

## Context

The project requires a persistence layer for an e-commerce backend. The team evaluated options for database access, considering raw SQL, lightweight ORMs, and full-featured ORMs.

## Problem

Which persistence technology should be used to:
- Accelerate development for an MVP
- Maintain control over database operations
- Demonstrate professional backend architecture
- Support complex domain models and relationships

## Decision

Use **SQLAlchemy ORM** as the persistence layer.

## Justification

- **Productivity**: ORM accelerates development by abstracting repetitive SQL operations
- **Control**: SQLAlchemy provides sufficient control over queries and schema
- **Industry standard**: Widely adopted in Python backend development
- **Portfolio relevance**: Demonstrates ORM usage, which is expected in professional backend roles
- **Not the focus**: The project goal is to demonstrate backend architecture, not raw SQL modeling
- **Flexibility**: Supports both ORM-style and Core-style queries when needed

## Consequences

- Database schema is defined through SQLAlchemy models
- Migrations are managed by Alembic
- Repositories use SQLAlchemy Session for data access
- Some SQL-specific optimizations may require Core-style queries
- Team must understand ORM concepts and SQLAlchemy specifics
