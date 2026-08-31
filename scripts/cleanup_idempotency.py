"""Manual fallback for temporary-data cleanup.

Run manually or via cron: `python scripts/cleanup_idempotency.py`.

Delegates to the same application use case used by the automatic in-app
scheduler: expired idempotency records and expired/revoked refresh tokens
are removed in a single transaction.
"""

from backend.app.application.use_cases.maintenance.cleanup import (
    run_temporary_data_cleanup_now,
)


def main():
    result = run_temporary_data_cleanup_now()
    print(f"Deleted {result['idempotency_keys']} expired idempotency keys")
    print(f"Deleted {result['refresh_tokens']} expired/revoked refresh tokens")


if __name__ == "__main__":
    main()
