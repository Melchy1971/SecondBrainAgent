from pathlib import Path

from secondbrain.desktop_app import DesktopAppRuntime
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


def test_task_creation_collects_title_and_requires_bound_confirmation(tmp_path: Path):
    bus = NativeActionBus(tmp_path, workspace_id="alpha")

    first = bus.submit("neue aufgabe")
    assert first == {"status": "slots_required", "missing": ["title"], "action_id": "tasks.create"}
    pending = bus.submit("Quartalsbericht abschliessen")
    assert pending["status"] == "confirmation_required"
    assert pending["action_id"] == "tasks.create"

    result = bus.confirm()

    assert result["status"] == "executed"
    assert result["result"]["title"] == "Quartalsbericht abschliessen"
    assert result["result"]["priority"] == "medium"


def test_task_list_reads_the_same_workspace_store(tmp_path: Path):
    bus = NativeActionBus(tmp_path, workspace_id="alpha")
    pending = bus.submit("erstelle aufgabe", {"title": "Review", "priority": "high"})
    assert pending["status"] == "confirmation_required"
    bus.confirm()

    result = bus.submit("liste aufgaben")

    assert result["status"] == "executed"
    assert result["result"]["count"] == 1
    assert result["result"]["items"][0]["title"] == "Review"
    assert result["result"]["items"][0]["priority"] == "high"


def test_task_actions_are_workspace_bound_and_reject_invalid_priority(tmp_path: Path):
    without_workspace = NativeActionBus(tmp_path)
    assert without_workspace.submit("liste aufgaben")["error"] == "workspace_required"

    bus = NativeActionBus(tmp_path, workspace_id="alpha")
    pending = bus.submit("neue aufgabe", {"title": "Review", "priority": "urgent"})
    assert pending["status"] == "confirmation_required"
    result = bus.confirm()
    assert result["status"] == "error"
    assert "task priority" in result["error"]
    assert DesktopAppRuntime(tmp_path).tasks() == []


def test_task_completion_collects_reference_and_requires_confirmation(tmp_path: Path):
    runtime = DesktopAppRuntime(tmp_path)
    runtime.add_task("Quartalsbericht")
    bus = NativeActionBus(tmp_path, workspace_id="alpha")

    first = bus.submit("aufgabe abschliessen")
    assert first == {"status": "slots_required", "missing": ["task"], "action_id": "tasks.complete"}
    pending = bus.submit("Quartalsbericht")
    assert pending["status"] == "confirmation_required"

    result = bus.confirm()

    assert result["status"] == "executed"
    assert result["result"]["column"] == "done"
    assert runtime.tasks()[0]["column"] == "done"


def test_task_completion_rejects_ambiguous_title_without_write(tmp_path: Path):
    runtime = DesktopAppRuntime(tmp_path)
    runtime.add_task("Review")
    runtime.add_task("REVIEW")
    bus = NativeActionBus(tmp_path, workspace_id="alpha")

    pending = bus.submit("erledige aufgabe", {"task": "review"})
    assert pending["status"] == "confirmation_required"
    result = bus.confirm()

    assert result["status"] == "error"
    assert "ambiguous" in result["error"]
    assert [task["column"] for task in runtime.tasks()] == ["backlog", "backlog"]


def test_task_rename_collects_reference_and_title_before_confirmation(tmp_path: Path):
    runtime = DesktopAppRuntime(tmp_path)
    runtime.add_task("Alter Titel")
    bus = NativeActionBus(tmp_path, workspace_id="alpha")

    first = bus.submit("aufgabe umbenennen")
    assert first == {
        "status": "slots_required",
        "missing": ["task", "new_title"],
        "action_id": "tasks.rename",
    }
    assert bus.submit("Alter Titel")["missing"] == ["new_title"]
    pending = bus.submit("Neuer Titel")
    assert pending["status"] == "confirmation_required"

    result = bus.confirm()

    assert result["status"] == "executed"
    assert result["result"]["title"] == "Neuer Titel"
    assert runtime.tasks()[0]["title"] == "Neuer Titel"


def test_task_archive_collects_reference_and_requires_confirmation(tmp_path: Path):
    runtime = DesktopAppRuntime(tmp_path)
    runtime.add_task("Alt", column="doing")
    bus = NativeActionBus(tmp_path, workspace_id="alpha")

    first = bus.submit("aufgabe archivieren")
    assert first == {"status": "slots_required", "missing": ["task"], "action_id": "tasks.archive"}
    pending = bus.submit("Alt")
    assert pending["status"] == "confirmation_required"

    result = bus.confirm()

    assert result["status"] == "executed"
    assert result["result"]["column"] == "archived"
    assert runtime.tasks()[0]["archived_from"] == "doing"


def test_desktop_shell_is_wired_to_action_bus():
    assert "self.action_bus = NativeActionBus" in Path(desktop_app.__file__).read_text(encoding="utf-8")
