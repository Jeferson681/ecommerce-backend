# Bug Audit Report — Final Pre-Deployment

## Summary

| Category    | Count |
|-------------|-------|
| **Total findings** | **2** |
| Critical    | 1     |
| High        | 1     |
| Medium      | 0     |
| Low         | 0     |

---

# Findings

## BUG-001

**Severity:** Critical

**Files:**
- `backend/app/application/use_cases/checkout/checkout.py` (lines 137–142)
- `backend/app/modules/payment/services.py` (lines 53–91)
- `backend/app/modules/payment/gateway/stripe_gateway.py` (lines 100–148)

**Description:**
The `checkout()` use case calls `process_payment()` without propagating the `idempotency_key` to Stripe. This causes `stripe.PaymentIntent.create()` to be called with `idempotency_key=None`, disabling Stripe-side idempotency protection.

If the checkout's local database transaction fails *after* Stripe has successfully charged the customer, the following sequence occurs:

1. Stripe has a confirmed PaymentIntent — the card was charged.
2. The local `uow.commit()` fails (e.g., transient DB error).
3. The `except Exception` block in `checkout()` rolls back local state (order, stock, payment) and deletes the application-layer idempotency key.
4. The customer or frontend retries (the idempotency key was deleted, so `try_order_response_replay` returns `None`).
5. A fresh checkout is attempted: new order, new payment, new Stripe call — **without any idempotency key**.
6. Stripe processes a **second charge**.

**Evidence:**

In `checkout.py`, lines 137–142:
```python
payment = process_payment(
    payment_id=payment.id,
    payment_method_id=payment_method_id,
    uow=uow,
    gateway=gateway,
    # idempotency_key NOT passed
)
```

Compare with `retry_payment.py`, lines 83–89, which *does* pass the key:
```python
payment = process_payment(
    payment_id=payment.id,
    payment_method_id=payment_method_id,
    uow=uow,
    gateway=gateway,
    idempotency_key=idempotency_key,  # correctly passed
)
```

The `stripe_gateway.py` line 121 shows the key is forwarded to Stripe:
```python
intent = stripe.PaymentIntent.create(
    ...
    idempotency_key=idempotency_key,  # None from checkout
)
```

The gateway result is processed locally at `checkout.py` lines 144–146:
```python
if payment.status == PaymentStatus.APPROVED:
    order.status = OrderStatus.PAID
```

If `uow.commit()` at line 161 fails **after** Stripe returned `APPROVED`, the customer is charged but no local state is persisted. The cleanup at lines 164–178 deletes the idempotency key and re-raises:

```python
except Exception:
    if idempotency_key is not None:
        try:
            uow.rollback()
            idempotency_repository.delete_by_key(idempotency_key, user_id)
            uow.commit()
        except Exception as cleanup_err:
            logger.exception(...)
    raise
```

There is **no compensation action** (no Stripe refund/void) in this path.

**Runtime impact:**
Double charge to the customer with no local order or payment record to reconcile. Requires manual Stripe intervention to refund one charge.

**Steps to reproduce:**
1. Ensure working Stripe integration (real or deterministic mock that always returns APPROVED).
2. Start a checkout for a user with items in cart.
3. Make the `uow.commit()` call at `checkout.py:161` fail (e.g., monkeypatch `session.commit` to raise, or force a DB connection drop).
4. Observe that the first Stripe call succeeds (card charged).
5. Retry the same checkout with a new idempotency key.
6. Stripe is called again and the card is charged a second time.

**Minimal fix:**
Pass `idempotency_key` to `process_payment()` in `checkout.py`:

```python
payment = process_payment(
    payment_id=payment.id,
    payment_method_id=payment_method_id,
    uow=uow,
    gateway=gateway,
    idempotency_key=idempotency_key,  # <-- add this
)
```

This ensures Stripe's `PaymentIntent.create` is called with the same idempotency key on retry, preventing duplicate charges.

---

## BUG-002

**Severity:** High

**Files:**
- `backend/app/application/use_cases/checkout/checkout.py` (lines 93–98, 164–178)
- `backend/app/idempotency/repositories/idempotency_repository.py` (lines 30–52)
- `backend/app/idempotency/helpers.py` (lines 105–119)

**Description:**
The checkout's idempotency key reservation uses `begin_nested()` (a savepoint) inside `IdempotencyRepository.claim()`. After the savepoint is released, the idempotency record is still pending in the outer session transaction. The `checkout()` function then calls `uow.commit()` at line 101 to persist the key to the database.

