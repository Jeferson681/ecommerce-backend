"""PaymentWebhookPayload is now a @dataclass in gateway.base, not a Pydantic schema.

The dataclass does not perform validation on instantiation, so the previous
test that expected PydanticValidationError is no longer applicable.
"""
