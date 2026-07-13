from secondbrain.agent.planning.approval_manager import ApprovalManager
from secondbrain.agent.planning.execution_context import ExecutionContext
from secondbrain.agent.planning.execution_engine import ExecutionEngine
from secondbrain.agent.planning.task_graph import AgentTask, TaskGraph


def test_execution_engine_runs_registered_tool():
    task = AgentTask(task_id="t1", title="Run", tool_calls=["ok"])
    graph = TaskGraph([task])
    context = ExecutionContext()
    context.register_tool("ok", lambda payload: {"ok": True, "task_id": payload["task"]["task_id"]})

    result = ExecutionEngine().execute(graph, context)

    assert result.status == "COMPLETED"
    assert result.outputs["t1"] == [{"ok": True, "task_id": "t1"}]


def test_execution_engine_stops_on_tool_failure():
    task = AgentTask(task_id="t1", title="Run", tool_calls=["missing"])
    graph = TaskGraph([task])

    result = ExecutionEngine().execute(graph, ExecutionContext())

    assert result.status == "FAILED"
    assert result.failed_tasks == ["t1"]


def test_execution_engine_waits_for_approval():
    task = AgentTask(task_id="t1", title="Delete", tool_calls=["delete_documents"])
    graph = TaskGraph([task])
    manager = ApprovalManager()

    result = ExecutionEngine(approval_manager=manager).execute(graph)

    assert result.status == "WAITING_APPROVAL"
    assert result.waiting_approval == ["t1"]
