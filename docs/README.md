# E-commerce Backend - Technical Documentation

A robust, modular-monolith backend for e-commerce platforms built with **FastAPI** and **SQLAlchemy 2.x**, following **Domain-Driven Design** principles with the **Unit of Work** pattern for transaction management.

## 🏗️ Architecture Overview

This project implements a **layered architecture** with clear separation of concerns:

- **Domain Layer**: Business logic and entity models (`modules/*/domain/models.py`)
- **Application Layer**: Use cases and transaction management (`application/uow/`)
- **Infrastructure Layer**: Database and repository implementations (`infrastructure/`, `modules/*/repositories/`)
- **API Layer**: HTTP endpoints and schemas (`api/routers/`, `modules/*/schemas.py`)
- **Core Layer**: Configuration, database setup, exceptions, and security (`core/`)

## 🛠️ Tech Stack

- **Language**: Python 3.12
- **Web Framework**: FastAPI with async/await support
- **ORM**: SQLAlchemy 2.x with Mapped/mapped_column syntax
- **Validation**: Pydantic v2 with custom validators
- **Database**: SQLite (development) / PostgreSQL (production)
- **Migrations**: Alembic for schema versioning
- **Testing**: pytest with fixtures and monkeypatch
- **Code Quality**: ruff, black, mypy, bandit (pre-commit hooks)

## 📦 Project Structure

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed folder structure and module organization.

## 🔑 Key Features

- **Typed Exceptions**: Domain-aware exception classes with HTTP status codes
- **Unit of Work Pattern**: Atomic transaction management with rollback support
- **Repository Pattern**: Clean data access abstraction for each aggregate
- **Modular Design**: Each domain entity (User, Product, Order, etc.) is self-contained
- **Authentication**: JWT-based auth with password hashing and policy validation
- **Request Logging**: Observability through structured request/response logging
- **Idempotency**: Service layer for handling idempotent operations

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Virtual environment

### Setup

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Set DATABASE_URL, JWT_SECRET_KEY, etc.

# Run migrations
alembic upgrade head

# Start server
python -m uvicorn app.main:app --reload
```

### Environment Variables

Required:
- `DATABASE_URL` - Database connection string
- `JWT_SECRET_KEY` - Secret key for JWT token signing
- `JWT_ALGORITHM` - Algorithm for JWT (default: HS256)
- `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` - Token expiry time

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed module structure and design patterns
- **[ENDPOINTS.md](./ENDPOINTS.md)** - Complete API endpoint reference
- **[DECISIONS.md](./DECISIONS.md)** - Architectural decision records (ADRs)

## ✅ Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_user_validation.py
```

## 🔒 Exception Handling

All errors use typed exceptions from `app/core/exceptions.py`:
- `NotFoundError` (404) - Resource not found
- `InvalidPasswordError` (422) - Password validation failed
- `ValidationError` (422) - Schema validation failed
- `AuthenticationError` (401) - Invalid credentials
- `AuthorizationError` (403) - Insufficient permissions

## 📝 Conventions

- **Branch naming**: `feat/feature-name`, `fix/issue-name`, `refactor/name`
- **Commit messages**: Conventional Commits format (`feat:`, `fix:`, `test:`, `refactor:`)
- **Code style**: Enforced by ruff, black, mypy (pre-commit)
- **Comments**: English language for international collaboration
