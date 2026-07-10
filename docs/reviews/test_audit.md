# Test Audit Report — Pre-Deployment

## Summary

**Overall assessment:** The test suite provides solid coverage of happy-path business flows, authentication security, idempotency replay protection, and stock atomicity. However, it has significant gaps in failure-path validation and regression protection for the two bugs recently fixed (BUG-001, BUG-002).

**Existing strengths:**
- Authentication: login, logout, refresh, token rotation, replay attack protection — thoroughly tested (12+ tests)
- Idempotency: enforcement, replay returns identical response, no duplicate orders/payments — well covered
- Stock: atomic decrement, concurrent safety, insufficient stock, increment — comprehensive
- Webhook: signature validation, approval flow, missing payment — good coverage
- Transaction rollback: flush-phase failure tested with cart and stock verification

**Total findings:** 4

---

# Findings

## TEST-001

**Severity:** High

**Feature:** Checkout — Stripe idempotency key propagation

**Why the current suite is insufficient:**
BUG-001 was a missing `idempotency_key` in the `process_payment()` call. The fix added the parameter to the checkout flow. However, there is no test that verifies the idempotency key reaches Stripe's `PaymentIntent.create()` call.

The existing test `test_idempotency_released_after_gateway_error` in `test_idempotency_failure.py` tests a different scenario: it fails on the gateway (no Stripe key configured), observes the key is released, then retries. This test does NOT:
1. Verify that Stripe receives the idempotency key when the gateway is operational.
2. Provide regression protection — a future refactor could accidentally remove `idempotency_key` from the `process_payment()` call again, and zero tests would fail.

The test `test_checkout_creates_order_and_payment` exercises the full checkout flow but validates only that the payment was created and approved in the database — not that the idempotency key was correctly forwarded to the external gateway.

**Runtime risk:**
A regression that removes the idempotency key from the Stripe call would go undetected. In production, this creates a double-charge risk during checkout failures (as documented in BUG-001). Financial impact.

**Suggested minimal test:**
Add a test that verifies `process_payment` receives the idempotency key when called from `checkout()`. For example, monkeypatch `StripeGateway.process_payment` to capture the `idempotency_key` argument and assert it matches the one provided in the checkout request header:

```python
def test_checkout_passes_idempotency_key_to_gateway(monkeypatch):
    captured_keys = []

    def tracking_process_payment(self, *, request, idempotency_key=None):
        captured_keys.append(idempotency_key)
        return PaymentGatewayResult(
            provider_payment_id="pi_test",
            status=PaymentStatus.APPROVED,
        )

    monkeypatch.setattr(StripeGateway, "process_payment", tracking_process_payment)

    # Perform checkout with known idempotency key
    key = "test-track-key"
    client.post("/orders/checkout", ..., headers={"Idempotency-Key": key})

    assert key in captured_keys
```

---

## TEST-002

**Severity:** High

**Feature:** UnitOfWork — commit-phase rollback

**Why the current suite is insufficient:**
BUG-002 was the `is_active` guard in `UnitOfWork.rollback()` making it a no-op after a failed commit. The fix removed the guard. However, no test validates that `rollback()` works correctly after a commit-phase failure.

The existing test `test_transaction_rollback_on_exception` in `test_critical_backend_checks.py` simulates a failure by monkeypatching `OrderRepository.create_item` to raise an exception. This failure occurs during `session.flush()`, not during `session.commit()`. After a flush failure, `session.is_active` is still `True`, so the rollback works normally. This test does NOT cover the commit-phase failure scenario.

Without a regression test, the fix could be inadvertently reverted or broken by future changes to the `UnitOfWork`.

**Runtime risk:**
A regression that reintroduces the `is_active` guard or similar rollback-blocking behavior would cause idempotency keys to become permanently stuck after a transient database failure during checkout commit. This blocks the user from completing checkout (ValidationError: "Idempotent request already in progress.").

**Suggested minimal test:**
Add a test that monkeypatches `session.commit` to raise an exception after flush succeeds, then verifies:
1. `uow.rollback()` does not raise.
2. The session can execute subsequent queries (e.g., `delete_by_key`).

```python
def test_rollback_after_commit_phase_failure(monkeypatch):
    original_commit = Session.commit

    def failing_commit(self):
        self.flush()  # ensure flush succeeds
        raise OperationalError("Connection lost", None, None)

    monkeypatch.setattr(Session, "commit", failing_commit)

    # Perform checkout that will fail during commit phase
    with pytest.raises(Exception):
        client.post("/orders/checkout", ..., headers={"Idempotency-Key": "test"})

    # Verify the idempotency key was cleaned up (rollback worked)
    r2 = client.post(
        "/orders/checkout",
        ...,
        headers={"Idempotency-Key": "test"},
    )
    # Should NOT return 400 "already in progress"
    assert r2.status_code != 400
```

