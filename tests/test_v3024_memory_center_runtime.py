from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from secondbrain.gui.memory_center_runtime import memory_center_status


def test_memory_center_reports_vault_memory_and_governance(tmp_path: Path) -> None:
    root = tmp_path
    memory_dir = root / "SecondBrain" / "22_Memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "note.md").write_text("# Note\nsource: manual\ntags: #test\ncontent", encoding="utf-8")
    (root / "config").mkdir()
    (root / "config" / "security.yaml").write_text("secret_encryption: true\ndata_classification: true\nprivacy_mode: false\n", encoding="utf-8")

    payload = memory_center_status(root)

    assert payload["schema"] == "secondbrain.gui.memory_center.v1"
    assert payload["summary"]["vault_memories"] == 1
    assert payload["summary"]["governance_blockers"] == 0
    assert payload["governance"]["secret_encryption"] is True


def test_memory_center_blocks_unencrypted_sqlite_memories(tmp_path: Path) -> None:
    root = tmp_path
    (root / "runtime").mkdir()
    db = root / "runtime" / "secondbrain.sqlite3"
    import sqlite3

    con = sqlite3.connect(db)
    con.execute("create table memories (id text, kind text, content text, source text, importance real)")
    con.execute("insert into memories values ('1','note','secret-ish','manual',0.5)")
    con.commit()
    con.close()

    payload = memory_center_status(root)

    assert payload["status"] == "blocked"
    assert payload["summary"]["sqlite_memories"] == 1
    assert any(b["code"] == "sqlite_memory_without_encryption" for b in payload["governance"]["blockers"])


def test_memory_center_endpoint_registered() -> None:
    server = Path("secondbrain/jarvis_hud_server.py").read_text(encoding="utf-8")
    assert "/api/memory-center/status" in server
    assert "memory_center_status(ROOT)" in server


def test_launcher_memory_center_status(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "launcher.py", "memory-center-status", "--project-root", str(tmp_path)],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode in {0, 1}
    payload = json.loads(result.stdout)
    assert payload["schema"] == "secondbrain.gui.memory_center.v1"
