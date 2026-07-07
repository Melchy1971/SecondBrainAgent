from __future__ import annotations

from secondbrain.agent.toolchain import ToolChain, ToolChainExecutor, ToolStep

from tests._toolchain_fakes import RecordingRunner


class CountingRunner(RecordingRunner):
    """Returns the running call-count for a tool (to drive while conditions)."""
    def __call__(self, name, inputs):
        self.calls.append((name, dict(inputs)))
        return self.count(name)


def test_conditional_then_branch():
    runner = RecordingRunner()
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("c")
    ch.conditional({"var": "flag", "op": "truthy"},
                   then_steps=[ToolStep.create("yes")],
                   else_steps=[ToolStep.create("no")])
    ex.run(ch, {"flag": True})
    assert runner.count("yes") == 1 and runner.count("no") == 0


def test_conditional_else_branch():
    runner = RecordingRunner()
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("c")
    ch.conditional({"var": "flag", "op": "truthy"},
                   then_steps=[ToolStep.create("yes")],
                   else_steps=[ToolStep.create("no")])
    ex.run(ch, {"flag": False})
    assert runner.count("no") == 1 and runner.count("yes") == 0


def test_conditional_with_callable():
    runner = RecordingRunner()
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("c")
    ch.conditional(lambda ctx: ctx.get("n", 0) > 5, then_steps=[ToolStep.create("big")])
    ex.run(ch, {"n": 10})
    assert runner.count("big") == 1


def test_foreach_loop_iterates_items():
    runner = RecordingRunner()
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("l").foreach("items", body=[ToolStep.create("proc", inputs={"v": "$item"})])
    ex.run(ch, {"items": ["a", "b", "c"]})
    assert runner.count("proc") == 3
    seen = [c[1]["v"] for c in runner.calls if c[0] == "proc"]
    assert seen == ["a", "b", "c"]


def test_while_loop_terminates_when_condition_false():
    runner = CountingRunner()
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("w")
    # body sets 'i' to the running call-count of 'inc'; loop while i < 3
    ch.loop_while(lambda ctx: ctx.get("i", 0) < 3,
                  body=[ToolStep.create("inc", output_var="i")])
    ex.run(ch, {"i": 0})
    assert runner.count("inc") == 3


def test_while_loop_respects_max_iterations():
    runner = RecordingRunner()
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("w").loop_while(lambda ctx: True, body=[ToolStep.create("x")],
                                   max_iterations=5)
    ex.run(ch, {})
    assert runner.count("x") == 5


def test_parallel_branches_all_run():
    runner = RecordingRunner()
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("p").parallel([
        [ToolStep.create("b1a"), ToolStep.create("b1b")],
        [ToolStep.create("b2a")],
    ])
    run = ex.run(ch)
    assert run.status == "ok"
    for t in ("b1a", "b1b", "b2a"):
        assert runner.count(t) == 1
    par = [r for r in run.results if r.type == "parallel"][0]
    assert par.output["branches"] == 2


def test_parallel_failure_fails_chain():
    runner = RecordingRunner(always_fail={"bad"})
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("p").parallel([[ToolStep.create("good")], [ToolStep.create("bad")]])
    run = ex.run(ch)
    assert run.status == "failed"
