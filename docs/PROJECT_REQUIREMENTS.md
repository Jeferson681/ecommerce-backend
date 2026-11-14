# Project Requirements

## 1. Purpose

This document describes the functional and technical requirements of the e-commerce system. It is a sanitized public representation of the complete working specification used during development; internal planning, validation records, and development-process details have been deliberately omitted.

## 2. Product Scope

The project is a modular e-commerce system composed of:

- a FastAPI backend API;
- a Next.js storefront frontend;
- PostgreSQL persistence for deployed environments;
- Stripe payment processing;
- Docker Compose service orchestration.

The system supports account management, product discovery, shopping carts, checkout, order tracking, payment processing, and operational health checks.

The backend is organized as a modular monolith with User, Product, Cart, Order, Payment, Idempotency, Maintenance, and Observability concerns.

## 3. MVP Scope

The delivered purchase lifecycle is:

```text
Browse products
    → Create account or sign in
    → Add products to cart
    → Synchronize the cart
    → Checkout with an idempotency key
    → Process payment
    → View order and payment status
```

Regular users can browse products, manage their profile, manage carts, complete purchases, retry failed payments, and consult their orders.

The backend includes protected administrative endpoints for platform operations. The administrative dashboard and its complete administrative consumption flows are deferred to the final project stage. The current scope does not introduce new administrative behavior beyond the existing backend surface.

## 4. Functional Requirements

### 4.1 Accounts and authentication

- Anonymous users can create accounts with first name, last name, email, and password.
- Email addresses are unique and normalized before persistence.
- Passwords must satisfy the configured security policy and length constraints.
- Users authenticate with email and password and receive access and refresh JWTs.
- Access tokens expire after 30 minutes by default; refresh tokens expire after 7 days by default.
- Refresh tokens rotate on use, and the previous token is revoked.
- Authenticated users can log out by revoking the submitted refresh token.
- Authenticated users can view and update their own profile.
- Users can change their password after supplying the current password and a valid new password.
- Users can delete their own account; administrators can manage accounts through protected backend operations.

### 4.2 Product catalog

- Public users can list and view products.
- Product listing supports search by name and description.
- Product listing supports category and price-range filtering.
- Product listing supports price and newest-first sorting.
- Product listing supports page and per-page pagination with metadata when pagination parameters are supplied.
- Administrators can create, update, and remove products through protected backend endpoints.
- Product prices must be positive, and stock quantities cannot be negative.
- Products with associated orders cannot be removed.

### 4.3 Shopping cart

- Authenticated users can retrieve their cart.
- Users can add products, update quantities, and remove items.
- A cart is created automatically when the first item is added.
- Local frontend cart items can be merged into the authenticated cart.
- Product activity and available stock are validated during cart operations.
- Cart item quantities must be positive.
- A product appears at most once in a given cart.

### 4.4 Checkout and orders

- Authenticated users can convert a non-empty cart into an order.
- Checkout requires a payment method identifier and an `Idempotency-Key` header.
- Checkout validates product availability and stock before creating the order.
- The order stores item quantities and price snapshots from checkout time.
- Stock is decremented atomically when checkout reserves inventory.
- The cart is cleared after successful checkout processing.
- Orders begin in `pending` status and become `paid` when payment is approved.
- Users can list their own orders and retrieve order details with items and payment history.
- Owners can retry a failed payment for a pending order using an idempotency key.
- Administrative order listing is available through a protected backend endpoint; dashboard consumption is deferred.

### 4.5 Payments

- Checkout creates a payment record and processes it through the payment gateway abstraction.
- Stripe is the concrete payment provider used by the deployed application.
- Payment amounts are positive and expressed to Stripe in USD cents.
- Card and provider errors are represented as failed payments with a failure reason.
- Payment status can be updated asynchronously through a Stripe webhook.
- Webhook payloads are verified before being processed.
- Payment history is available with order details and through the protected administrative payments endpoint.

### 4.6 Health and readiness

- `GET /healthz` provides a liveness response when the application is running.
- `GET /readyz` checks database connectivity and reports readiness details.

## 5. Business Rules

### Identity and authorization

- Email addresses are unique, lowercased, and trimmed.
- Names are trimmed before persistence.
- Passwords contain uppercase, lowercase, numeric, and special characters and are between 8 and 24 characters.
- Passwords are stored only as bcrypt hashes.
- User profile operations are limited to the owner or an administrator according to the operation.
- Product write operations and platform-wide order/payment listings require administrator authorization.
- Inactive users cannot authenticate or use protected endpoints.

### Catalog and inventory

- Product prices must be greater than zero.
- Product stock must be zero or greater.
- Inactive products cannot be purchased.
- Cart quantities must be positive and cannot exceed available stock.
- Checkout uses a conditional atomic stock decrement to protect against concurrent overselling.
- Product text fields are trimmed before persistence.

### Checkout and idempotency

