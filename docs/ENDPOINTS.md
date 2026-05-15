# Endpoints

## user

- [POST] /users → create_user
- [GET] /users/me → get_current_user
- [GET] /users/{user_id} → get_user
- [GET] /users → list_users
- [PATCH] /users/{user_id} → update_user
- [POST] /users/{user_id}/change-password → change_password
- [DELETE] /users/{user_id} → delete_user

## auth

- [POST] /auth/token → login
- [POST] /auth/refresh → refresh_access_token
- [POST] /auth/logout → logout

## product

- [GET] /products → list_products
- [GET] /products/{id} → get_product
- [POST] /products → create_product
- [PATCH] /products/{id} → update_product
- [DELETE] /products/{id} → delete_product

## cart

- [GET] /cart → get_cart
- [POST] /cart/items → add_item
- [PATCH] /cart/items/{item_id} → update_item
- [DELETE] /cart/items/{item_id} → remove_item

## order

- [POST] /orders/checkout → checkout
- [GET] /orders → list_orders
- [GET] /orders/{id} → get_order

## payment

- [POST] /payments → process_payment
- [GET] /payments/{id} → get_payment
