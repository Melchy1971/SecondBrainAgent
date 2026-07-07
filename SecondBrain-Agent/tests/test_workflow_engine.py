from __future__ import annotations

from secondbrain.agent.workflow import WorkflowExecutor, WorkflowState
from secondbrain.agent.workflow_models import WorkflowStep

from tests._workflow_fakes import FakeJobQueue, FakeNotifications, MemorySink, RecordingRunner


def _steps():
    return [
        WorkflowStep(id="a", name="A", tool_name="t.a"),
        WorkflowStep(id="b", name="B", tool_name="t.b", dependencies=["a"]),
        WorkflowStep(id="c", name="C", tool_name="t.c", dependencies=["b"]),
    ]


def _executor(tmp_path, runner, **kw):
    return WorkflowExecutor(tmp_path, tool_runner=runner, jobs=FakeJobQueue(),
                            notifications=FakeNotifications(), **kw)


def test_run_completes_multi_step_in_dependency_order(tmp_path):
    runner = RecordingRunner()
    mem = MemorySink()
    ex = _executor(tmp_path, runner, memory_sink=mem)
    cp = ex.create("Mehrstufiger Plan", _steps())
    result = ex.run(cp.workflow_id)

    assert result.state == WorkflowState.COMPLETED
    assert runner.calls == ["a", "b", "c"]
    status = ex.status(cp.workflow_id)
    assert status["steps_completed"] == 3
    # memory sink fed with step + completion facts
    kinds = {f["kind"] for f in mem.facts}
    assert "workflow_step" in kinds and "workflow_completed" in kinds


def test_topological_reordering_of_unordered_steps(tmp_path):
    runner = RecordingRunner()
    ex = _executor(tmp_path, runner)
    # declared out of order; dependencies must still be respected
    steps = [
        WorkflowStep(id="c", name="C", tool_name="t.c", dependencies=["b"]),
        WorkflowStep(id="a", name="A", tool_name="t.a"),
        WorkflowStep(id="b", name="B", tool_name="t.b", dependencies=["a"]),
    ]
    cp = ex.create("obj", steps)
    ex.run(cp.workflow_id)
    assert runner.calls == ["a", "b", "c"]


def test_step_without_tool_is_noop_success(tmp_path):
    runner = RecordingRunner()
    ex = _executor(tmp_path, runner)
    steps = [WorkflowStep(id="manual", name="Manueller Schritt", tool_name=None)]
    cp = ex.create("obj", steps)
    result = ex.run(cp.workflow_id)
    assert result.state == WorkflowState.COMPLETED
    assert runner.calls == []  # runner not invoked for tool-less step


def test_failure_without_retry_budget_prepares_rollback(tmp_path):
    def boom():
        raise ValueError("kaputt")

    runner = RecordingRunner(behavior={"b": boom})
    jobs = FakeJobQueue()
    notif = FakeNotifications()
    ex = WorkflowExecutor(tmp_path, tool_runner=runner, jobs=jobs, notifications=notif)
    steps = [
        WorkflowStep(id="a", name="A", tool_name="t.a"),
        WorkflowStep(id="b", name="B", tool_name="t.b", dependencies=["a"], max_retries=0),
    ]
    cp = ex.create("obj", steps)
    result = ex.run(cp.workflow_id)

    assert result.state == WorkflowState.ROLLBACK_READY
    # rollback plan lists the completed step 'a' only, in reverse
    plan = ex.prepare_rollback(cp.workflow_id)
    assert [s["step_id"] for s in plan["rollback"]] == ["a"]
    # a failure notification was raised
    assert any(n["level"] == "error" for n in notif.sent)


def test_list_and_audit(tmp_path):
    runner = RecordingRunner()
    ex = _executor(tmp_path, runner)
    cp = ex.create("obj", _steps())
    ex.run(cp.workflow_id)

    listed = ex.list()
    assert any(w["workflow_id"] == cp.workflow_id and w["state"] == "COMPLETED" for w in listed)
    events = ex.audit_events(cp.workflow_id)
    kinds = {e["event"] for e in events}
    assert {"workflow_created", "workflow_running", "workflow_completed"} <= kinds


def test_unknown_workflow_raises(tmp_path):
    ex = _executor(tmp_path, RecordingRunner())
    try:
        ex.run("nope")
    except KeyError as exc:
        assert "unknown_workflow" in str(exc)
    else:
        raise AssertionError("expected KeyError")
