from __future__ import annotations

import json

from secondbrain.agent.workflow import WorkflowExecutor, WorkflowState
from secondbrain.agent.workflow.store import WorkflowStore, workflows_dir
from secondbrain.agent.workflow_models import WorkflowStep

from tests._workflow_fakes import FakeJobQueue, FakeNotifications, RecordingRunner


def _ex(tmp_path, runner):
    return WorkflowExecutor(tmp_path, tool_runner=runner, jobs=FakeJobQueue(),
                            notifications=FakeNotifications())


def _steps():
    return [
        WorkflowStep(id="a", name="A", tool_name="t.a"),
        WorkflowStep(id="b", name="B", tool_name="t.b", dependencies=["a"]),
        WorkflowStep(id="c", name="C", tool_name="t.c", dependencies=["b"]),
    ]


def test_checkpoint_file_written_and_loadable(tmp_path):
    ex = _ex(tmp_path, RecordingRunner())
    cp = ex.create("obj", _steps())
    ex.run(cp.workflow_id)

    path = workflows_dir(tmp_path) / f"{cp.workflow_id}.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["state"] == "COMPLETED"
    assert data["cursor"] == 3

    reloaded = WorkflowStore(tmp_path).load(cp.workflow_id)
    assert reloaded.state == WorkflowState.COMPLETED


def test_resume_after_crash_continues_from_last_checkpoint(tmp_path):
    # First run: step 'b' raises so the workflow does not finish.
    calls = {"n": 0}

    def flaky_b():
        raise TimeoutError("db lock")

    runner = RecordingRunner(behavior={"b": flaky_b})
    ex = _ex(tmp_path, runner)
    cp = ex.create("obj", _steps(), workflow_id="wf_crash")
    ex.run("wf_crash")  # 'a' completes, 'b' exhausts retries -> ROLLBACK_READY

    store = WorkflowStore(tmp_path)
    saved = store.load("wf_crash")
    assert saved.runs()["a"].status == "completed"
    assert saved.runs()["b"].status == "failed"

    # Simulate a crash mid-'b' on a fresh attempt: force state RUNNING and mark
    # 'b' as if it were running when the process died, and reset error.
    saved.state = WorkflowState.RUNNING
    saved.step_runs["b"]["status"] = "running"
    saved.cursor = 1
    store.save(saved)

    # New executor, healthy runner -> resume_after_crash finishes the workflow
    # and does NOT re-run the already-completed step 'a'.
    healthy = RecordingRunner()
    ex2 = _ex(tmp_path, healthy)
    result = ex2.resume_after_crash("wf_crash")

    assert result.state == WorkflowState.COMPLETED
    assert "a" not in healthy.calls        # completed step not repeated
    assert healthy.calls == ["b", "c"]     # resumed from the crash point


def test_completed_steps_are_idempotent_on_rerun(tmp_path):
    runner = RecordingRunner()
    ex = _ex(tmp_path, runner)
    cp = ex.create("obj", _steps())
    ex.run(cp.workflow_id)
    # running an already-completed workflow is a no-op
    again = ex.run(cp.workflow_id)
    assert again.state == WorkflowState.COMPLETED
    assert runner.calls == ["a", "b", "c"]  # not called a second time


def test_atomic_save_leaves_no_tmp_file(tmp_path):
    ex = _ex(tmp_path, RecordingRunner())
    cp = ex.create("obj", _steps())
    ex.run(cp.workflow_id)
    leftovers = list(workflows_dir(tmp_path).glob("*.tmp"))
    assert leftovers == []
