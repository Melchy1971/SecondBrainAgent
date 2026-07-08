from __future__ import annotations

from secondbrain.agent.toolchain import ToolChain, ToolChainExecutor, ToolStep

from tests._toolchain_fakes import RecordingRunner


def test_retry_succeeds_within_budget():
    runner = RecordingRunner(fail={"flaky": 2})   # fails twice, succeeds on 3rd
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("r").tool("flaky", max_attempts=3)
    run = ex.run(ch)
    assert run.status == "ok"
    assert runner.count("flaky") == 3
    assert [r.attempts for r in run.results if r.name == "flaky"][0] == 3


def test_retry_exhausted_fails_chain():
    runner = RecordingRunner(fail={"flaky": 5})
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("r").tool("flaky", max_attempts=2)
    run = ex.run(ch)
    assert run.status == "failed"
    assert runner.count("flaky") == 2


def test_fallback_recovers_failure():
    runner = RecordingRunner(always_fail={"primary"})
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("f").tool("primary", fallback=ToolStep.create("backup"))
    run = ex.run(ch)
    assert run.status == "ok"
    assert runner.count("backup") == 1
    assert any(r.used_fallback for r in run.results if r.name == "primary")


def test_fallback_also_fails_propagates():
    runner = RecordingRunner(always_fail={"primary", "backup"})
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("f").tool("primary", fallback=ToolStep.create("backup"))
    run = ex.run(ch)
    assert run.status == "failed"


def test_rollback_compensates_completed_steps():
    runner = RecordingRunner(always_fail={"boom"})
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("rb")
    ch.tool("create_a", rollback_tool="delete_a")
    ch.tool("create_b", rollback_tool="delete_b")
    ch.tool("boom")   # fails -> rollback delete_b then delete_a (reverse order)
    run = ex.run(ch)
    assert run.status == "failed"
    assert run.rolled_back == ["delete_b", "delete_a"]


def test_rollback_disabled_leaves_no_compensation():
    runner = RecordingRunner(always_fail={"boom"})
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("rb", rollback_on_error=False)
    ch.tool("create_a", rollback_tool="delete_a")
    ch.tool("boom")
    run = ex.run(ch)
    assert run.status == "failed"
    assert run.rolled_back == []
    assert runner.count("delete_a") == 0


def test_error_recorded_in_run():
    runner = RecordingRunner(always_fail={"boom"})
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("e").tool("boom")
    run = ex.run(ch)
    assert run.status == "failed"
    assert "boom" in run.error
    assert any(r.status == "failed" for r in run.results)
