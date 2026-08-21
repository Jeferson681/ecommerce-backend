# ADR-005: Selective Application Layer for Cross-Domain Use Cases

## Status

Accepted

## Context

The project needed to decide where to place use case orchestration logic. A separate Application layer was considered, and the team evaluated the cost-benefit of adding another abstraction layer.

## Problem

Where should use case orchestration live:
- In a dedicated Application layer (separate from domain Services)
- Within the existing Services layer
- In the Routers directly

## Decision

The project has a **selective Application Layer**:

```text
backend/app/application/use_cases/
```

It exists specifically to concentrate **cross-domain use cases** — application flows that coordinate operations involving multiple modules/entities and that do not naturally belong to a single domain module.

The Application Layer is **not** described as a mandatory layer for all use cases.

### Architectural rule

- Use cases that clearly belong to a single context/module remain inside that module.
- Use cases that coordinate multiple modules/entities may be placed in `backend/app/application/use_cases/`.

### Existing examples

- `checkout`
- `retry_payment`
- `webhook`

These use cases have a cross-cutting/orchestrating nature and justify their location in the Application Layer.

## Justification

- **Cross-domain coordination**: Checkout, retry payment, and webhook processing coordinate multiple modules (cart, product, order, payment, idempotency) and do not belong to a single domain.
- **Selective use**: Single-domain use cases remain inside their owning module, avoiding an unnecessary mandatory Application layer.
- **Clear separation**: Routers remain thin HTTP adapters; cross-domain orchestration is explicit where it provides real value.
- **Pragmatic scope**: The Application Layer is introduced only where multiple domains participate, not as a blanket architectural requirement.

## Consequences

- The Application Layer exists at `backend/app/application/use_cases/`.
- It is used selectively for cross-domain use cases (`checkout`, `retry_payment`, `webhook`).
- Single-domain use cases remain inside their owning module services.
- Routers remain thin, delegating to module services or application use cases.
- The pattern is consistent across the project.
