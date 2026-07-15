"""Deterministic tests for the v30.97 performance framework.

Uses synthetic cases/data so results do not depend on machine timing noise.
"""

from __future__ import annotations

import json

import pytest

from secondbrain.perf import history as hist
from secondbrain.perf import regression as reg
from secondbrain.perf.harness import measure
from secondbrain.perf.registry import BenchmarkCase, default_registry
from secondbrain.perf.report import (
    render_dashboard_html,
    render_markdown,
    run_benchmarks,
    run_case,
)


def _result(component, case, per_iter_ms, status="ok"):
    return {"component": component, "case": case, "status": status, "metrics": {"per_iter_ms": per_iter_ms}}


# -- harness -----------------------------------------------------------------

def test_measure_reports_iterations_and_time():
    counter = {"n": 0}

    def fn():
        counter["n"] += 1

    m = measure(fn, iterations=10)
    assert counter["n"] == 10
    assert m.iterations == 10
    assert m.seconds >= 0.0
    assert m.per_iter_ms >= 0.0


def test_measure_sums_db_ms():
    m = measure(lambda: {"db_ms": 2.0}, iterations=3)
    assert m.db_ms == pytest.approx(6.0)


# -- regression --------------------------------------------------------------

def test_regression_flags_over_threshold():
    baseline = [_result("A", "x", 100.0)]
    current = [_result("A", "x", 120.0)]  # +20%
    regs = reg.compare_runs(current, baseline)
    assert len(regs) == 1
    assert regs[0].regressed is True
    assert regs[0].delta_pct == pytest.approx(20.0)
    assert reg.gate(regs)["status"] == "FAIL"


def test_regression_within_threshold_passes():
    regs = reg.compare_runs([_result("A", "x", 105.0)], [_result("A", "x", 100.0)])  # +5%
    assert regs[0].regressed is False
    assert reg.gate(regs)["status"] == "PASS"


def test_regression_improvement_is_not_flagged():
    regs = reg.compare_runs([_result("A", "x", 80.0)], [_result("A", "x", 100.0)])  # -20%
    assert regs[0].regressed is False
    assert regs[0].delta_pct == pytest.approx(-20.0)


def test_regression_ignores_non_ok_and_missing_baseline():
    regs = reg.compare_runs(
        [_result("A", "x", 100.0, status="error"), _result("B", "y", 100.0)],
        [_result("A", "x", 10.0)],
    )
    assert regs == []  # error skipped; B has no baseline


# -- history + trend ---------------------------------------------------------

def test_history_append_load_and_baseline(tmp_path):
    path = tmp_path / "history.jsonl"
    hist.append_run(path, {"timestamp": "t1", "results": [_result("A", "x", 10.0)]})
    hist.append_run(path, {"timestamp": "t2", "results": [_result("A", "x", 11.0)]})
    loaded = hist.load_history(path)
    assert len(loaded) == 2
    assert hist.latest_baseline(loaded)["timestamp"] == "t2"


def test_history_skips_corrupt_lines(tmp_path):
    path = tmp_path / "history.jsonl"
    path.write_text(json.dumps({"timestamp": "t1", "results": []}) + "\nnot json\n", encoding="utf-8")
    assert len(hist.load_history(path)) == 1


def test_trend_extracts_series(tmp_path):
    runs = [
        {"timestamp": "t1", "results": [_result("A", "x", 10.0)]},
        {"timestamp": "t2", "results": [_result("A", "x", 12.0)]},
    ]
    series = hist.trend(runs, "A", "x")
    assert [p["value"] for p in series] == [10.0, 12.0]


# -- run_case ----------------------------------------------------------------

def test_run_case_ok_error_and_requires_service():
    ok = run_case(BenchmarkCase("C", "ok", fn=lambda: None, iterations=2))
    assert ok.status == "ok" and ok.metrics["iterations"] == 2

    def boom():
        raise RuntimeError("kaputt")

    err = run_case(BenchmarkCase("C", "err", fn=boom))
    assert err.status == "error" and "kaputt" in err.detail

    svc = run_case(BenchmarkCase("C", "svc", requires_service=True, note="pg"))
    assert svc.status == "requires_service" and svc.detail == "pg"


# -- orchestration + rendering -----------------------------------------------

def test_run_benchmarks_writes_artifacts_and_gate(tmp_path):
    cases = [BenchmarkCase("C", "fast", fn=lambda: None, iterations=3),
             BenchmarkCase("S", "svc", requires_service=True, note="needs db")]
    run1 = run_benchmarks(tmp_path, cases=cases)
    assert run1["gate"]["status"] == "PASS"  # first run: no baseline
    assert run1["summary"] == {"total": 2, "ok": 1, "requires_service": 1, "error": 0}
    art = tmp_path / "OUTPUTS" / "v30.97-performance"
    assert (art / "performance_report.md").exists()
    assert (art / "performance_dashboard.html").exists()
    assert len(hist.load_history(art / "history.jsonl")) == 1

    run2 = run_benchmarks(tmp_path, cases=cases)
    assert run2["baseline_timestamp"] == run1["timestamp"]
    assert len(hist.load_history(art / "history.jsonl")) == 2


def test_render_markdown_and_dashboard_are_wellformed():
    run = {
        "timestamp": "t", "psutil": True, "baseline_timestamp": None,
        "gate": {"status": "PASS", "threshold_pct": 10.0, "compared": 1, "regressions": []},
        "summary": {"total": 1, "ok": 1, "requires_service": 0, "error": 0},
        "results": [{"component": "A", "case": "x", "status": "ok",
                     "metrics": {"per_iter_ms": 1.2, "cpu_percent": 50, "ram_delta_mb": 0.1,
                                 "io_read_kb": 0, "io_write_kb": 0, "db_ms": 0}}],
        "regressions": [],
    }
    md = render_markdown(run, [run])
    assert "Performance Report" in md and "PASS" in md
    html = render_dashboard_html(run, [run])
    assert html.startswith("<!doctype html>") and "PERFORMANCE DASHBOARD" in html
    assert html.count("<table") == 1


def test_default_registry_has_all_components():
    reg_cases = default_registry()
    components = {c.component for c in reg_cases}
    for expected in ["Chunking", "Approval", "Memory", "Agent Planner", "Metriken",
                     "Import", "OCR", "Embedding", "Vector Search", "Hybrid Search",
                     "GUI", "Connector Sync", "Dashboard", "RAG"]:
        assert expected in components
    real = [c for c in reg_cases if not c.requires_service]
    assert len(real) == 5
