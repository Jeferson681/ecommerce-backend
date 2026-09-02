# Project Structure

Navigation map of the repository — where each major component lives.

```text
ecommerce-backend/
├── backend/                        # FastAPI backend (API + domain)
│   └── app/
│       ├── main.py                 # Application entry point
│       ├── api/                    # HTTP / presentation layer
│       ├── application/            # Cross-domain use cases
│       ├── modules/                # Domain modules
│       ├── core/                   # Shared application components
│       ├── infrastructure/         # Infrastructure layer
│       ├── idempotency/            # Idempotency key management
│       ├── observability/          # Logging and health probes
│       └── uow/                    # Unit of Work transaction manager
│
├── frontend/                       # Next.js storefront
│   ├── app/                        #   Routes and pages
│   ├── core/                       #   Shared configuration and utilities
│   ├── modules/                    #   Feature modules
│   ├── shared/                     #   UI primitives and layout
│   └── public/                     #   Static assets
│
├── alembic/                        # Database migrations
│   └── versions/
│
├── tests/                          # Test suite
│   ├── unit/
│   ├── integration/
│   └── workflows/
│
├── docs/                           # Documentation
│   ├── architecture/               #   ADRs and architecture decisions
│   └── assets/                     #   UX evidence and supporting assets
│
├── .github/                        # CI/CD workflows
│   └── workflows/
│
├── docker/                         # Dockerfiles and entrypoint scripts
├── scripts/                        # Maintenance and seeding scripts
│
├── docker-compose.yml              # Service orchestration
├── openapi.yaml                    # API contract
├── pyproject.toml                  # Python project configuration
├── requirements.txt                # Runtime dependencies
├── requirements-dev.txt            # Development dependencies
├── Makefile                        # Development commands
├── pytest.ini                      # Pytest markers
├── .pre-commit-config.yaml         # Code quality hooks
├── .env.example                    # Environment variable template
└── README.md                       # Project overview
```

## Where to find things

| Component | Location |
|-----------|----------|
| HTTP endpoints | `backend/app/api/` |
| Domain modules and business logic | `backend/app/modules/` |
| Cross-domain use cases | `backend/app/application/use_cases/` |
| Shared application components | `backend/app/core/` |
| Database engine/session factory (canonical owner) | `backend/app/core/database.py` |
| Database session dependency (FastAPI) | `backend/app/infrastructure/db/` |
| FastAPI dependencies (DI wiring) | `backend/app/modules/auth/deps.py`, `backend/app/infrastructure/db/dependencies.py`, `backend/app/uow/dependencies.py` |
| Idempotency key management | `backend/app/idempotency/` |
| Logging and health probes | `backend/app/observability/` |
| Transaction management | `backend/app/uow/` |
| Frontend storefront | `frontend/` |
| Database migrations | `alembic/` |
| Tests | `tests/` |
| Documentation and ADRs | `docs/` |
| CI/CD automation | `.github/workflows/` |
| Docker deployment | `docker/`, `docker-compose.yml` |
| API contract | `openapi.yaml` |
| Python configuration | `pyproject.toml`, `requirements*.txt` |

For architectural rationale and how components relate, see `docs/architecture/`.
