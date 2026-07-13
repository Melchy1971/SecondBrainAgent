from secondbrain.learning import LearningEngine


def test_learning_status_empty(tmp_path):
    engine = LearningEngine(tmp_path)
    assert engine.status()["experiences"] == 0


def test_add_experience_and_metrics(tmp_path):
    engine = LearningEngine(tmp_path)
    engine.add_experience("task", "ok", True, "rag", 1.2)
    metrics = engine.metrics.compute()
    assert metrics[0]["capability"] == "rag"
    assert metrics[0]["success_rate"] == 1.0


def test_reflection_creates_recommendation(tmp_path):
    engine = LearningEngine(tmp_path)
    engine.add_experience("a", "fail", False, "connector", 1, "timeout")
    engine.add_experience("b", "fail", False, "connector", 2, "timeout")
    reflection = engine.reflect()
    assert reflection["recommendations"]


def test_backlog_from_reflection(tmp_path):
    engine = LearningEngine(tmp_path)
    engine.add_experience("a", "fail", False, "agent", 1, "bad_plan")
    engine.add_experience("b", "fail", False, "agent", 2, "bad_plan")
    backlog = engine.create_backlog_from_reflection()
    assert len(backlog) >= 1


def test_episode(tmp_path):
    engine = LearningEngine(tmp_path)
    episode = engine.episodes.create("Sprint", ["1"], "Summary")
    assert episode["title"] == "Sprint"
