from secondbrain.agent.planning.execution_history import ExecutionHistory, ExecutionHistoryEntry


def test_execution_history_persists_entries(tmp_path):
    path = tmp_path / "history.json"
    history = ExecutionHistory(path)
    history.append(ExecutionHistoryEntry(plan_id="p1", status="COMPLETED", completed_tasks=2, failed_tasks=0))

    history.save()

    loaded = history.load()
    assert loaded[0]["plan_id"] == "p1"
    assert loaded[0]["completed_tasks"] == 2