If the checkout fails **between** the successful Stripe charge (Bug-001 scenario) and `uow.commit()`, the idempotency key was already committed to the database at line 101 (it survived the rollback at line 167 because it was committed before the rollback). But the `delete_by_key` at line 169 is issued **after** `uow.rollback()` at line 167 leaves the session in an invalid state.

In `unit_of_work.py` line 58:
```python
def rollback(self) -> None:
    if self._session is not None and self._session.is_active:
        self._session.rollback()
```

After a failed commit, `is_active` is `False`, so `rollback()` is a **no-op**. The session is NOT reset to a clean state. Subsequent `execute()` calls (like the DELETE from `delete_by_key`) can fail or behave unexpectedly.

**Evidence:**

`checkout.py` lines 164–171:
```python
except Exception:
    if idempotency_key is not None:
        try:
            uow.rollback()  # <-- no-op if commit failed at line 161
            idempotency_repository.delete_by_key(
                idempotency_key,
                user_id,
            )
            uow.commit()  # <-- may succeed or raise; session state unpredictable
```

`idempotency_repository.py` lines 85–93:
```python
def delete_by_key(self, key: str, user_id: int) -> bool:
    statement = delete(IdempotencyKey).where(
        IdempotencyKey.key == key,
        IdempotencyKey.user_id == user_id,
    )
    result = self.session.execute(statement)
    self.session.flush()
    return ...
```

If the session is in an invalid state (post-failed-commit without proper rollback), executing the DELETE may raise an exception (e.g., `"This session is in 'prepared' state"`). The inner `except Exception` catches it and logs it, but the original exception is then re-raised. The idempotency key **remains in the database** with `response_status IS NULL` and `response_body IS NULL` — a "stuck" key.

**Runtime impact:**
A stuck idempotency key blocks subsequent checkout attempts for that user+key combination. The `reserve_idempotency_key()` function (`helpers.py:47-82`) will see the existing record with `response_status=None` and raise `"Idempotent request already in progress."`. This returns a 400/ValidationError to the user, who cannot complete checkout even though the cart still exists.

Additionally, if the Stripe payment was already charged (Bug-001 scenario), the user is stuck: charged by Stripe but cannot retry checkout locally, and no refund mechanism exists.

**Steps to reproduce:**
1. Environment as described in Bug-001.
2. Initiate checkout with idempotency key "test-key-1".
3. Force `uow.commit()` at `checkout.py:161` to fail.
4. Observe the cleanup path: `uow.rollback()` is a no-op (session not active after failed commit).
5. `idempotency_repository.delete_by_key()` fails because the session is in an invalid state.
6. The inner `except` catches it, logs it, and re-raises the original exception.
7. The idempotency key "test-key-1" remains in DB with `response_status=NULL`.
8. Retry with the same idempotency key → ValidationError("Idempotent request already in progress.").

**Minimal fix:**
In `unit_of_work.py`, change `rollback()` to always reset the session, not only when `is_active`:

```python
def rollback(self) -> None:
    if self._session is not None:
        try:
            self._session.rollback()
        except Exception:
            if self._session.is_active:
                self._session.close()
                logger.exception(...)
```

Or, more targeted: in the `checkout.py` cleanup block, ensure the session is reset before attempting cleanup:

```python
except Exception:
    if idempotency_key is not None:
        try:
            # Close and reopen to ensure clean state
            uow.session.close()
            # The session factory creates a new connection/session
            new_session = uow.session_factory()
            uow.attach(new_session)
            idempotency_repository.delete_by_key(...)
            uow.commit()
        except Exception as cleanup_err:
            ...
    raise
```

---

# Conclusion

The project has **two real, reproducible defects** that affect runtime behavior:

1. **Critical — BUG-001**: Missing Stripe idempotency key in the checkout flow creates a double-charge risk when the local database transaction fails after Stripe has approved the payment. This is a financial-impact bug that affects customers and requires manual Stripe intervention to resolve.

2. **High — BUG-002**: The error recovery path in checkout uses `uow.rollback()` which becomes a no-op after a failed commit, leaving the database session in an invalid state. The subsequent idempotency key cleanup fails silently, leaving a "stuck" key that blocks the user from retrying checkout.

**Both bugs require fixes before deployment.**

