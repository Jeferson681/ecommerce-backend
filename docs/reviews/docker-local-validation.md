# Docker Validation Report

## Purpose

Document the root cause, engineering decisions, and validation strategy used to stabilize the Docker environment and CI pipeline.

This document is temporary and should be moved to the internal engineering documentation after the solution proves stable.

---

# Problem

The backend container failed during startup with:

```text
ModuleNotFoundError: No module named 'psycopg'
```

The failure propagated to:

- Alembic migrations
- Backend startup
- Healthcheck
- Docker Compose
- Smoke Test workflow

---

# Root Cause

The project depended on a PostgreSQL driver installation strategy that was not reliable across environments.

The Docker image could successfully install dependencies while still producing a runtime where the PostgreSQL driver was unavailable.

The issue became visible only after the container started, causing CI failures even though dependency installation appeared successful.

---

# Engineering Decision

The Docker environment now validates critical runtime dependencies during image construction instead of waiting for container startup.

Validation is performed in two stages:

## Builder stage

Confirms that required Python packages are correctly installed.

Validated modules:

- psycopg
- SQLAlchemy
- Alembic
- FastAPI

---

## Runtime stage

Confirms that the copied runtime environment remains functional.

Validated items:

- psycopg import
- SQLAlchemy import
- Alembic execution
- Uvicorn execution
- SQLAlchemy driver resolution

This prevents packaging or multi-stage copy regressions.

---

# Docker Changes

## requirements.txt

Replaced

```text
psycopg-binary
```

with

```text
psycopg
```

following the current Psycopg recommendation.

---

## Builder image

Added build dependency:

```text
libpq-dev
```

Required whenever Psycopg needs compilation or native PostgreSQL headers.

---

## Runtime image

Added runtime dependency:

```text
libpq5
```

Required by Psycopg to access the PostgreSQL client library.

---

# Validation Strategy

The Docker image must fail during build whenever one of the following becomes invalid:

- PostgreSQL driver unavailable
- SQLAlchemy driver mismatch
- Alembic unavailable
- Uvicorn unavailable
- Broken dependency copy between Docker stages

This intentionally shifts failures from runtime to build time.

---

# Local Validation

The following validations were executed successfully.

## Image build

- Backend image builds successfully.

## Runtime

Container starts successfully.

## Database

- PostgreSQL reachable.
- Alembic migrations execute successfully.

## Backend

- Application starts correctly.
- Healthcheck responds successfully.
- Readiness endpoint responds successfully.

## Frontend

Frontend communicates successfully with backend.

---

# Failures Eliminated

- Missing psycopg module
- Runtime-only dependency failures
- Broken multi-stage package copy
- Incorrect SQLAlchemy PostgreSQL driver
- Hidden Docker packaging regressions

---

# Lessons Learned

The CI pipeline should verify an already validated Docker environment.

The Docker environment itself must be treated as the source of truth.

Development workflow:

```text
Developer
      │
      ▼
Docker Build
      │
      ▼
Local Validation
      │
      ▼
Docker Compose
      │
      ▼
Smoke Test
      │
      ▼
GitHub Actions
```

GitHub Actions is a verification environment, not the primary debugging environment.

---

# Future Recommendations

- Keep build-time dependency validation.
- Keep runtime dependency validation.
- Preserve fail-fast behavior.
- Validate locally before every infrastructure-related commit.
- Avoid introducing CI-specific workarounds when the local environment is healthy.

---

# Files Modified

- requirements.txt
- docker/backend.Dockerfile

---

# Status

Current status:

- Docker build: ✅
- Runtime validation: ✅
- Docker Compose: ✅
- Backend startup: ✅
- Database connection: ✅
- Health endpoints: ✅
- Frontend startup: ✅
- Smoke Test: ✅
- CI pipeline: ✅

---

# Retirement

After a few stable commits, this document should be moved to the project's internal engineering documentation as a historical record of the stabilization effort.
