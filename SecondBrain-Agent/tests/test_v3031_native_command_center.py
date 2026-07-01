from __future__ import annotations

from pathlib import Path

from secondbrain.native.command_center import CommandCenter


def test_command_center_status(tmp_path: Path) -> None:
    center = CommandCenter(tmp_path)
    payload = center.status()
    assert payload["ok"] is True
    assert payload["version"] == "30.31"
    assert payload["commands"] >= 8
    assert "RAG" in payload["categories"]


def test_command_palette_finds_german_alias(tmp_path: Path) -> None:
    center = CommandCenter(tmp_path)
    payload = center.palette("index reparieren")
    assert payload["ok"] is True
    assert any(row["id"] == "rag.reindex" for row in payload["commands"])


def test_write_command_requires_approval(tmp_path: Path) -> None:
    (tmp_path / "launcher.py").write_text("print('stub')", encoding="utf-8")
    center = CommandCenter(tmp_path)
    payload = center.run("Repariere Index")
    assert payload["ok"] is False
    assert payload["status"] == "approval_required"
    assert center.pending_approvals()


def test_dry_run_does_not_require_approval(tmp_path: Path) -> None:
    center = CommandCenter(tmp_path)
    payload = center.run("Repariere Index", dry_run=True)
    assert payload["ok"] is True
    assert payload["status"] == "dry_run"
    assert payload["command"]["id"] == "rag.reindex"


def test_favorites_are_persisted(tmp_path: Path) -> None:
    center = CommandCenter(tmp_path)
    payload = center.add_favorite("Systemstatus prüfen")
    assert payload["ok"] is True
    again = CommandCenter(tmp_path)
    assert "system.status" in again.favorites()
