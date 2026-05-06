# Endpoints

## user

- [POST] /users → create_user
- [GET] /users/{user_id} → get_user
- [PATCH] /users/{user_id} → update_user
- [DELETE] /users/{user_id} → delete_user

## auth

- [POST] /auth/token → login
- [POST] /auth/logout → logout

## product

- [GET] /products → list_products
- [GET] /products/{id} → get_product

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