BUG-001 alone is a deployment blocker due to the direct financial impact (double charge). BUG-002 compounds the issue by preventing the user from recovering after the failure.

No other runtime defects meeting the audit criteria were found in the reviewed codebase.

---

# Technical Validation

## BUG-001

### 1. Is the bug real?

**Confirmed.**

The `checkout()` function at `checkout.py:137-142` calls:
```python
payment = process_payment(
    payment_id=payment.id,
    payment_method_id=payment_method_id,
    uow=uow,
    gateway=gateway,
)
```

The `idempotency_key` parameter is not passed. The `process_payment()` function at `services.py:80-84` forwards the key to the gateway:
```python
result = process_gateway_payment(
    gateway=gateway,
    request=request,
    idempotency_key=idempotency_key,  # None
)
```

This means `stripe.PaymentIntent.create()` is called without an idempotency key (line 121 of `stripe_gateway.py`). In contrast, `retry_payment.py:83-89` correctly passes the key.

The failure scenario is real: if `uow.commit()` at `checkout.py:161` raises after Stripe has returned `APPROVED`, the cleanup at lines 164-178 deletes the local idempotency key and re-raises. On retry with the same key, `try_order_response_replay` returns `None` (key was deleted), and a new Stripe call is made without idempotency protection.

### 2. Root Cause

**Correct.**

The root cause is the missing `idempotency_key` argument in the `process_payment()` call. The function accepts the parameter (keyword-only, defaults to `None`), and `retry_payment.py` demonstrates the correct usage.

### 3. Reproduction

**Sufficient, with one clarification.**

Step 5 says "Retry the same checkout with a new idempotency key." This reproduces the double charge because a different key bypasses Stripe idempotency. However, even retrying with the **same** key would not prevent the double charge without the fix, because the local idempotency record was already deleted from the database (step 3 in the sequence), so the retry would proceed to call Stripe without a key.

With the fix applied, retrying with the same key would hit Stripe's idempotency cache and return the original result without a second charge.

### 4. Proposed Fix

**Correct.**

Adding `idempotency_key=idempotency_key` to the `process_payment()` call is the correct fix. The function signature at `services.py:53-60` accepts `idempotency_key: str | None = None` as a keyword-only argument. The `process_gateway_payment` helper at `helpers.py:25-33` forwards it to the gateway. The `stripe_gateway.py:121` passes it to `stripe.PaymentIntent.create()`.

### 5. Better Fix

No better fix exists. This is a one-line change that adds a single keyword argument. It is the smallest possible change, has zero production risk, preserves the existing architecture, preserves public APIs, and preserves existing business behavior.

### 6. Side Effects

**None.**

The `idempotency_key` parameter defaults to `None`. Passing the key explicitly is additive — it only changes behavior when the key is present, and only in Stripe's PaymentIntent creation. No regression risk. No behavioral change for non-idempotent requests (though `idempotency_key` is required by the router, not optional). No transactional or consistency issues.

### 7. Final Verdict

- Status: **Confirmed**
- Recommended Fix: **Original fix** (pass `idempotency_key` to `process_payment`)

---

## BUG-002

### 1. Is the bug real?

**Confirmed.**

The `uow.rollback()` at `unit_of_work.py:57-59` guards with `self._session.is_active`:
```python
def rollback(self) -> None:
    if self._session is not None and self._session.is_active:
        self._session.rollback()
```

When `session.commit()` fails during the **commit phase** (as opposed to the flush phase), SQLAlchemy sets `is_active = False`. In this state, `rollback()` is a no-op, and subsequent `execute()` calls (such as `delete_by_key`) raise `"This session is in 'prepared' state"` or similar. The cleanup in `checkout.py:167-171` fails:

```python
uow.rollback()  # no-op
idempotency_repository.delete_by_key(...)  # raises
uow.commit()  # not reached
```

The inner `except` at line 173 catches the error from `delete_by_key`, logs it, and the original exception is re-raised. The idempotency key remains in the database with `response_status=NULL`. On retry, `reserve_idempotency_key()` in `helpers.py:47-82` finds the existing record and raises `"Idempotent request already in progress."`.

**Important nuance:** This bug only manifests when the failure occurs during the **commit phase** of SQLAlchemy's two-phase commit protocol (after flush succeeds but before the database confirms the transaction). If the failure occurs during the **flush phase** (e.g., constraint violation), `is_active` remains `True`, `rollback()` succeeds, and `delete_by_key()` works correctly. The report does not distinguish between these two failure modes, but the bug is real in the commit-phase failure case.

