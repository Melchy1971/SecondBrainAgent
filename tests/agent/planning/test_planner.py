from secondbrain.agent.planning.planner import AgentPlanner


def test_planner_creates_linear_plan():
    graph = AgentPlanner().create_plan("Index documents", ["import", "embed", "search"])
    ordered = graph.topological()

    assert len(ordered) == 3
    assert ordered[1].dependencies == [ordered[0].task_id]
    assert ordered[2].dependencies == [ordered[1].task_id]
