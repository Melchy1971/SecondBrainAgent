from __future__ import annotations

import json
from pathlib import Path

from secondbrain.native.memory_explorer import MemoryExplorer


def test_memory_explorer_status_empty(tmp_path: Path) -> None:
    explorer = MemoryExplorer(tmp_path)
    status = explorer.status()
    assert status["ok"] is True
    assert status["version"] == "30.33"
    assert status["total_memories"] == 0


def test_memory_explorer_add_search_archive_restore(tmp_path: Path) -> None:
    explorer = MemoryExplorer(tmp_path)
    created = explorer.add("Markus baut Jarvis als native Desktop App", tags=["jarvis", "desktop"], kind="semantic")
    assert created["ok"] is True
    memory_id = created["memory"]["memory_id"]
    found = explorer.search("native")
    assert found["count"] == 1
    assert found["memories"][0]["kind"] == "semantic"
    assert explorer.favorite(memory_id)["ok"] is True
    assert explorer.archive(memory_id)["ok"] is True
    assert explorer.entries()["count"] == 0
    assert explorer.restore(memory_id)["ok"] is True
    assert explorer.entries()["count"] == 1


def test_memory_explorer_reads_voice_and_chat_runtime(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime" / "native"
    runtime.mkdir(parents=True)
    (runtime / "voice_notes.jsonl").write_text(json.dumps({"text": "Sprachnotiz für Tischtennis", "source": "voice"}) + "\n", encoding="utf-8")
    (runtime / "chat_history.jsonl").write_text(json.dumps({"question": "Was fehlt im Agent Center?", "source": "chat"}) + "\n", encoding="utf-8")
    explorer = MemoryExplorer(tmp_path)
    status = explorer.status()
    assert status["total_memories"] == 2
    assert status["by_kind"]["episodic"] == 1
    assert status["by_kind"]["conversation"] == 1


def test_memory_explorer_export_json_and_markdown(tmp_path: Path) -> None:
    explorer = MemoryExplorer(tmp_path)
    explorer.add("Exportierbare Erinnerung", tags=["export"])
    json_export = explorer.export("json")
    md_export = explorer.export("md")
    assert Path(json_export["path"]).exists()
    assert Path(md_export["path"]).exists()
    assert "Exportierbare Erinnerung" in Path(md_export["path"]).read_text(encoding="utf-8")


def test_memory_explorer_timeline(tmp_path: Path) -> None:
    explorer = MemoryExplorer(tmp_path)
    explorer.add("Timeline Eintrag")
    timeline = explorer.timeline()
    assert timeline["ok"] is True
    assert timeline["days"]


def test_memory_hardening_privacy_mode_blocks_writes(tmp_path: Path) -> None:
    explorer = MemoryExplorer(tmp_path)
    blocked = explorer.add("Soll nicht gespeichert werden", privacy_mode=True)
    assert blocked["ok"] is False
    assert blocked["status"] == "privacy_mode_blocks_writes"


def test_memory_hardening_sensitive_block_and_review(tmp_path: Path) -> None:
    explorer = MemoryExplorer(tmp_path)
    blocked = explorer.add("password=hunter2", kind="semantic")
    assert blocked["ok"] is False
    assert blocked["status"] == "sensitive_blocked"

    review_required = explorer.add("Private Information zum Projekt", kind="project")
    assert review_required["ok"] is False
    assert review_required["status"] == "review_required"
    review_id = review_required["review"]["review_id"]
    approve = explorer.review_decide(review_id, approved=True)
    assert approve["ok"] is True
    assert approve["status"] == "approved"
    assert explorer.entries(query="Private Information")["count"] == 1


def test_memory_hardening_dedup_delete_and_forget(tmp_path: Path) -> None:
    explorer = MemoryExplorer(tmp_path)
    created = explorer.add(
        "Deduplizierter Fakt",
        kind="semantic",
        confidence=0.1,
        evidence=["ticket-42"],
        expires_in_seconds=1,
    )
    assert created["ok"] is True
    memory_id = created["memory"]["memory_id"]
    assert created["memory"]["kind"] == "semantic"
    assert created["memory"]["evidence"] == ["ticket-42"]

    dedup = explorer.add("Deduplizierter   Fakt", kind="semantic")
    assert dedup["ok"] is True
    assert dedup["status"] == "deduplicated"

    deleted = explorer.delete(memory_id)
    assert deleted["ok"] is True
    assert explorer.entries(query="Deduplizierter", include_archived=True, include_expired=True)["count"] == 0


def test_memory_hardening_forget_policy_archives_expired(tmp_path: Path) -> None:
    explorer = MemoryExplorer(tmp_path)
    explorer.add("Kurzlebige Erinnerung", kind="task", expires_in_seconds=-1)
    result = explorer.apply_forget_policy(max_age_days=1, min_confidence=0.2)
    assert result["ok"] is True
    assert result["expired"] >= 1
