# ADR-009: Stripe + PaymentGateway Protocol

## Status

Accepted

## Context

The project requires payment processing for an e-commerce backend. The team needed to choose a payment provider and design an abstraction that allows for future provider changes without rewriting business logic.

## Problem

How to implement payment processing to:
- Simplify MVP development with a proven provider
- Maintain flexibility to switch providers in the future
- Isolate payment provider details from business logic
- Support webhooks and idempotent payment retries

## Decision

Use **Stripe** as the payment provider with a **PaymentGateway protocol**:
- Stripe is integrated for payment intents and webhooks
- A `PaymentGateway` protocol defines the contract
- All payment operations go through the gateway interface
- The gateway can be replaced with another provider (e.g., PayPal, Mercado Pago) without changing business logic

## Justification

- **MVP simplicity**: Stripe provides excellent documentation and SDKs
- **Abstraction**: The PaymentGateway protocol decouples business logic from provider specifics
- **Future-proof**: New providers can be added by implementing the same protocol
- **Webhook support**: Stripe webhooks are well-documented and reliable
- **Idempotency**: Stripe supports idempotency keys, which aligns with the project's idempotency strategy

## Consequences

- Payment logic is isolated in `payment/gateway/` module
- Services depend on the `PaymentGateway` protocol, not Stripe directly
- Webhook processing uses the same gateway abstraction
- Switching providers requires only a new gateway implementation
- Tests can use mock gateways implementing the same protocol
