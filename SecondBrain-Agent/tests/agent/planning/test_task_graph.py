import pytest

from secondbrain.agent.planning.task_graph import AgentTask, TaskGraph


def test_task_graph_orders_dependencies_first():
    first = AgentTask(task_id="a", title="A")
    second = AgentTask(task_id="b", title="B", dependencies=["a"])
    graph = TaskGraph([first, second])

    assert [task.task_id for task in graph.topological()] == ["a", "b"]


def test_task_graph_rejects_missing_dependency():
    with pytest.raises(ValueError):
        TaskGraph([AgentTask(task_id="b", title="B", dependencies=["missing"])])


def test_task_graph_rejects_cycle():
    a = AgentTask(task_id="a", title="A", dependencies=["b"])
    b = AgentTask(task_id="b", title="B", dependencies=["a"])
    with pytest.raises(ValueError):
        TaskGraph([a, b])
