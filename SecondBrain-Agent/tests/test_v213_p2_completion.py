from secondbrain.agent.retry_backoff import RetryBackoffEngine
from secondbrain.agent.parallel_executor import ParallelExecutor
from secondbrain.agent.metrics import AgentMetrics
from secondbrain.gates.p2_completion_report import build_p2_completion_report


def test_retry_backoff():
    assert RetryBackoffEngine().schedule(3) == 8


def test_parallel_executor():
    result = ParallelExecutor().run([lambda: 1, lambda: 2])
    assert sorted(result) == [1, 2]


def test_metrics():
    metrics = AgentMetrics().summarize(2, 10, 1)
    assert metrics["success_rate"] == 0.9


def test_completion_report():
    report = build_p2_completion_report()
    assert report["status"] == "PASS"
    assert report["next_phase"] == "P4_CONNECTORS"
