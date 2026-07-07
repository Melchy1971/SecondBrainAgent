from __future__ import annotations

from secondbrain.agent.workflow import WorkflowExecutor, WorkflowState
from secondbrain.agent.workflow.recovery import (
    FAIL_FAST,
    RETRY,
    ROLLBACK,
    WAIT_FOR_APPROVAL,
    WorkflowRecovery,
)
from secondbrain.agent.workflow_models import WorkflowStep

from tests._workflow_fakes import FakeJobQueue, FakeNotifications, RecordingRunner


def test_classify_preserves_base_contract():
    rec = WorkflowRecovery()
    assert rec.classify(TimeoutError("timeout while waiting"))["strategy"] == RETRY
    assert rec.classify(Exception("approval required"))["strategy"] == WAIT_FOR_APPROVAL
    assert rec.classify(ValueError("boom"))["strategy"] == FAIL_FAST


def test_decide_is_type_robust_for_timeout():
    rec = WorkflowRecovery()
    assert rec.decide(TimeoutError("x"), attempt=1, max_retries=3).strategy == RETRY


def test_decide_retries_within_budget_then_rolls_back():
    rec = WorkflowRecovery()
    assert rec.decide(TimeoutError("timeout"), attempt=1, max_retries=3).strategy == RETRY
    assert rec.decide(TimeoutError("timeout"), attempt=3, max_retries=3).strategy == ROLLBACK


def test_decide_approval_error_waits():
    rec = WorkflowRecovery()
    v = rec.decide(Exception("needs approval"), attempt=1, max_retries=3)
    assert v.strategy == WAIT_FOR_APPROVAL


def test_decide_unknown_error_retries_then_rolls_back():
    rec = WorkflowRecovery()
    assert rec.decide(ValueError("boom"), attempt=1, max_retries=2).strategy == RETRY
    assert rec.decide(ValueError("boom"), attempt=2, max_retries=2).strategy == ROLLBACK


def test_executor_retries_transient_error_then_succeeds(tmp_path):
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        if state["n"] < 3:
            raise TimeoutError("transient")
        return "recovered"

    runner = RecordingRunner(behavior={"a": flaky})
    ex = WorkflowExecutor(tmp_path, tool_runner=runner, jobs=FakeJobQueue(),
                          notifications=FakeNotifications())
    cp = ex.create("obj", [WorkflowStep(id="a", name="A", tool_name="t.a", max_retries=3)])
    result = ex.run(cp.workflow_id)

    assert result.state == WorkflowState.COMPLETED
    assert result.runs()["a"].attempts == 3
    assert result.runs()["a"].output == "recovered"
