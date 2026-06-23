from secondbrain.agent.planning.replan_engine import ReplanEngine
from secondbrain.agent.planning.task_graph import AgentTask, TaskGraph


def test_replan_engine_adds_retry_for_failed_task():
    task = AgentTask(task_id="t1", title="Broken", status="FAILED")
    graph = TaskGraph([task])

    replanned = ReplanEngine().replan_failed(graph, "tool_failed")

    retry_tasks = [task for task in replanned.tasks.values() if task.metadata.get("replanned_from") == "t1"]
    assert len(retry_tasks) == 1
    assert retry_tasks[0].status == "REPLANNED"
