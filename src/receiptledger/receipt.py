from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Receipt:
    key: str
    value: object
    by: str
    at: str
    prev_hash: str | None
    hash: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "key": self.key,
                "value": self.value,
                "by": self.by,
                "at": self.at,
                "prev_hash": self.prev_hash,
                "hash": self.hash,
            }
        )

    @staticmethod
    def from_json(line: str) -> Receipt:
        data = json.loads(line)
        return Receipt(**data)


def make_receipt(key: str, value: object, *, by: str, prev_hash: str | None) -> Receipt:
    at = datetime.now(timezone.utc).isoformat()
    digest_input = json.dumps([key, value, by, at, prev_hash], sort_keys=True, default=str)
    content_hash = hashlib.sha256(digest_input.encode()).hexdigest()
    return Receipt(key=key, value=value, by=by, at=at, prev_hash=prev_hash, hash=content_hash)
