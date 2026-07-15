# Deployment Guide

Production deployment instructions for ecommerce-backend.

---

## Prerequisites

Required:

- Docker
- Docker Compose v2+
- Git

Optional:

- Stripe account (for payment processing)
- Domain name with DNS configured

---

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ecommerce-backend
```

### 2. Configure Environment

Copy the example environment file and fill in required values:

```bash
cp .env.example .env
```

Then edit `.env` with your production values.

### 3. Build and Start

```bash
docker compose up --build -d
```

This starts three services:

| Service | Container | Port |
|---|---|---|
| PostgreSQL | `ecommerce-postgres` | 5432 (internal) |
| Backend (FastAPI) | `ecommerce-backend` | 8000 |
| Frontend (nginx) | `ecommerce-frontend` | 3000 |

### 4. Verify Deployment

Check that all services are healthy:

```bash
docker compose ps
```

Expected output — all services should show `Up` and `(healthy)`.

Verify backend health endpoints:

```bash
curl http://localhost:8000/healthz
# {"status": "ok"}

curl http://localhost:8000/readyz
# {"status": "ok", "checks": {"database": "ok"}}
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|---|---|---|
| `POSTGRES_DB` | PostgreSQL database name | `ecommerce` |
| `POSTGRES_USER` | PostgreSQL user | `ecommerce_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `change_me` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | `random-64-char-string` |
| `STRIPE_SECRET_KEY` | Stripe API secret key | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_...` |

### Optional

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Frontend API URL |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated allowed CORS origins |

### Build Metadata (Optional)

| Variable | Default | Description |
|---|---|---|
| `VERSION` | `1.0.0` | Application version |
| `COMMIT` | `unknown` | Git commit hash |
| `BUILD_DATE` | `unknown` | Build timestamp |

---

## Database Migrations

Migrations run **automatically** on container startup via the entrypoint script.

To run migrations manually:

```bash
docker compose exec backend alembic upgrade head
```

To check migration status:

```bash
docker compose exec backend alembic current
```

To rollback the last migration:

```bash
docker compose exec backend alembic downgrade -1
```

---

## Health Endpoints

| Endpoint | Type | Description |
|---|---|---|
| `/healthz` | Liveness | Returns `{"status": "ok"}` when running |
| `/readyz` | Readiness | Returns database connectivity status |

The Docker Compose healthchecks use these endpoints to determine service readiness.

---

## Logs

View logs for all services:

```bash
docker compose logs -f
```

View logs for a specific service:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

---

## Managing the Application

### Stop

```bash
docker compose down
```

### Stop and Remove Volumes (Destructive)

```bash
docker compose down -v
```

**Warning:** This deletes the PostgreSQL data volume. Use with caution.

### Restart a Service

```bash
docker compose restart backend
```

### Rebuild After Changes

```bash
docker compose up --build -d
```

### View Running Processes

```bash
docker compose top
```

---

## Production Notes

### HTTPS

The application serves HTTP only by default. In production, place a reverse proxy (e.g., nginx, Caddy, Traefik) in front of the exposed ports to terminate TLS.

Recommended configuration:

```
Client → Reverse Proxy (TLS) → Backend (port 8000)
                              → Frontend (port 3000)
```

### Debug Mode

Ensure `DEBUG` is **not set to `true`** in the `.env` file for production. The Docker Compose default is `DEBUG: "false"`. Debug mode exposes stack traces to clients and disables the JWT secret key validation.

### CORS Configuration

If the frontend is served from a different domain than the backend, configure the allowed CORS origins:

```env
CORS_ORIGINS=https://shop.example.com,https://admin.example.com
```

### Startup Order

Docker Compose ensures:

1. PostgreSQL starts first and becomes healthy
2. Backend starts after PostgreSQL is healthy, runs migrations, then starts the API
3. Frontend starts after Backend is healthy

### Data Persistence

PostgreSQL data is stored in a Docker named volume (`postgres_data`). This volume persists across restarts.

### Healthchecks

All services have healthchecks configured. Docker Compose waits for PostgreSQL and Backend to be healthy before starting dependent services.

---

## Troubleshooting

### Backend fails to start

Check logs:

```bash
docker compose logs backend
```

Common causes:

- Missing `.env` file
- Missing required environment variables
- PostgreSQL not reachable (check `DATABASE_URL`)
- Migration failure (check `alembic upgrade head` output)

### Database connection refused

Verify PostgreSQL is healthy:

```bash
docker compose ps postgres
```

Check PostgreSQL logs:

```bash
docker compose logs postgres
```

### Migration errors

Run migrations manually:

```bash
docker compose exec backend alembic upgrade head
```

### Frontend returns 404 on page refresh

The nginx configuration handles SPA routing via `try_files` — this is pre-configured in `frontend/nginx.conf`. If issues persist, verify the nginx config is correct.
