import pytest
from secondbrain.connectors.dead_letter import DeadLetter
from secondbrain.connectors.dead_letter_store import JsonDeadLetterQueue, replay
from secondbrain.connectors.conflict_detection import detect, ConflictType


def test_dlq_persists_and_replays(tmp_path):
    q = JsonDeadLetterQueue(tmp_path / "dlq.json")
    q.push(DeadLetter("c1", "err", "boom", item_id="i1"))
    q.push(DeadLetter("c1", "err", "boom2", item_id="i2"))
    assert len(JsonDeadLetterQueue(tmp_path / "dlq.json").list()) == 2   # persisted
    result = replay(q, lambda letter: letter.item_id == "i1")           # only i1 succeeds
    assert result == {"replayed": 2, "succeeded": 1, "failed": 1}
    remaining = q.list()
    assert len(remaining) == 1 and remaining[0].item_id == "i2"
    assert remaining[0].attempts == 2                                   # attempt incremented


@pytest.mark.parametrize("local,remote,base,expected", [
    (None, None, None, ConflictType.NONE),
    (None, {"content_hash": "r"}, None, ConflictType.REMOTE_ONLY),
    ({"content_hash": "l"}, None, None, ConflictType.LOCAL_ONLY),
    ({"content_hash": "x"}, {"content_hash": "x"}, None, ConflictType.IDENTICAL),
    ({"content_hash": "l"}, {"content_hash": "r"}, {"content_hash": "b"}, ConflictType.BOTH_CHANGED),
    ({"content_hash": "l"}, {"content_hash": "b"}, {"content_hash": "b"}, ConflictType.LOCAL_AHEAD),
    ({"content_hash": "b"}, {"content_hash": "r"}, {"content_hash": "b"}, ConflictType.REMOTE_AHEAD),
])
def test_conflict_types(local, remote, base, expected):
    assert detect(local, remote, base=base, external_id="e").type == expected


def test_conflict_timestamp_fallback():
    assert detect({"updated_at": 1}, {"updated_at": 2}).type == ConflictType.REMOTE_AHEAD
    assert detect({"updated_at": 3}, {"updated_at": 2}).type == ConflictType.LOCAL_AHEAD
