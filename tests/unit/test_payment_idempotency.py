"""process_payment no longer has idempotency replay logic integrated.

The current process_payment in payment/use_cases.py does not accept
requesting_user_id or request_hash. Idempotency for the payment step
is handled at the checkout/retry_payment orchestration layer.
"""
