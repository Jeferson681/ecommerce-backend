# API Endpoints

Complete reference of all HTTP endpoints in the current codebase.

---

## Infrastructure

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/healthz` | — | Liveness probe — application is running |
| `GET` | `/readyz` | — | Readiness probe — database connectivity |

---

## User

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/users` | — | Create a new user account |
| `GET` | `/users/me` | Bearer | Get current authenticated user |
| `GET` | `/users/{user_id}` | Bearer | Get user by ID (owner or admin) |
| `PATCH` | `/users/{user_id}` | Bearer | Update user profile (owner or admin) |
| `PATCH` | `/users/{user_id}/change-password` | Bearer | Change account password with current-password confirmation (owner only) |
| `DELETE` | `/users/{user_id}` | Bearer | Delete user account (owner or admin) |
| `GET` | `/users` | Bearer + Admin | List all users (admin only) |

---

## Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/token` | — | Login — receive access + refresh tokens |
| `POST` | `/auth/refresh` | — | Exchange refresh token for new access token |
| `POST` | `/auth/logout` | Bearer | Revoke the submitted refresh token and end the current session |

---

## Product

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/products` | — | List products with optional filters; paginated envelope (`items`/`total`/`page`/`per_page`/`total_pages`) when `page`/`per_page` provided |
| `GET` | `/products/{product_id}` | — | Get product by ID |
| `POST` | `/products` | Bearer + Admin | Create a new product |
| `PATCH` | `/products/{product_id}` | Bearer + Admin | Update an existing product |
| `DELETE` | `/products/{product_id}` | Bearer + Admin | Remove a product |

**Query parameters for `GET /products`:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | `string` | Search query (name and description) |
| `category` | `string` | Filter by category |
| `sort` | `enum` | Sort order: `price_asc`, `price_desc`, `newest` |
| `page` | `int` | Page number (1-based). If only `page` is provided, `per_page` defaults to 24. |
| `per_page` | `int` | Items per page (max 100) |

---

## Cart

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/cart` | Bearer | Get current user's cart |
| `POST` | `/cart/items` | Bearer | Add item to cart (auto-creates cart if needed) |
| `PATCH` | `/cart/items/{item_id}` | Bearer | Update item quantity |
| `DELETE` | `/cart/items/{item_id}` | Bearer | Remove item from cart |
| `POST` | `/cart/merge` | Bearer | Merge local/anonymous items into authenticated cart |

---

## Order

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/orders/checkout` | Bearer | Complete checkout — converts cart to order |
| `POST` | `/orders/{order_id}/retry-payment` | Bearer | Retry payment for a failed order |
| `GET` | `/orders` | Bearer | List current user's orders |
| `GET` | `/orders/{order_id}` | Bearer | Get order by ID with items and payments (owner or admin) |

**Notes:**
- `POST /orders/checkout` requires `Idempotency-Key` header.
- `POST /orders/{order_id}/retry-payment` requires `Idempotency-Key` header.
- Responses include `payments[]` array with full payment history for each order.

---

## Admin

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/admin/orders` | Bearer + Admin | List all platform orders |
| `GET` | `/admin/payments` | Bearer + Admin | List all platform payments |

---

## Webhooks

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/webhooks/stripe` | — | Stripe webhook receiver (HMAC signature verified) |

---

## Status Codes

| Code | Meaning |
|------|---------|
| `201` | Created (POST responses) |
| `200` | Success (GET, PATCH responses) |
| `204` | No content (DELETE, logout) |
| `400` | Validation error |
| `401` | Authentication required or invalid credentials |
| `403` | Insufficient permissions |
| `404` | Resource not found |
| `422` | Schema validation failure |
| `500` | Internal server error |
