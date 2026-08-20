# Technical Documentation

Technical overview of the e-commerce backend.

This document provides a high-level understanding of the system, its architecture, business workflows, and engineering decisions before diving into the detailed documentation.

---

# System Overview

The project implements a complete e-commerce purchase lifecycle, covering:

- User registration and authentication
- Product catalog management
- Shopping cart operations
- Checkout orchestration
- Payment processing
- Payment retries
- Webhook-driven payment synchronization

The architecture prioritizes consistency, simplicity, and maintainability while remaining practical for real-world backend development.

---

# Architectural Overview

The system follows a layered architecture composed of Presentation, Application, Domain Modules, and Infrastructure.

Business functionality is organized around domain-oriented modules: simple single-domain workflows remain inside their owning module, and only workflows coordinating multiple domains execute through the Application layer.

For the complete description of the layers, responsibilities, and architectural boundaries, see [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

# Main Architectural Objectives

The architecture is designed around five goals.

## Separation of Concerns

Each layer has a single responsibility.

- Presentation handles HTTP.
- Application orchestrates cross-domain workflows.
- Domain modules own business logic.
- Infrastructure provides technical implementations.

## Consistency

Transaction boundaries, business rules, and persistence responsibilities remain explicit and predictable across the project.

## Simplicity

Avoid abstractions that do not provide practical value.

CRUD operations stay inside their domain module.

Application orchestration is introduced only for multi-domain workflows.

## Testability

Business behavior can be validated independently from infrastructure concerns.

## Maintainability

Domain ownership and module boundaries allow the system to evolve without unnecessary coupling.

---

# Core Domains

The system is organized around business domains.

## Users

Authentication, authorization, and account lifecycle.

## Products

Catalog management and inventory tracking.

## Cart

Temporary purchase state and cart operations.

## Orders

Purchase records generated during checkout.

## Payments

Payment processing, retries, provider communication, and status tracking.

## Idempotency

Protection against duplicate execution of critical workflows.

---

# Business Workflow Model

The system distinguishes between two categories of workflows.

## Module Workflows

Single-domain business operations remain inside their owning module.

Examples:

- Create User
- Update Product
- Add Cart Item
- Delete User

These use cases own:

- business rules;
- repositories;
- transaction boundaries through UnitOfWork.

## Application Workflows

Only workflows involving multiple domains execute through the Application layer.

Examples:

- Checkout
- Retry Payment
- Stripe Webhook Processing

These use cases coordinate multiple modules without owning domain-specific business rules.

---

# Purchase Flow

The primary workflow is:

User

→ Authentication

→ Product Selection

→ Cart Management

→ Checkout

→ Order Creation

→ Payment Creation

→ Payment Confirmation

Checkout represents the primary cross-domain orchestration of the system.

---

# Payment Architecture

Payment processing is isolated behind a gateway abstraction.

This allows:

- provider replacement;
- easier testing;
- reduced coupling between business rules and Stripe.

Stripe is currently the concrete implementation.

Payment state may change through:

- Checkout
- Retry Payment
- Stripe Webhooks

---

# Transaction Management

Every write operation executes through a UnitOfWork.

Repositories:

- never commit;
- never rollback.

Transaction ownership belongs to:

- module use cases for single-domain workflows;
- application use cases for cross-domain workflows.

---

# Testing Philosophy

Different testing layers validate different system risks.

## Unit Tests

Validate isolated business rules.

## Integration Tests

Validate interaction between business logic and infrastructure.

## Workflow Tests

Validate complete business journeys through public HTTP APIs.

Examples include:

- Authentication
- Checkout
- Payment processing
- Stock updates
- Idempotency guarantees

---

# Documentation Map

| Document | Purpose |
|----------|---------|
| ARCHITECTURE.md | Layers, transaction boundaries, workflow model, and architecture overview |
| DECISIONS.md | Consolidated summary of architectural decisions and accepted trade-offs |
| architecture/ADR-INDEX.md | Index of detailed Architecture Decision Records |
| ENDPOINTS.md | Complete HTTP API reference |
| PROJECT_STRUCTURE.md | Repository organization and module layout |
| RUN.md | Setup and development workflow |

---

# Suggested Reading Order

## Understanding the Architecture

1. README-TECH.md
2. ARCHITECTURE.md
3. DECISIONS.md
4. architecture/ADR-INDEX.md

## Working on the Codebase

1. README-TECH.md
2. PROJECT_STRUCTURE.md
3. ARCHITECTURE.md
4. DECISIONS.md
5. architecture/ADR-INDEX.md
6. RUN.md

## Consuming the API

1. README-TECH.md
2. ENDPOINTS.md
3. RUN.md

---

# Project Snapshot

- Backend: FastAPI
- ORM: SQLAlchemy 2.x
- Migrations: Alembic
- Validation: Pydantic v2
- Payments: Stripe
- Authentication: JWT
- Architecture: Layered Architecture with Domain-Oriented Modules
- Transaction Pattern: Unit of Work
- Persistence Pattern: Repository
- External Integration: Gateway
- Testing: Unit, Integration, and Workflow Tests
