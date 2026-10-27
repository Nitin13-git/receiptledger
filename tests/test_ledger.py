from pathlib import Path

import pytest

from receiptledger import ConflictError, Ledger


def test_append_and_head_roundtrip(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.append("task-1", {"status": "started"}, by="agent-a")
    receipt = ledger.append("task-1", {"status": "done"}, by="agent-a")

    head = ledger.head("task-1")
    assert head is not None
    assert head.value == {"status": "done"}
    assert head.hash == receipt.hash


def test_head_is_none_for_unknown_key(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    assert ledger.head("missing") is None


def test_history_returns_all_receipts_for_a_key_in_order(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.append("task-1", 1, by="a")
    ledger.append("task-2", "unrelated", by="a")
    ledger.append("task-1", 2, by="a")

    history = ledger.history("task-1")
    assert [r.value for r in history] == [1, 2]


def test_conflict_detected_on_stale_expected_hash(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.append("task-1", "v1", by="agent-a")

    # agent-b read the ledger before agent-a's write landed, so its
    # expected_prev_hash (None) is now stale.
    with pytest.raises(ConflictError):
        ledger.append("task-1", "v2", by="agent-b", expected_prev_hash=None)


def test_conflict_check_passes_with_correct_expected_hash(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    first = ledger.append("task-1", "v1", by="agent-a")
    second = ledger.append("task-1", "v2", by="agent-a", expected_prev_hash=first.hash)
    assert second.prev_hash == first.hash


def test_head_lookup_does_not_rescan_full_file(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    for i in range(500):
        ledger.append(f"key-{i}", i, by="bulk")
    last = ledger.append("key-0", "updated", by="bulk")

    head = ledger.head("key-0")
    assert head.value == "updated"
    assert head.hash == last.hash
