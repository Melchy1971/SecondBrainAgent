from secondbrain.multi_agent import MultiAgentRuntime


def test_status_agents(tmp_path):
    rt = MultiAgentRuntime(tmp_path)
    assert rt.status()["counts"]["agents"] == 7


def test_task_plan_run_low_risk(tmp_path):
    rt = MultiAgentRuntime(tmp_path)
    task = rt.create_task("Plan", "Plane den nächsten Sprint")
    plan = rt.plan(task["id"])
    assert plan["ok"] is True
    run = rt.run(task["id"])
    assert run["decision"] == "pass"


def test_high_risk_needs_approval(tmp_path):
    rt = MultiAgentRuntime(tmp_path)
    task = rt.create_task("Write", "Schreibe Datei", risk="high")
    run = rt.run(task["id"])
    assert run["decision"] == "needs_approval"
    assert rt.backlog()


def test_messages_results_reviews_memory(tmp_path):
    rt = MultiAgentRuntime(tmp_path)
    task = rt.create_task("Research", "Recherchiere Wissen")
    rt.run(task["id"])
    assert rt.messages(task["id"])
    assert rt.results(task["id"])
    assert rt.reviews(task["id"])
    assert rt.memory()


def test_unknown_task(tmp_path):
    rt = MultiAgentRuntime(tmp_path)
    assert rt.run("missing")["ok"] is False