---

## TEST-003

**Severity:** Medium

**Feature:** Checkout — cart cleanup and stock reservation rollback ordering

**Why the current suite is insufficient:**
In `checkout.py`, `clear_cart()` and `reserve_stock()` are called before `uow.flush()` (line 152). The `reserve_stock` function calls `decrement_stock_if_enough` which executes an UPDATE via `session.execute()`. The `clear_cart` calls `repository.delete(cart)` with `session.flush()`.

The final `uow.commit()` at line 161 is the only point that persists all these changes to the database. If it fails (the BUG-002 scenario), both the cart deletion and stock decrement are uncommitted. With the BUG-002 fix, `rollback()` now correctly resets transaction state. But there is no test that verifies this atomicity property for the cart+stock combination specifically.

The existing test `test_transaction_rollback_on_exception` only tests the case where the exception occurs *before* the cart is cleared (it monkeypatches `create_item`, which is called before `clear_cart`). It does not test the scenario where the failure occurs *after* `clear_cart` and `reserve_stock` have executed but the commit fails.

**Runtime risk:**
If a future refactor changes the ordering of operations or introduces a non-transactional side effect between flush and commit, the cart-stock atomicity could break. The cart could be cleared but the order not created, without any test catching it.

**Suggested minimal test:**
Add a test that forces `uow.commit()` to fail at line 161 (after flush), then verifies:
1. The cart still exists in the database (not deleted).
2. The product stock is unchanged (not decremented).
3. No order was created.

```python
def test_rollback_after_flush_restores_cart_and_stock(monkeypatch):
    def failing_commit(self):
        raise Exception("simulated commit failure")

    monkeypatch.setattr(Session, "commit", failing_commit)

    product_stock_before = get_product_stock(product_id)

    with pytest.raises(Exception):
        client.post("/orders/checkout", ..., headers={"Idempotency-Key": "test"})

    # Cart should still exist
    cart_resp = client.get("/cart", headers=auth_header)
    assert cart_resp.status_code == 200

    # Stock should be unchanged
    assert get_product_stock(product_id) == product_stock_before
```

---

## TEST-004

**Severity:** Medium

**Feature:** Retry-payment with actual failed payment

**Why the current suite is insufficient:**
The `/orders/{order_id}/retry-payment` endpoint has test coverage only for:
- Missing idempotency key returns 400/422 (`test_retry_payment_missing_idempotency_key_returns_400`)
- Replay with same key returns same response (`test_retry_payment_replay_returns_same_response`)

There is no test that:
1. Deliberately creates a failed payment on an order.
2. Calls retry-payment with a new payment method.
3. Verifies the payment status transitions from FAILED to APPROVED.
4. Verifies the order status transitions from PENDING to PAID.

The retry flow requires a specific order state: order must be PENDING and there must be a FAILED payment. Without an integration test, a regression in `get_failed_payment_for_order` or the status transition logic in `retry_payment()` would go undetected.

**Runtime risk:**
A regression in the retry-payment flow would prevent users from retrying failed payments, forcing them to abandon their cart or contact support. The error would likely surface as a 404 ("No failed payment found") or validation error.

**Suggested minimal test:**
Add a test that creates an order with a failed payment, then calls retry-payment with a valid payment method:

```python
def test_retry_payment_after_failed_payment():
    # Create order + failed payment via DB
    # Call retry-payment endpoint
    # Verify: payment status == APPROVED, order status == PAID
```

---

# Conclusion

The automated test suite is **conditionally sufficient** for a production-ready portfolio project.

**Strengths justify confidence in:**
- Authentication security (rotation, replay protection, logout)
- Idempotency enforcement (replay returns cached result, no duplicates)
- Stock atomicity (concurrent safety, insufficient stock rejection)
- Webhook processing (signature validation, status updates)

**Critical gaps remain in failure-path validation:**
- No regression test for BUG-001 (Stripe idempotency key) — **HIGH**
- No regression test for BUG-002 (commit-phase rollback) — **HIGH**
- Cart+stock rollback after commit failure — not tested — **MEDIUM**
- Retry-payment with actual failed payment not tested — **MEDIUM**

The project is deployable **only after the suggested minimal tests are added** for TEST-001 and TEST-002. These tests protect the two bugs that were recently fixed in the audit. Without them, a future refactor could silently reintroduce the defects.
