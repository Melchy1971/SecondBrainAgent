from secondbrain.agent.tool_registry import ToolRegistry
from secondbrain.agent.agent_executor import AgentExecutor
from secondbrain.agent.planner import Planner
from secondbrain.agent.workflow_engine import WorkflowEngine


def test_tool_registry():
    registry = ToolRegistry()
    registry.register("hello", lambda: "world")
    assert registry.get("hello")() == "world"


def test_agent_executor():
    registry = ToolRegistry()
    registry.register("add", lambda a, b: a + b)
    executor = AgentExecutor(registry)
    assert executor.execute("add", 2, 3) == 5


def test_planner_and_workflow():
    graph = Planner().create_plan("Create report")
    result = WorkflowEngine().run(graph)
    assert result["status"] == "PASS"
    assert result["tasks"] == 1
