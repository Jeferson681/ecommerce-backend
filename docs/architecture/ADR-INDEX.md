# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records (ADRs) documenting the significant architectural decisions made for this project.

## Index

| Number | Title | Description |
|--------|-------|-------------|
| ADR-001 | Modular Monolith | Single system with independent modules |
| ADR-002 | SQLAlchemy ORM | ORM choice for accelerated development |
| ADR-003 | Unit of Work | Centralized transaction management |
| ADR-004 | Repository Pattern | Data access abstraction |
| ADR-005 | Selective Application Layer for Cross-Domain Use Cases | Cross-domain use cases in Application layer |
| ADR-006 | Routers Without Business Logic | HTTP-only routers |
| ADR-007 | Shared Core | Cross-cutting concerns |
| ADR-008 | Single Database | One database for the monolith |
| ADR-009 | Stripe + PaymentGateway Protocol | Payment provider abstraction |

## What is an ADR?

An Architecture Decision Record captures a significant architectural decision made for this project, including:

- **Context**: The situation and constraints
- **Problem**: What needed to be solved
- **Decision**: What was decided
- **Justification**: Why this decision was made
- **Consequences**: The resulting outcomes

## How to Use

When adding a new ADR:

1. Copy the template from `adr/ADR-TEMPLATE.md`
2. Number it sequentially (next available number)
3. Fill in all sections
4. Add the entry to this index
5. Submit a pull request

## References

- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) by Michael Nygard
