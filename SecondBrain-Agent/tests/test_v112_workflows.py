from pathlib import Path

from secondbrain.autonomous_agent_v110 import ToolHost
from secondbrain.workflow_engine_v112 import WorkflowEngine, WorkflowDefinition, step
from secondbrain.specialist_agents_v112 import build_specialist_workflow
from secondbrain.launcher_runtime_v112 import SecondBrainLauncherV112


def test_workflow_engine_executes_dependencies(tmp_path):
    host = ToolHost()
    host.register("workflow.noop", lambda payload: {"ok": True, "echo": payload})
    engine = WorkflowEngine(tmp_path, host)
    s1 = step("first", "workflow.noop", {"a": 1})
    s2 = step("second", "workflow.noop", {"b": 2}, [s1.step_id])
    run = engine.run(WorkflowDefinition("wf.test", "Test", steps=[s1, s2]))
    assert run.status == "completed"
    assert [s.status for s in run.workflow.steps] == ["done", "done"]


def test_workflow_engine_blocks_missing_tool(tmp_path):
    engine = WorkflowEngine(tmp_path, ToolHost())
    s1 = step("missing", "missing.tool")
    run = engine.run(WorkflowDefinition("wf.missing", "Missing", steps=[s1]))
    assert run.status == "failed"
    assert run.outputs["failed_step"] == "missing"


def test_specialist_research_workflow_shape():
    wf = build_specialist_workflow("research", "SecondBrain Stand")
    assert wf.metadata["agent"] == "research_agent"
    assert [s.action for s in wf.steps] == ["rag.search", "rag.answer", "ai.ask", "desktop.quick_capture"]


def test_launcher_workflow_status(tmp_path):
    launcher = SecondBrainLauncherV112(tmp_path)
    status = launcher.workflow_status()
    assert "runs" in status
    assert status["runs"] == 0


def test_launcher_generic_workflow_runs(tmp_path):
    launcher = SecondBrainLauncherV112(tmp_path)
    result = launcher.workflow_run("generic", "Hallo Workflow")
    assert result["status"] == "completed"
    assert result["workflow"] == "generic Workflow"
