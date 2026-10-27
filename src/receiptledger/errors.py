class ConflictError(Exception):
    """Raised when a write's expected_prev_hash doesn't match the ledger's current head.

    Means another writer appended a receipt for this key since the caller
    last read it — the caller should re-read the head and retry, not
    overwrite blindly.
    """
