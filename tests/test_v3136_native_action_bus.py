from pathlib import Path

from secondbrain.desktop_native.action_bus import NativeActionBus
from secondbrain.desktop_native import app as desktop_app


def test_navigation_runs_through_registry_without_subprocess(tmp_path: Path):
    bus = NativeActionBus(tmp_path)
    result = bus.submit("öffne dokumente")
    assert result["status"] == "executed"
    assert result["action_id"] == "navigation.documents"
    assert result["result"]["next_view"] == "documents"


def test_external_write_creates_workspace_bound_approval(tmp_path: Path):
    bus = NativeActionBus(tmp_path, workspace_id="alpha")
    result = bus.submit("sende mail", {"recipient": "a@example.test", "body": "Hallo"})
    assert result["status"] == "approval_required"
    assert result["approval_id"]
    rows = bus.approvals.list(status="pending")
    assert len(rows) == 1
    assert rows[0]["workspace_id"] == "alpha"
    assert rows[0]["payload"]["binding"] == result["binding"]
    assert rows[0]["tool_idempotent"] is False


def test_confirmation_executes_direct_ingestion_service(tmp_path: Path, monkeypatch):
    source = tmp_path / "note.txt"
    source.write_text("Jarvis integration", encoding="utf-8")
    bus = NativeActionBus(tmp_path, workspace_id="alpha")
    called = {}

    def fake_ingest(self, path):
        called["path"] = path
        return {"ok": True}

    monkeypatch.setattr("secondbrain.desktop_native.action_bus.P1RagRuntime.ingest_file", fake_ingest)
    pending = bus.submit("importiere datei", {"path": str(source)})
    assert pending["status"] == "confirmation_required"
    result = bus.confirm()
    assert result["status"] == "executed"
    assert called["path"] == str(source)


def test_unbound_yes_never_executes(tmp_path: Path):
    bus = NativeActionBus(tmp_path)
    assert bus.confirm()["error"] == "no_bound_confirmation"


def test_legacy_voice_parser_routes_search_through_registry(tmp_path: Path, monkeypatch):
    bus = NativeActionBus(tmp_path)
    monkeypatch.setattr("secondbrain.desktop_native.action_bus.ChatEngine.search", lambda self, query: {"ok": True, "query": query})
    result = bus.submit("Suche Rechnung Telekom")
    assert result["action_id"] == "search.query"
    assert result["result"]["query"] == "rechnung telekom"


def test_desktop_shell_is_wired_to_action_bus():
    assert "self.action_bus = NativeActionBus" in Path(desktop_app.__file__).read_text(encoding="utf-8")
