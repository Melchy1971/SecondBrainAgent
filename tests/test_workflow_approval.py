from __future__ import annotations

from secondbrain.agent.safety import SafetyService
from secondbrain.agent.workflow import WorkflowExecutor, WorkflowState
from secondbrain.agent.workflow_models import WorkflowStep
from secondbrain.native.approval import NativeApprovalQueue, approval_path

from tests._workflow_fakes import FakeJobQueue, FakeNotifications, RecordingRunner


def _steps():
    return [
        WorkflowStep(id="a", name="Vorbereiten", tool_name="t.a"),
        WorkflowStep(id="b", name="Löschen", tool_name="file.delete", dependencies=["a"], requires_approval=True),
        WorkflowStep(id="c", name="Abschluss", tool_name="t.c", dependencies=["b"]),
    ]


def _executor(tmp_path):
    runner = RecordingRunner()
    jobs = FakeJobQueue()
    notif = FakeNotifications()
    safety = SafetyService(tmp_path)  # real v30.61 approval layer
    ex = WorkflowExecutor(tmp_path, tool_runner=runner, safety=safety, jobs=jobs, notifications=notif)
    return ex, runner, jobs, notif, safety


def test_run_halts_at_approval_step_and_reuses_native_queue(tmp_path):
    ex, runner, jobs, notif, safety = _executor(tmp_path)
    cp = ex.create("Kritischer Plan", _steps())
    result = ex.run(cp.workflow_id)

    assert result.state == WorkflowState.WAITING_APPROVAL
    assert runner.calls == ["a"]  # stopped before the approval step

    # Approval landed in the ONE canonical native queue (v30.61), not a new one.
    assert approval_path(tmp_path) == tmp_path.resolve() / "runtime" / "native" / "approval_queue.jsonl"
    pending = NativeApprovalQueue(tmp_path).list(status="pending")
    assert len(pending) == 1
    assert pending[0]["risk_level"] == "destructive"

    # Job mirrored to blocked, action-required notification raised.
    assert ("job_1", "blocked") in jobs.status_calls
    assert any(n["action_required"] for n in notif.sent)


def test_resume_after_approval_completes(tmp_path):
    ex, runner, jobs, notif, safety = _executor(tmp_path)
    cp = ex.create("Kritischer Plan", _steps())
    ex.run(cp.workflow_id)

    approval_id = NativeApprovalQueue(tmp_path).list(status="pending")[0]["approval_id"]
    safety.approve(approval_id, decided_by="markus")

    result = ex.resume(cp.workflow_id)
    assert result.state == WorkflowState.COMPLETED
    assert runner.calls == ["a", "b", "c"]


def test_resume_still_pending_stays_waiting(tmp_path):
    ex, runner, jobs, notif, safety = _executor(tmp_path)
    cp = ex.create("Kritischer Plan", _steps())
    ex.run(cp.workflow_id)
    result = ex.resume(cp.workflow_id)  # not approved yet
    assert result.state == WorkflowState.WAITING_APPROVAL
    assert runner.calls == ["a"]


def test_rejected_approval_fails_workflow(tmp_path):
    ex, runner, jobs, notif, safety = _executor(tmp_path)
    cp = ex.create("Kritischer Plan", _steps())
    ex.run(cp.workflow_id)

    approval_id = NativeApprovalQueue(tmp_path).list(status="pending")[0]["approval_id"]
    safety.reject(approval_id, decided_by="markus")

    result = ex.resume(cp.workflow_id)
    assert result.state == WorkflowState.FAILED
    assert "c" not in runner.calls


def test_approval_not_duplicated_on_repeated_resume(tmp_path):
    ex, runner, jobs, notif, safety = _executor(tmp_path)
    cp = ex.create("Kritischer Plan", _steps())
    ex.run(cp.workflow_id)
    ex.resume(cp.workflow_id)
    ex.resume(cp.workflow_id)
    # still exactly one approval request for the step
    assert len(NativeApprovalQueue(tmp_path).list()) == 1
