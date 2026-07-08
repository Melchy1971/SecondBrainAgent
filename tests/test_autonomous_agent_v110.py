from pathlib import Path
from secondbrain.autonomous_agent_v110 import AutonomousAgentRuntime, ToolHost, run_to_summary


def test_autonomous_agent_completes_ai_goal(tmp_path):
    host = ToolHost()
    host.register("ai.ask", lambda payload: {"answer": "ok:" + payload.get("prompt", "")})
    runtime = AutonomousAgentRuntime(tmp_path, host)

    run = runtime.run_once("Erstelle eine kurze Analyse", max_steps=3)
    summary = run_to_summary(run)

    assert summary["status"] == "completed"
    assert any(s["action"] == "ai.ask" for s in summary["steps"])
    assert summary["verification"]["ok"] is True


def test_autonomous_agent_uses_rag_for_document_goal(tmp_path):
    host = ToolHost()
    host.register("rag.search", lambda payload: {"hits": []})
    host.register("rag.answer", lambda payload: {"answer": "Antwort", "citations": []})
    host.register("desktop.quick_capture", lambda payload: {"path": "capture.md"})
    runtime = AutonomousAgentRuntime(tmp_path, host)

    run = runtime.run_once("Schreibe eine Dokumentation zu v11", max_steps=5)

    assert run.status == "completed"
    assert [s.action for s in run.steps][:3] == ["rag.search", "rag.answer", "desktop.quick_capture"]


def test_autonomous_agent_blocks_missing_tool(tmp_path):
    runtime = AutonomousAgentRuntime(tmp_path, ToolHost())
    run = runtime.run_once("Bitte sync Connectoren", max_steps=3)

    assert run.status == "failed"
    assert run.verification["ok"] is False
    assert run.verification["failed_step"] == "connectors.sync"


def test_run_store_persists_runs(tmp_path):
    host = ToolHost()
    host.register("ai.ask", lambda payload: {"answer": "ok"})
    runtime = AutonomousAgentRuntime(tmp_path, host)
    run = runtime.run_once("Analyse", max_steps=2)

    runtime2 = AutonomousAgentRuntime(tmp_path, host)
    loaded = runtime2.store.get(run.run_id)

    assert loaded.run_id == run.run_id
    assert runtime2.status()["runs"] == 1
