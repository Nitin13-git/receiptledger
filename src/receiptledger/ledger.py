from __future__ import annotations

import json
import os
from pathlib import Path

from receiptledger.errors import ConflictError
from receiptledger.receipt import Receipt, make_receipt


class Ledger:
    """Append-only receipt log with an O(1) head lookup per key.

    Receipts are appended to a JSONL file. A side index file maps each key
    to the byte offset of its most recent receipt, so `head(key)` seeks
    directly to that offset instead of scanning the whole ledger —
    constant-time regardless of how many receipts have accumulated.
    `history(key)` still has to scan the full file; that's the one
    operation this index doesn't help with.
    """

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._index_path = self._path.with_suffix(self._path.suffix + ".index.json")
        if not self._path.exists():
            self._path.write_text("")
        if not self._index_path.exists():
            self._index_path.write_text(json.dumps({}))

    def _load_index(self) -> dict:
        return json.loads(self._index_path.read_text())

    def _save_index(self, index: dict) -> None:
        self._index_path.write_text(json.dumps(index, indent=2))

    def append(self, key: str, value: object, *, by: str, expected_prev_hash: str | None = "__skip__") -> Receipt:
        """Append a receipt for `key`.

        If `expected_prev_hash` is given (anything other than the default
        sentinel, including None), it must match the key's current head
        hash or `ConflictError` is raised — pass the hash you last read,
        or None if you expect this to be the key's first receipt.
        """
        index = self._load_index()
        current = index.get(key)
        current_hash = current["hash"] if current else None

        if expected_prev_hash != "__skip__" and expected_prev_hash != current_hash:
            raise ConflictError(
                f"key {key!r}: expected prev_hash {expected_prev_hash!r}, ledger has {current_hash!r}"
            )

        receipt = make_receipt(key, value, by=by, prev_hash=current_hash)

        offset = os.path.getsize(self._path) if self._path.exists() else 0
        with open(self._path, "a") as f:
            f.write(receipt.to_json() + "\n")

        index[key] = {"hash": receipt.hash, "offset": offset}
        self._save_index(index)
        return receipt

    def head(self, key: str) -> Receipt | None:
        index = self._load_index()
        entry = index.get(key)
        if entry is None:
            return None
        with open(self._path) as f:
            f.seek(entry["offset"])
            line = f.readline()
        return Receipt.from_json(line)

    def history(self, key: str) -> list[Receipt]:
        receipts = []
        with open(self._path) as f:
            for line in f:
                if not line.strip():
                    continue
                receipt = Receipt.from_json(line)
                if receipt.key == key:
                    receipts.append(receipt)
        return receipts
