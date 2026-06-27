# Project Structure

Complete directory tree of the backend codebase.

```text
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
│   ├── application/use_cases/           # Cross-domain workflow orchestration only
│   │   ├── checkout/
│   │   ├── retry_payment/
│   │   └── webhook/
│   │
│   ├── core/                            # Cross-cutting concerns
│   │   ├── config.py
│   │   ├── database.py
│   │   └── exceptions.py
│   │
│   ├── idempotency/                     # Idempotency key management
│   │   ├── domain/models.py
│   │   ├── helpers.py
│   │   ├── repositories/
│   │   └── service.py
│   │
│   ├── modules/                         # Domain modules
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
├── frontend/                            # Next.js demo frontend (visual API demonstration and manual validation)
├── tests/                               # Unit, integration and workflow tests
│   ├── unit/
│   ├── integration/
│   └── workflows/
│
└── alembic/                             # Database migrations
```

---

# Module Anatomy

Each domain module owns its business workflows and follows a consistent structure.

```text
modules/{entity}/
├── domain/models.py       # SQLAlchemy aggregate root
├── repositories/          # Persistence layer
├── schemas.py             # Request/response DTOs
└── services.py            # Module use cases and business workflows
```

Module services:

- own CRUD workflows;
- own domain-specific business rules;
- instantiate their own repositories when appropriate;
- may manage transactions through the provided UnitOfWork.

---

# Cross-Domain Orchestration

Only workflows involving multiple business domains live in `application/use_cases/`.

```text
application/use_cases/
├── checkout/              # Cart → Product → Order → Payment → Idempotency
├── retry_payment/         # Order → Payment → Idempotency
└── webhook/               # Payment → Order
```

Application use cases:

- coordinate multiple domain modules;
- define transaction boundaries across domains;
- sequence business workflows;

They do **not** own domain-specific business rules, which remain inside the corresponding module services.
