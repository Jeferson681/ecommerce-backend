# E-commerce Backend API

A modular FastAPI backend for e-commerce platforms with domain-driven design, built with SQLAlchemy 2.x and comprehensive test coverage.

## Prerequisites

- Python 3.12+
- pip or poetry
- SQLite (included) or PostgreSQL

## Installation

```bash
# Clone and setup
git clone <repository>
cd ecommerce-backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
DATABASE_URL=sqlite:///./ecommerce.db
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=30
```

## Running

```bash
# Apply migrations
alembic upgrade head

# Start development server
python -m uvicorn app.main:app --reload
```

Server available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app
```

## Project Structure

- `app/core/` - Configuration, database, security, exceptions
- `app/modules/` - Domain modules (user, product, auth)
- `app/api/` - HTTP routers and schemas
- `app/application/` - Unit of Work transaction management
- `tests/` - Unit and integration tests

See [docs/](./docs/) for detailed architecture documentation.

## Tech Stack

- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Alembic
- pytest

## Implemented Features

- User management (create, read, update, delete, password change)
- Product catalog (create, read, update, delete)
- JWT authentication with token validation
- Typed exception handling with HTTP status mapping
- Unit of Work pattern for atomic transactions
- Request logging and observability

## Development

```bash
# Format and lint
pre-commit run --all-files

# Type checking
mypy app/

# Security scan
bandit -r app/
```

## Documentation

- [Architecture](./docs/ARCHITECTURE.md) - System design and folder structure
- [Endpoints](./docs/ENDPOINTS.md) - API reference
- [Technical Docs](./docs/README.md) - Complete technical documentation

## License

MIT
