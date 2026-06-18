# Unit of Work Consistency Audit

Audit date: 2026-06-18
Scope: `application/`, `modules/`, `idempotency/`, `uow/`
Focus: transactional consistency only

---

## Executive Summary

**Verdict: PASS**

The codebase is transactionally consistent. All write operations follow the same UoW model. No repository owns transactions. No session operations bypass the UoW. The two-commit pattern in checkout and retry-payment is justified by the idempotency strategy.

---

## Audit 1 — Direct Session Control

| File | Operation | Verdict |
|---|---|---|
| `uow/unit_of_work.py:55` | `self.session.commit()` | ✅ Expected — UoW implementation |
| `uow/unit_of_work.py:59` | `self._session.rollback()` | ✅ Expected — UoW implementation |
| `uow/unit_of_work.py:62` | `self.session.flush()` | ✅ Expected — UoW implementation |
| `idempotency/repositories/idempotency_repository.py:42` | `self.session.begin_nested()` | ✅ Expected — idempotency claim mechanism |

No unexpected direct session control found.

---

## Audit 2 — Repository Transaction Ownership

**No repository calls `commit()`, `rollback()`, or `begin()`.**

All repositories use `flush()` only, which writes to the current transaction without ending it. Transaction ownership remains exclusively with the UoW.

**Verdict: ✅ PASS**

---

## Audit 3 — Transaction Boundary Fragmentation

| Use case | Commits | Classification |
|---|---|---|
| `checkout/checkout.py` | 2 (`uow.commit()` at line 98 + line 153) | **Justified** — first commit makes idempotency claim visible to concurrent requests; second commits the complete operation |
| `retry_payment/retry_payment.py` | 2 (`uow.commit()` at line 71 + line 101) | **Justified** — same idempotency pattern |
| `webhook/payment_webhook.py` | 1 (`uow.commit()` at line 60) | **Justified** — single atomic operation |
| `cart/use_cases.py` | 1 per operation | **Justified** — each cart mutation is atomic |
| `product/use_cases.py` | 1 per operation | **Justified** |
| `user/use_cases.py` | 1 per operation | **Justified** |

The two-commit pattern in checkout and retry-payment is not fragmentation — it's a deliberate design:

```
Commit 1: Reserve idempotency key (visible to concurrent requests)
         ↓
         Business work (order, payment, gateway)
         ↓
Commit 2: Persist complete result + idempotency response
```

If the business work fails, the exception handler rolls back the session and deletes the stuck key in a fresh transaction.

**Verdict: ✅ PASS**

---

## Audit 4 — Flush Usage

| Location | Required? | Reason |
|---|---|---|
| All repositories `flush()` in `create()`/`update()`/`delete()` | ✅ Required | Ensures entity gets an `id` (via `refresh`) before the caller needs it, without committing the transaction |
| `checkout/checkout.py:144` `uow.flush()` | ✅ Required | Ensures order/payment/cart changes are visible to `OrderRead.model_validate()` for idempotency response serialization, without committing (which would prevent rollback on failure) |
| `retry_payment/retry_payment.py:92` `uow.flush()` | ✅ Required | Same reason as checkout |
| `payment/use_cases.py:48` `uow.flush()` | ✅ Required | Ensures Payment.id is available before `process_payment()` uses it |
| `idempotency/repositories/idempotency_repository.py:44,76,91,106` | ✅ Required | Flushes within nested transaction (claim) and ensures row visibility |

No redundant or optional flushes found.

**Verdict: ✅ PASS**

---

## Audit 5 — Entity State After Rollback

Two locations perform `uow.rollback()` followed by entity access:

| Location | Pattern | Risk |
|---|---|---|
| `checkout/checkout.py:162-167` | `uow.rollback()` → `delete_by_key()` → `uow.commit()` | ✅ **No risk.** After rollback, the session is clean. A new, independent operation (delete) is performed on the fresh session. The original entities (order, payment) are discarded — only the idempotency key is accessed by key string, not by ORM identity |
| `retry_payment/retry_payment.py:111-116` | Same pattern | ✅ **No risk.** Identical safe pattern |

**Verdict: ✅ PASS**

---

## Audit 6 — Mixed Transaction Models

No operation simultaneously uses raw `Session` operations and `UnitOfWork` inside the same transactional workflow.

All write operations follow:

```
UoW → repositories(uow.session) → uow.commit() / uow.rollback()
```

**Verdict: ✅ PASS**

---

## Audit 7 — Nested Transactions

| Location | Purpose | Verdict |
|---|---|---|
| `idempotency/repositories/idempotency_repository.py:42` | `begin_nested()` for idempotency key claim — detects unique constraint violations without aborting the outer transaction | ✅ Expected — documented in DECISIONS.md |

No other `begin_nested()` calls exist.

**Verdict: ✅ PASS**

---

## Audit 8 — UoW Contract Consistency

All write operations follow the same model:

```
1. Instantiate repositories with uow.session
2. Perform reads/writes
3. uow.commit() on success
4. Exception propagates → UoW.__exit__() → automatic rollback
```

The only variation is the idempotency cleanup in checkout and retry-payment, which adds an explicit `uow.rollback()` + `delete_by_key()` + `uow.commit()` inside the exception handler. This is a deliberate extension of the pattern, not a violation.

**Verdict: ✅ PASS**

---

## False Positives Rejected

| Potential finding | Why rejected |
|---|---|
| Webhook use case missing `try/except` | `UoW.__exit__()` handles rollback automatically on exception |
| Repositories calling `flush()` | `flush()` is not a transaction operation — it writes to the current transaction without ending it |
| Two commits in checkout/retry | Justified by idempotency strategy (claim must be visible before business work) |
| `uow.rollback()` in exception handler | Required for idempotency key cleanup — session must be reset before `delete_by_key()` + `commit()` |

---

## Final Assessment

**Can the current UoW implementation be considered transactionally consistent across the codebase?**

**Yes.** The codebase is transactionally consistent:

1. **All write operations** go through `UnitOfWork` — no exceptions
2. **No repository** owns transactions — all use `flush()` only
3. **No direct session control** outside UoW and idempotency claim mechanism
4. **The two-commit pattern** in checkout/retry is justified and correctly implemented with failure cleanup
5. **Flush usage** is appropriate and required in all locations
6. **Entity state after rollback** is handled safely — no stale entity access
7. **No mixed transaction models** exist
8. **Nested transactions** are limited to the idempotency claim mechanism
