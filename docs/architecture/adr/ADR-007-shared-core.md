# ADR-007: Shared Core

## Status

Accepted

## Context

The project has cross-cutting concerns that are used across multiple modules but don't belong to any specific domain. These include configuration, database connections, security utilities, logging, and exception handling.

## Problem

How to organize shared functionality that:
- Is used by multiple modules
- Doesn't belong to any specific domain
- Should not be duplicated across modules
- Needs clear ownership and maintenance

## Decision

Create a **shared `core` package**:
- `core/config.py`: Application settings and configuration
- `core/database.py`: Database engine and session management
- `core/security.py`: Password hashing and JWT utilities
- `core/exceptions.py`: Common exception classes
- `core/rate_limit.py`: Rate limiting configuration
- `observability/`: Logging and health checks

## Justification

- **Avoid duplication**: Common functionality is defined once
- **Clear ownership**: Core components have a single, obvious location
- **Not domain-specific**: These concerns don't belong to any single module
- **Not pure infrastructure**: Core is part of the application, not external infrastructure
- **Easy discovery**: Developers know where to find shared utilities

## Consequences

- All modules import from `core` for cross-cutting concerns
- Core has no dependencies on domain modules
- Changes to core affect all modules (requires careful versioning)
- Core is stable and changes infrequently
- New modules can rely on core being available