### 2. Root Cause

**Partially correct.**

The report correctly identifies that `uow.rollback()` is a no-op when `is_active` is False after a failed commit. However, the description conflates the idempotency key's savepoint reservation (`begin_nested()` at `idempotency_repository.py:42`) with the rollback issue. The savepoint behavior is not actually relevant to the bug. The root cause is simply that `uow.rollback()` does not handle sessions in non-active state, and the cleanup code in `checkout.py` relies on it to reset the session before executing `delete_by_key`.

The actual root cause is: **`UnitOfWork.rollback()` assumes the session is always in an active state, but after a commit-phase failure, `session.is_active` is `False`, making `rollback()` a no-op.**

### 3. Reproduction

**Partially correct.**

The reproduction steps conflate BUG-001 and BUG-002. Step 1 says "Environment as described in Bug-001" which involves Stripe. The idempotency key stuck issue (BUG-002) is independent of Stripe — it only requires a commit-phase failure at line 161.

Corrected reproduction steps:
1. Ensure the database connection is available.
2. Start a checkout with idempotency key "test-key-1" for a user with items in cart.
3. Force the `uow.commit()` at `checkout.py:161` to fail during the **commit phase** (not the flush phase). For example, monkeypatch the session's `connection.commit` to raise an `OperationalError` after flush succeeds.
4. Observe that the `except` block at line 164 executes.
5. `uow.rollback()` at line 167 is a no-op (session.is_active is False after the commit-phase failure).
6. `idempotency_repository.delete_by_key()` at line 168 raises because the session cannot execute queries.
7. The inner `except` at line 173 logs the error, and the original exception is re-raised.
8. The idempotency key "test-key-1" remains in the database with `response_status=NULL`.

### 4. Proposed Fix

**Incorrect.**

The report offers two alternatives:

**Alternative 1 (fix in UnitOfWork):**
```python
def rollback(self) -> None:
    if self._session is not None:
        try:
            self._session.rollback()
        except Exception:
            if self._session.is_active:
                self._session.close()
                logger.exception(...)
```

This has a logic error: if `self._session.rollback()` raises because `is_active` is False, the `except` block checks `self._session.is_active` — which is still False — so `close()` is never called. The fix does not solve the problem.

**Alternative 2 (fix in checkout.py):**
```python
uow.session.close()
new_session = uow.session_factory()
uow.attach(new_session)
```

This is overly invasive. It bypasses the UnitOfWork abstraction and directly manipulates session lifecycle. It also requires the session factory to be callable (which it is, but this couples the cleanup code to the factory). It closes the session but does not properly handle cleanup of the underlying connection.

### 5. Better Fix

The simplest correct fix is in `unit_of_work.py`. SQLAlchemy's `Session.rollback()` is designed to be safe to call regardless of session state. When called on a non-active session, it:
- Cleans up the existing (closed/errored) transaction.
- Begins a new transaction.
- Does not raise.

Therefore, the `is_active` guard is unnecessary. Remove it:

```python
def rollback(self) -> None:
    if self._session is not None:
        self._session.rollback()
```

This is a one-line change (removing `and self._session.is_active`). It is safer than the proposed alternatives because:
1. It relies on SQLAlchemy's built-in defensive programming (not custom logic).
2. It is the smallest possible change.
3. It has zero production risk.
4. It preserves the UnitOfWork abstraction.
5. It handles both the flush-phase and commit-phase failure scenarios.

### 6. Side Effects

The alternative fix (removing `is_active` guard) has **no negative side effects**. Calling `session.rollback()` on an already-active session:
- Rolls back the current transaction (same behavior as before).
- Begins a new transaction.

Calling `session.rollback()` on a non-active session (after failed commit):
- Cleans up the prepared/errored transaction.
- Begins a new transaction.

This is standard SQLAlchemy usage. The original `is_active` guard was unnecessarily restrictive.

### 7. Final Verdict

- Status: **Confirmed**
- Recommended Fix: **Alternative fix** (remove `is_active` guard from `UnitOfWork.rollback()`)

Change:
```python
# Before
def rollback(self) -> None:
    if self._session is not None and self._session.is_active:
        self._session.rollback()

# After
def rollback(self) -> None:
    if self._session is not None:
        self._session.rollback()
