# Endpoints

Snapshot: current implemented API

## User

- [POST] /users
- [GET] /users/me
- [GET] /users/{user_id}
- [PATCH] /users/{user_id}
- [POST] /users/{user_id}/change-password
- [DELETE] /users/{user_id}
- [GET] /users

## Auth

- [POST] /auth/token
- [POST] /auth/refresh
- [POST] /auth/logout

## Product

- [GET] /products
- [GET] /products/{id}
- [POST] /products
- [PATCH] /products/{id}
- [DELETE] /products/{id}

Query params supported today:
- `page`
- `per_page`

## Cart

- [GET] /cart
- [POST] /cart/items
- [PATCH] /cart/items/{item_id}
- [DELETE] /cart/items/{item_id}

## Order

- [POST] /orders/checkout
- [GET] /orders
- [GET] /orders/{id}

Notes:
- checkout supports `Idempotency-Key`

## Payment

- [POST] /payments
- [GET] /payments/{id}
- [GET] /admin/payments

Notes:
- payment flow uses idempotency

## FUTURE

### User
- `/users/me/addresses`

### Auth
- `/auth/session`

### Product
- search, category filter, sort, featured, new arrivals, recommended

### Cart
- `/cart/items/{item_id}/increment`
- `/cart/items/{item_id}/decrement`

### Order
- `/admin/orders`
- `/orders/{id}/cancel`

### Payment
- status refinements

### Admin Analytics
- `/admin/dashboard`
- `/admin/stats/orders`
- `/admin/stats/payments`
- `/admin/stats/products`
