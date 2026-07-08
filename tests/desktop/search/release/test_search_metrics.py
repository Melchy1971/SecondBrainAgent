from secondbrain.desktop.search.release import SearchMetricsCollector


def test_metrics_collector_measures_and_counts():
    collector = SearchMetricsCollector()
    result = collector.measure("search_latency_ms", lambda: "ok")
    collector.set_counts(result_count=3, history_size=2)
    data = collector.snapshot.to_dict()
    assert result == "ok"
    assert data["search_latency_ms"] >= 0
    assert data["result_count"] == 3
    assert data["history_size"] == 2
