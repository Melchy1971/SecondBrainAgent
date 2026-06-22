from secondbrain.ga.performance_suite import PerformanceSuite
from secondbrain.ga.chaos_suite import ChaosSuite
from secondbrain.ga.release_report import build_release_report


def test_performance():
    result = PerformanceSuite().benchmark(1000, 10)
    assert result["throughput"] == 100.0


def test_chaos():
    assert ChaosSuite().simulate_failure("database")["status"] == "RECOVERED"


def test_release_report():
    assert build_release_report()["version"] == "1.0.0-RC1"\n