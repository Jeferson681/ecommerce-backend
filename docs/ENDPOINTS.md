# API Endpoints

Current implemented API surface.

---

## Infrastructure

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Health check |

---

## User

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/users` | — | Create a new user account |
| `GET` | `/users/me` | Bearer | Get current authenticated user |
| `GET` | `/users/{user_id}` | Bearer | Get user by ID (owner or admin) |
| `PATCH` | `/users/{user_id}` | Bearer | Update user profile (owner or admin) |
| `POST` | `/users/{user_id}/change-password` | Bearer | Change account password (owner only) |
| `DELETE` | `/users/{user_id}` | Bearer | Delete user account (owner or admin) |
| `GET` | `/users` | Bearer + Admin | List all users (admin only) |

---

## Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/token` | — | Authenticate and receive access + refresh tokens |
| `POST` | `/auth/refresh` | — | Exchange refresh token for a new access token |
| `POST` | `/auth/logout` | Bearer | Validate refresh token (no revocation) |

---

## Product

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/products` | — | List products with optional filters |
| `GET` | `/products/{product_id}` | — | Get product by ID |
| `POST` | `/products` | Bearer + Admin | Create a new product |
| `PATCH` | `/products/{product_id}` | Bearer + Admin | Update an existing product |
| `DELETE` | `/products/{product_id}` | Bearer + Admin | Remove a product |

**Query parameters for `GET /products`:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | `int` | Page number (1-based) |
| `per_page` | `int` | Items per page (max 100) |
| `q` | `string` | Search query (name and description) |
| `category` | `string` | Filter by category |
| `sort` | `enum` | Sort order: `price_asc`, `price_desc`, `newest` |

---

## Cart

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/cart` | Bearer | Get current user's cart |
| `POST` | `/cart/items` | Bearer | Add item to cart |
| `PATCH` | `/cart/items/{item_id}` | Bearer | Update item quantity |
| `DELETE` | `/cart/items/{item_id}` | Bearer | Remove item from cart |
| `POST` | `/cart/merge` | Bearer | Merge anonymous cart items after login |

---

## Order

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/orders/checkout` | Bearer | Complete checkout (converts cart to order) |
| `POST` | `/orders/{order_id}/retry-payment` | Bearer | Retry payment for a failed order |
| `GET` | `/orders` | Bearer | List current user's orders |
| `GET` | `/orders/{order_id}` | Bearer | Get order by ID (owner or admin) |

**Notes:**
- Checkout supports `Idempotency-Key` header for idempotent requests.
- Retry-payment supports payment method replacement.

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
| `POST` | `/webhooks/stripe` | — | Stripe webhook receiver (signature verified) |

---

## Future Roadmap

### User
- `GET /users/me/addresses`


### Order
- `POST /orders/{order_id}/cancel`

### Payment
- Payment methods management
-

### Admin Analytics
- `GET /admin/dashboard`
- `GET /admin/stats/orders`
- `GET /admin/stats/payments`
-
