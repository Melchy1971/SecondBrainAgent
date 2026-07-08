import os, time
from secondbrain.connectors.local_folder import LocalFolderConnector


def test_syncs_text_files(tmp_path):
    (tmp_path / "a.md").write_text("hello", encoding="utf-8")
    (tmp_path / "b.txt").write_text("world", encoding="utf-8")
    (tmp_path / "skip.bin").write_bytes(b"\x00\x01")
    conn = LocalFolderConnector(tmp_path)
    batch = conn.fetch_since(None, 50)
    names = {i.payload.external_id for i in batch.items}
    assert names == {"a.md", "b.txt"}                  # .bin filtered by extension
    assert batch.next_cursor is not None


def test_incremental_by_mtime(tmp_path):
    (tmp_path / "a.md").write_text("1", encoding="utf-8")
    conn = LocalFolderConnector(tmp_path)
    first = conn.fetch_since(None, 50)
    assert conn.fetch_since(first.next_cursor, 50).items == []   # nothing new
    time.sleep(0.01)
    (tmp_path / "b.md").write_text("2", encoding="utf-8")
    os.utime(tmp_path / "b.md", (time.time() + 5, time.time() + 5))
    second = conn.fetch_since(first.next_cursor, 50)
    assert [i.payload.external_id for i in second.items] == ["b.md"]


def test_max_bytes_skips_content(tmp_path):
    (tmp_path / "big.txt").write_text("x" * 100, encoding="utf-8")
    conn = LocalFolderConnector(tmp_path, max_bytes=10)
    item = conn.fetch_since(None, 50).items[0]
    assert "skipped" in item.payload.content
