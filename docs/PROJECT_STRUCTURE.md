# Project Structure

Complete directory tree of the backend codebase.

```
backend/
├── app/
│   ├── main.py                          # FastAPI app factory + lifespan
│   │
│   ├── api/routers/                     # Presentation Layer (HTTP)
│   │   ├── admin.py                     # Admin endpoints
│   │   ├── auth.py                      # Token login/logout/refresh
│   │   ├── cart.py                      # Cart CRUD + merge
│   │   ├── order.py                     # Checkout, retry-payment, order queries
│   │   ├── payment_webhook.py           # Stripe webhook receiver
│   │   ├── product.py                   # Product catalog CRUD
│   │   └── user.py                      # User CRUD
│   │
│   ├── application/use_cases/           # Application Layer (orchestration)
│   │   ├── checkout/
│   │   ├── retry_payment/
│   │   └── webhook/
│   │
│   ├── core/                            # Cross-cutting concerns
│   │   ├── config.py
│   │   ├── database.py
│   │   └── exceptions.py
│   │
│   ├── idempotency/                     # Idempotency Key management
│   │   ├── domain/models.py
│   │   ├── helpers.py
│   │   ├── repositories/
│   │   └── service.py
│   │
│   ├── modules/                         # Domain Layer
│   │   ├── auth/
│   │   ├── cart/
│   │   ├── order/
│   │   ├── payment/
│   │   ├── product/
│   │   └── user/
│   │
│   └── uow/                             # Unit of Work transaction manager
│       ├── dependencies.py
│       └── unit_of_work.py
│
├── frontend/                            # Next.js storefront (manual testing)
├── tests/                               # 224 tests (unit + integration)
│   ├── unit/
│   ├── integration/
│   └── workflows/
│
└── alembic/                             # Database migrations
```

## Module Anatomy

Each domain module follows a consistent structure:

```
modules/{entity}/
├── domain/models.py       # SQLAlchemy aggregate root
├── repositories/          # Data access
├── schemas.py             # Pydantic request/response contracts
└── use_cases.py           # Orchestration (or in application/ for cross-module flows)
```

## Cross-Module Orchestration

Flows that span multiple modules live in `application/use_cases/`:

```
application/use_cases/
├── checkout/              # Cart → Order → Payment → Cleanup
├── retry_payment/         # Order → Payment (no cart)
└── webhook/               # Stripe event → Payment → Order
