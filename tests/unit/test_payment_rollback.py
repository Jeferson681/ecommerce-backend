"""process_payment no longer integrates with OrderRepository, IdempotencyRepository or PaymentCreate.

The current process_payment in payment/use_cases.py accepts:
    payment_id, payment_method_id, uow, gateway, idempotency_key
and handles rollback via the UoW passed from the caller (checkout/retry_payment).
"""