- Checkout cannot proceed with an empty cart.
- Checkout and payment retry require an idempotency key.
- An idempotency key belongs to the user that created it.
- A key cannot be reused with a different request payload.
- Successful repeated requests return the persisted response without re-executing the operation.
- Key reservation occurs before the main workflow to protect against concurrent duplicate execution.
- Failed workflows release their reserved key through a compensating transaction.
- Idempotency records expire after 24 hours.
- Order totals are calculated from the product price snapshot multiplied by item quantity.

### Orders and payments

- Orders start as `pending` and become `paid` after approved payment.
- Payment processing is permitted for pending or failed payments according to the payment workflow.
- Payment retry requires a pending order with a failed payment.
- Stripe statuses are mapped to internal approved, pending, failed, or cancelled payment states.
- Webhook events update the payment identified by the provider payment ID.

### Sessions

- Refresh token rotation revokes the old token before issuing a new pair.
- Refresh token records persist only a SHA-256 hash of the token JTI.
- JWT issuer, audience, expiration, and token type are validated.
- Logout revokes the submitted refresh token.

## 6. Non-Functional Requirements

### Security

- JWT bearer authentication protects private operations.
- Administrative operations require the administrator role.
- Login is limited to 5 requests per minute per client IP.
- Refresh is limited to 10 requests per minute per client IP.
- Stripe webhook signatures use timestamp validation and constant-time HMAC comparison.
- Production requires `JWT_SECRET_KEY` and does not expose stack traces.
- CORS origins are configurable.

### Consistency and transactions

- Write operations use a Unit of Work for transaction management.
- Repositories do not commit or roll back transactions directly.
- Cross-domain workflows coordinate repositories through the Application layer.
- Checkout, payment retry, webhook processing, inventory updates, and idempotency behavior preserve their defined transaction boundaries.

### Observability

- Requests produce structured logs containing method, path, status, duration, and correlation ID.
- Clients can provide `X-Request-ID`; otherwise the application generates one.
- The request ID is returned in the response header and included in logs.
- Liveness and readiness endpoints are available for deployment health checks.

### Reliability and operations

- Alembic manages database schema migrations.
- Migrations run automatically when the backend container starts.
- Expired idempotency records and expired or revoked refresh tokens are cleaned automatically by the maintenance scheduler.
- The same cleanup operation can also be invoked by the maintenance script.
- Docker images include configurable version, commit, and build-date metadata.
- Pre-commit checks enforce formatting, linting, type checking, security scanning, and configuration validation.

## 7. Main User Flows

### Guest purchase

```text
Browse catalog
  → Create account
  → Login
  → Add products to cart
  → Checkout with payment method and Idempotency-Key
  → Stripe payment processing
  → View order status
  → View order history
```

### Local cart synchronization

```text
Add products to local cart
  → Login
  → Merge local items into authenticated cart
  → Continue to checkout
```

### Failed payment retry

```text
Checkout
  → Payment fails
  → Order remains pending
  → Retry payment with a new idempotency-protected request
  → Payment succeeds
  → Order becomes paid
```

### Session renewal

```text
Access token expires
  → Frontend requests token refresh
  → Existing refresh token is validated and revoked
  → New access and refresh tokens are issued
  → Original request is retried
```

### Asynchronous payment update

```text
Stripe event
  → Webhook signature verification
  → Payment lookup by provider ID
  → Payment status update
  → Order status update when payment is approved
```

## 8. Integrations

### PostgreSQL

PostgreSQL 17 is the deployed relational database. SQLAlchemy accesses it through the `psycopg` driver. The database stores users, products, carts, orders, payments, idempotency records, and refresh-token records.

### Stripe

Stripe creates PaymentIntents, processes payment methods received from the frontend, and sends asynchronous status events through webhooks.

### Frontend and backend

The Next.js frontend consumes the FastAPI API, uses Stripe Elements for payment input, manages local cart state, refreshes expired sessions, and displays product, cart, checkout, order, and payment flows.

## 9. Technical Constraints Relevant to Requirements

- The system is a modular monolith and is deployed as a single application stack.
- Domain modules own their models, schemas, repositories, and single-domain use cases.
- Cross-domain workflows use the Application layer.
- Routers are HTTP adapters and do not own business rules.
- Repositories encapsulate persistence operations.
- Unit of Work owns transaction commit and rollback.
- Stock belongs to the Product aggregate rather than a separate inventory service.
- Payment processing depends on the `PaymentGateway` abstraction rather than directly on Stripe in business workflows.
- The Docker Compose stack consists of PostgreSQL, backend, and frontend services with health checks and startup ordering.
- Production configuration is supplied through environment variables.

## 10. Current Scope and Limitations

- The backend API and storefront cover the delivered purchase lifecycle described above.
- The administrative backend surface exists and is protected by role-based authorization, while the dashboard and complete administrative consumption flows are deferred to the final project stage.
- The application serves HTTP by default; production deployments should place a TLS-terminating reverse proxy in front of the services.
- Stripe credentials and webhook configuration are required for live payment processing.
- SQLite is suitable for local development and tests; deployed environments use PostgreSQL.

## Public Documentation Notice

This document is a sanitized public representation of the complete working specification used during development. Internal planning, validation records, and development-process details have been intentionally omitted.
