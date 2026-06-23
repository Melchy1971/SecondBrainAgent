from secondbrain.agent.dag_builder import DagBuilder, WorkflowCycleError
from secondbrain.agent.workflow_models import WorkflowStep
from secondbrain.agent.workflow_executor import WorkflowExecutor
from secondbrain.agent.tool_registry import ToolRegistry


def test_dag_builder_orders_dependencies():
    steps = [
        WorkflowStep("b", "second", dependencies=["a"]),
        WorkflowStep("a", "first"),
    ]
    ordered = DagBuilder().topological_order(steps)
    assert [s.id for s in ordered] == ["a", "b"]


def test_dag_builder_detects_cycles():
    steps = [
        WorkflowStep("a", "a", dependencies=["b"]),
        WorkflowStep("b", "b", dependencies=["a"]),
    ]
    try:
        DagBuilder().topological_order(steps)
    except WorkflowCycleError:
        pass
    else:
        raise AssertionError("expected WorkflowCycleError")


def test_workflow_executor_runs_tools():
    registry = ToolRegistry()
    registry.register("add", lambda a, b: {"value": a + b})
    plan = DagBuilder().build(
        "wf1",
        "add numbers",
        [WorkflowStep("s1", "add", tool_name="add", input={"a": 2, "b": 3})],
    )
    result = WorkflowExecutor(registry).execute(plan)
    assert result.status == "COMPLETED"
    assert result.completed_steps == 1


def test_workflow_executor_fails_unknown_tool():
    registry = ToolRegistry()
    plan = DagBuilder().build(
        "wf2",
        "missing",
        [WorkflowStep("s1", "missing", tool_name="missing", max_retries=0)],
    )
    result = WorkflowExecutor(registry).execute(plan)
    assert result.status == "FAILED"
    assert result.failed_step == "s1"
