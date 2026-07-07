from __future__ import annotations

from secondbrain.agent.toolchain import ToolChain, ToolChainExecutor, VisualWorkflow

from tests._toolchain_fakes import FakeRegistry, RecordingRunner


def test_sequential_tools_run_in_order():
    runner = RecordingRunner()
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("seq").tool("a").tool("b").tool("c")
    run = ex.run(ch)
    assert run.status == "ok"
    assert [c[0] for c in runner.calls] == ["a", "b", "c"]
    assert len([r for r in run.results if r.type == "tool"]) == 3


def test_output_var_and_input_resolution():
    runner = RecordingRunner(outputs={"produce": {"value": 42}})
    ex = ToolChainExecutor(tool_runner=runner)
    ch = ToolChain("io").tool("produce", output_var="p").tool("consume", inputs={"x": "$p"})
    run = ex.run(ch)
    assert run.context["p"] == {"value": 42}
    # consume received the resolved value
    consume_inputs = [c[1] for c in runner.calls if c[0] == "consume"][0]
    assert consume_inputs["x"] == {"value": 42}


def test_reuses_tool_registry_run():
    runner = RecordingRunner()
    registry = FakeRegistry(runner)
    ex = ToolChainExecutor(registry=registry)
    ch = ToolChain("reg").tool("do")
    run = ex.run(ch)
    assert run.status == "ok"
    assert runner.count("do") == 1


def test_visual_ascii_and_mermaid():
    ch = ToolChain("viz").tool("a").tool("b", max_attempts=3, rollback_tool="undo_b")
    vw = ch.visualize()
    ascii_art = vw.ascii()
    assert "ToolChain: viz" in ascii_art
    assert "tool:b" in ascii_art
    assert "rollback:undo_b" in ascii_art
    mermaid = vw.mermaid()
    assert mermaid.startswith("flowchart TD")
    assert "done" in mermaid


def test_chain_to_dict_roundtrips_structure():
    ch = ToolChain("d").tool("a", output_var="x")
    d = ch.to_dict()
    assert d["name"] == "d"
    assert d["steps"][0]["tool"] == "a"
    assert d["steps"][0]["output_var"] == "x"
