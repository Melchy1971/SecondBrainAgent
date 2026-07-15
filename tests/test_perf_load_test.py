"""Sprint 37 (v30.98) acceptance tests - scalable load profiles + gate."""

from __future__ import annotations

import pytest

from secondbrain.perf.load_test import (
    BLOCKED, BOTTLENECK_CATEGORIES, CONDITIONAL_PASS, LoadRun, PASS, PROFILES,
    classify_bottleneck, deterministic_dataset, percentiles, run_load_gate,
)


# 1: profiles are reproducible
def test_profiles_reproducible():
    p = PROFILES["small"]
    a = deterministic_dataset(p, seed=42, limit=200)
    b = deterministic_dataset(p, seed=42, limit=200)
    assert a == b and len(a) == 200
    c = deterministic_dataset(p, seed=43, limit=200)
    assert c != a  # different seed -> different data


# 2: runs can be aborted in a controlled way
def test_controlled_abort():
    run = LoadRun(PROFILES["small"])
    steps = [
        ("import", lambda: {"throughput": 100}),
        ("embed", lambda: {"throughput": 0, "error": "provider_down"}),
        ("search", lambda: {"throughput": 50}),  # must not run after abort
    ]
    report = run.run(steps, abort_if=lambda r: "aborted_on_error" if r.get("error") else None)
    assert report["aborted"] and report["abort_reason"] == "aborted_on_error"
    assert report["completed_steps"] == ["import", "embed"]  # search never ran


# 3: intermediate state (checkpoints) is retained
def test_checkpoints_retained():
    run = LoadRun(PROFILES["small"])
    run.run([("import", lambda: {"docs": 1000}), ("index", lambda: {"chunks": 5000})])
    assert [c["step"] for c in run.checkpoints] == ["import", "index"]
    assert run.partial_report()["metrics"]["index"]["chunks"] == 5000


# 4: no production data is used
def test_no_production_data():
    data = deterministic_dataset(PROFILES["medium"], limit=50)
    assert all(r["synthetic"] is True and r["id"].startswith("synthetic-") for r in data)


# 5: baseline comparison works (reuses perf.regression)
def test_baseline_comparison():
    baseline = {"cases": [{"component": "search", "case": "vector", "status": "ok", "metrics": {"per_iter_ms": 100.0}}]}
    slower = {"cases": [{"component": "search", "case": "vector", "status": "ok", "metrics": {"per_iter_ms": 130.0}}],
              "saturation": {"database": 0.9}}
    report = run_load_gate(slower, baseline=baseline)
    assert "baseline_regression" in report["warnings"]
    assert report["status"] == CONDITIONAL_PASS


# 6: bottlenecks are classified automatically
def test_bottleneck_classification():
    assert classify_bottleneck({"database": 0.95, "cpu": 0.4}) == "database"
    assert classify_bottleneck({"embedding": 0.8, "network": 0.7}) == "embedding"
    assert classify_bottleneck({}) == "cpu"
    assert set(BOTTLENECK_CATEGORIES) >= {"cpu", "memory", "disk", "database", "network",
                                          "provider", "lock_contention", "queue", "gui", "parser", "embedding"}


# 7: report contains no document content
def test_report_no_document_content():
    run = LoadRun(PROFILES["small"])
    run.run([("parse", lambda: {"throughput": 10, "text": "SECRET DOCUMENT BODY",
                                "content": "should not appear", "body": "nor this"})])
    report = run.partial_report()
    blob = str(report)
    assert "SECRET DOCUMENT BODY" not in blob
    assert "should not appear" not in blob and "nor this" not in blob


# 8: gate blocks on data loss or deadlock
def test_gate_blocks_on_data_loss_and_deadlock():
    assert run_load_gate({"flags": {"data_loss": True}})["status"] == BLOCKED
    assert run_load_gate({"flags": {"deadlock": True}})["status"] == BLOCKED
    assert run_load_gate({"flags": {"oom": True}})["status"] == BLOCKED
    assert "data_loss" in run_load_gate({"flags": {"data_loss": True}})["blockers"]


# gate: p95 over limit blocks; clean run passes
def test_gate_p95_and_clean():
    assert run_load_gate({"vector_search_p95_ms": 999})["status"] == BLOCKED
    assert run_load_gate({"search_error_rate": 0.5})["status"] == BLOCKED
    clean = run_load_gate({"vector_search_p95_ms": 100, "hybrid_search_p95_ms": 200,
                           "search_error_rate": 0.0, "queue_growth_ratio": 0.5})
    assert clean["status"] == PASS


# gate: provider throttling is only a warning (CONDITIONAL_PASS)
def test_gate_provider_warning_conditional():
    report = run_load_gate({"flags": {"provider_throttled": True}, "vector_search_p95_ms": 100})
    assert report["status"] == CONDITIONAL_PASS
    assert "provider_limiting" in report["warnings"]


# percentiles
def test_percentiles():
    p = percentiles([float(i) for i in range(1, 101)])
    assert p["p50"] <= p["p95"] <= p["p99"]
    assert percentiles([]) == {"p50": 0.0, "p95": 0.0, "p99": 0.0}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
