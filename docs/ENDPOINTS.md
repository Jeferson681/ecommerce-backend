# Endpoints

## User

### Public

- [POST] /users
  Register a new user account.

### Authenticated

- [GET] /users/me
  Return the currently authenticated user profile.

- [GET] /users/{user_id}
  Return a specific user profile.
  Access: owner or admin.

- [PATCH] /users/{user_id}
  Update user profile data.
  Access: owner or admin.

- [POST] /users/{user_id}/change-password
  Change account password.
  Access: owner only.

- [DELETE] /users/{user_id}
  Delete or deactivate a user account.
  Access: owner or admin.

### Admin

- [GET] /users
  List all users.

#### Future

- [GET] /users
  List all users with pagination and filtering.

---

## Auth

### Public

- [POST] /auth/token
  Authenticate user and issue access token.

- [POST] /auth/refresh
  Refresh access token using refresh token.

### Authenticated

- [POST] /auth/logout
  Invalidate current authentication session/token.

#### Future

- [GET] /auth/session
  Return current authenticated session state and role information.

---

## Product

### Public

- [GET] /products
  List available products.

  Query params:
  - `page` (>= 1)
  - `per_page` (1-100)

- [GET] /products/{id}
  Return product details.

### Admin

- [POST] /products
  Create a new product.

- [PATCH] /products/{id}
  Update product information or stock.

- [DELETE] /products/{id}
  Remove or deactivate a product.

#### Future

#### Storefront queries

- [GET] /products?q={query}
  Search products by name or description.

- [GET] /products?category={category}
  Filter products by category.

- [GET] /products?sort={sort}
  Sort products by:
  - `price_asc`
  - `price_desc`
  - `newest`
  - `popular`

#### Storefront endpoints

- [GET] /products/featured
  Return highlighted storefront products.

- [GET] /products/new-arrivals
  Return recently added products.

- [GET] /products/recommended
  Return recommended or curated products.

---

## Cart

### Authenticated

- [GET] /cart
  Return the authenticated user's active cart.

- [POST] /cart/items
  Add a product to the cart or increment quantity.

- [PATCH] /cart/items/{item_id}
  Update cart item quantity.

- [DELETE] /cart/items/{item_id}
  Remove an item from the cart.

#### Future

- [POST] /cart/items/{item_id}/increment
  Increment cart item quantity by one.

- [POST] /cart/items/{item_id}/decrement
  Decrement cart item quantity by one.
  Removes the item when quantity reaches zero.

---

## Order

### Authenticated

- [POST] /orders/checkout
  Create an order from the current cart.

  Supports `Idempotency-Key` and uses the idempotency repository to reserve, replay, and persist results.

- [GET] /orders
  List orders belonging to the authenticated user.

- [GET] /orders/{id}
  Return details of a specific order.
  Access: owner or admin.

#### Future

#### Admin

- [GET] /admin/orders
  List all orders across the platform.

- [POST] /orders/{id}/cancel
  Cancel an order when allowed by the current order status.

#### Recommended order statuses

- `pending`
- `paid`
- `processing`
- `shipped`
- `delivered`
- `cancelled`

---

## Payment

### Authenticated

- [POST] /payments
  Process payment for an order.

  Requires idempotency protection.

- [GET] /payments/{id}
  Return payment details.
  Access: owner or admin.

### Admin

- [GET] /admin/payments
  List and inspect platform payments.

#### Future

#### Recommended payment statuses

- `pending`
- `authorized`
- `paid`
- `failed`
- `refunded`

---

## Address

#### Future

#### Authenticated

- [GET] /users/me/addresses
  List saved addresses.

- [POST] /users/me/addresses
  Create a new address.

- [PATCH] /users/me/addresses/{id}
  Update an address.

- [DELETE] /users/me/addresses/{id}
  Remove an address.

---

## Admin Analytics

#### Future

#### Admin

- [GET] /admin/dashboard
  Return aggregated platform metrics.

- [GET] /admin/stats/orders
  Return order statistics.

- [GET] /admin/stats/payments
  Return payment statistics.

- [GET] /admin/stats/products
  Return product statistics.
