import pytest
from secondbrain.connectors.outlook_pst import OutlookPstConnector, FakePstReader


def test_pst_connector_watermark():
    reader = FakePstReader([
        {"id": "m1", "subject": "One", "body": "b1", "received": "2026-01-01T00:00:00Z", "sender": "a"},
        {"id": "m2", "subject": "Two", "body": "b2", "received": "2026-01-02T00:00:00Z", "sender": "b"},
    ])
    conn = OutlookPstConnector(reader)
    batch = conn.fetch_since(None, 50)
    assert [i.payload.title for i in batch.items] == ["One", "Two"]
    assert batch.next_cursor == "2026-01-02T00:00:00Z"
    later = conn.fetch_since("2026-01-01T00:00:00Z", 50)
    assert [i.payload.external_id for i in later.items] == ["m2"]


def test_pypff_optional_or_skip(tmp_path):
    pytest.importorskip("pypff")
    from secondbrain.connectors.outlook_pst import PypffPstReader   # noqa: F401
