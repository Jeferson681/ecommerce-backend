# Technical Documentation

Technical overview of the e-commerce backend.

This document provides a high-level understanding of the system, its architecture, business flows, and engineering decisions before diving into the detailed documentation.

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

The system was designed to prioritize transactional consistency, modularity, and testability rather than focusing solely on CRUD operations.

---

# Main Architectural Objectives

The architecture was designed around five goals:

## Separation of Concerns

Business rules remain isolated from HTTP, database, and payment provider implementations.

## Transactional Consistency

Critical operations execute within well-defined transaction boundaries to maintain data consistency and support safe recovery from failures.

## Testability

Business behavior can be validated independently from infrastructure concerns.

## Extensibility

External providers and persistence implementations can evolve without forcing changes across the entire system.

## Predictability

Idempotency and explicit business workflows reduce the risk of duplicated operations and inconsistent states.

---

# Core Domains

The system is organized around business domains rather than technical layers.

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

Protection against duplicate checkout execution.

---

# Purchase Flow

The primary workflow of the system is:

User
→ Authentication
→ Product Selection
→ Cart Management
→ Checkout
→ Order Creation
→ Payment Creation
→ Payment Confirmation

The checkout process coordinates multiple domains and represents the most complex transactional workflow in the application.

---

# Payment Architecture

Payment processing is isolated behind a gateway abstraction.

This allows:

- Provider replacement
- Easier testing
- Reduced coupling between business rules and Stripe

Stripe is currently the concrete implementation used by the project.

Payment updates may occur through:

- Direct checkout responses
- Retry operations
- Stripe webhooks

---

# Testing Philosophy

The project uses multiple testing layers because different risks exist at different levels.

## Unit Tests

Validate isolated business rules.

## Integration Tests

Validate interaction with the database and infrastructure components.

## Workflow Tests

Validate complete business journeys through public HTTP APIs.

Examples include:

- Authentication flows
- Checkout execution
- Payment processing
- Stock updates
- Idempotency guarantees

---

# Documentation Map

| Document | Purpose |
|-----------|----------|
| ARCHITECTURE.md | Detailed architecture, layers, transaction boundaries, and flows |
| DECISIONS.md | Major architectural decisions and trade-offs |
| ENDPOINTS.md | Complete API reference |
| PROJECT_STRUCTURE.md | Repository organization and module layout |
| RUN.md | Setup, execution, and development workflow |

---

# Suggested Reading Order

## Understanding the System

1. README-TECH.md
2. ARCHITECTURE.md
3. DECISIONS.md

## Working on the Codebase

1. README-TECH.md
2. RUN.md
3. PROJECT_STRUCTURE.md
4. ARCHITECTURE.md

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
- Architecture: Layered + Domain-Oriented Modules
- Patterns: Unit of Work, Repository, Gateway
- Testing: Unit, Integration, and Workflow Tests
-
