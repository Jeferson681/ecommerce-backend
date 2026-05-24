# Endpoints

## User

### Public
- [POST] /users
  Register a new user account.

### Authenticated User
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
  List all users with pagination and filtering.

---

## Auth

### Public
- [POST] /auth/token
  Authenticate user and issue access token.

- [POST] /auth/refresh
  Refresh access token using refresh token.

### Authenticated User
- [POST] /auth/logout
  Invalidate current authentication session/token.

---

## Product

### Public
- [GET] /products
  List available products.

- [GET] /products/{id}
  Return product details.

### Admin
- [POST] /products
  Create a new product.

- [PATCH] /products/{id}
  Update product information or stock.

- [DELETE] /products/{id}
  Remove or deactivate a product.

---

## Cart

### Authenticated User
- [GET] /cart
  Return the authenticated user's active cart.

- [POST] /cart/items
  Add a product to the cart or increment quantity.

- [PATCH] /cart/items/{item_id}
  Update cart item quantity.

- [DELETE] /cart/items/{item_id}
  Remove an item from the cart.

---

## Order

### Authenticated User
- [POST] /orders/checkout
  Create an order from the current cart.

- [GET] /orders
  List orders belonging to the authenticated user.

- [GET] /orders/{id}
  Return details of a specific order.
  Access: owner or admin.

### Admin
- [GET] /admin/orders
  List all orders across the platform.

---

## Payment

### Authenticated User
- [POST] /payments
  Process payment for an order.
  Requires idempotency protection.

- [GET] /payments/{id}
  Return payment details.
  Access: owner or admin.

### Admin
- [GET] /admin/payments
  List and inspect platform payments.
