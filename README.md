# ReceiptLedger

An append-only receipt log for agent sessions, built for two things
conversation history doesn't give you for free: **O(1) lookup** of a key's
latest state no matter how long the ledger gets, and **conflict
detection** when two sessions write to the same key without having seen
each other's latest write.

## How it works

- Receipts are appended to a JSONL file — one line per write, each hash-
  chained to the previous receipt for the same key (`prev_hash`).
- A side index file maps `key -> byte offset of its latest receipt`, so
  `head(key)` seeks straight to that offset instead of scanning the whole
  ledger. `history(key)` still scans the full file — that's the one
  operation the index doesn't help with.
- `append(key, value, by=..., expected_prev_hash=...)` — pass the hash you
  last read as `expected_prev_hash` and a write that landed in between
  raises `ConflictError` instead of silently clobbering it. Omit it to
  skip the check.

## Quickstart

```bash
pip install -e ".[dev]"
pytest
```

```python
from receiptledger import ConflictError, Ledger

ledger = Ledger("session.ledger.jsonl")
receipt = ledger.append("task-1", {"status": "started"}, by="agent-a")

try:
    ledger.append("task-1", {"status": "done"}, by="agent-b", expected_prev_hash=receipt.hash)
except ConflictError:
    ...  # someone else wrote to task-1 since agent-b last read it
```

The JSONL format is plain text on purpose — it diffs cleanly and commits
into a git repo like any other file, so a ledger's own history is just
`git log` on the file if you want that.

## License

MIT
