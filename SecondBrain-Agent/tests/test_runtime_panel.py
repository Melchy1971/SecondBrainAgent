"""v30.46.3 - Tests fuer das RuntimePanel-Modell (Rechts: Runtime)."""
from secondbrain.native.ai_workspace.models import ApplicationState
from secondbrain.native.ai_workspace.panels import RuntimePanel


def _state() -> ApplicationState:
    return ApplicationState(
        project_root="H:/Projekt",
        version="v30.46.3",
        modules=[],
        active_provider="ollama",
        active_model="llama3.2",
    )


def test_runtime_snapshot_contains_operating_fields() -> None:
    snapshot = RuntimePanel.snapshot(_state())
    assert snapshot["version"] == "v30.46.3"
    assert snapshot["provider"] == "ollama"
    assert snapshot["model"] == "llama3.2"
    assert snapshot["conversation"] == "-"


def test_runtime_lines_are_ordered_and_complete() -> None:
    lines = RuntimePanel.lines(_state())
    keys = [line.split(":", 1)[0] for line in lines]
    assert keys == ["version", "status", "message", "provider", "model", "conversation", "module", "updated"]


def test_runtime_snapshot_shows_active_conversation() -> None:
    state = _state()
    state.current_conversation = "abc-123"
    assert RuntimePanel.snapshot(state)["conversation"] == "abc-123"
