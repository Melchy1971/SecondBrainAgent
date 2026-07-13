from secondbrain.long_term_memory import LongTermMemoryRuntime


def test_status(tmp_path):
    rt = LongTermMemoryRuntime(tmp_path)
    assert rt.status()["version"] == "16.6"


def test_episode_recall(tmp_path):
    rt = LongTermMemoryRuntime(tmp_path)
    rt.add_episode("Turnier", "Markus spielt Tischtennis in Bietigheim", importance=0.9)
    assert rt.recall("Bietigheim")["episodic"]


def test_fact_update(tmp_path):
    rt = LongTermMemoryRuntime(tmp_path)
    rt.add_fact("Jarvis", "status", "v1")
    updated = rt.add_fact("Jarvis", "status", "v2")
    assert updated["updated"] is True
    assert rt.recall("v2")["semantic"]


def test_procedure_result(tmp_path):
    rt = LongTermMemoryRuntime(tmp_path)
    proc = rt.add_procedure("Release", ["Code", "Test"])
    row = rt.record_procedure_result(proc["id"], True)
    assert row["success_count"] == 1


def test_consolidation_graph(tmp_path):
    rt = LongTermMemoryRuntime(tmp_path)
    rt.add_episode("Jarvis", "Jarvis nutzt SecondBrain.")
    run = rt.consolidate()
    assert run["created_facts"] >= 1
    assert rt.graph_export()["nodes"]


def test_seed(tmp_path):
    rt = LongTermMemoryRuntime(tmp_path)
    status = rt.seed_demo()
    assert status["counts"]["episodic_memory"] == 1
