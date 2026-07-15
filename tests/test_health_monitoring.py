"""Deterministic tests for the v30.99 health monitoring framework."""

from __future__ import annotations

import json

import pytest

from secondbrain.monitoring import history as hist
from secondbrain.monitoring.dashboard import render_dashboard_html, render_markdown, run_health
from secondbrain.monitoring.health import (
    AMPEL,
    HealthCheck,
    HealthMonitor,
    HealthStatus,
    _by_threshold,
)

_COMPONENTS = ["CPU", "RAM", "Disk", "GPU", "DB", "Queue", "Agenten",
               "Connectoren", "Memory", "Embedding", "Provider", "Audit"]


def test_snapshot_covers_all_components(tmp_path):
    snap = HealthMonitor(tmp_path).snapshot()
    assert {c["component"] for c in snap["checks"]} == set(_COMPONENTS)
    assert snap["overall"] in {s.value for s in HealthStatus}
    assert set(snap["counts"]) == {s.value for s in HealthStatus}
    assert snap["schema"] == "secondbrain.monitoring.health.v1"


def test_ampel_mapping():
    assert AMPEL[HealthStatus.OK] == "green"
    assert AMPEL[HealthStatus.WARN] == "yellow"
    assert AMPEL[HealthStatus.CRITICAL] == "red"
    assert AMPEL[HealthStatus.UNAVAILABLE] == "grey"


def test_threshold_grading():
    th = {"cpu": {"warn": 80.0, "critical": 95.0}}
    assert _by_threshold("cpu", 10.0, th) == HealthStatus.OK
    assert _by_threshold("cpu", 85.0, th) == HealthStatus.WARN
    assert _by_threshold("cpu", 96.0, th) == HealthStatus.CRITICAL


def test_overall_is_worst_grade():
    checks = [HealthCheck("A", HealthStatus.OK), HealthCheck("B", HealthStatus.WARN),
              HealthCheck("C", HealthStatus.UNAVAILABLE)]
    assert HealthMonitor._overall(checks) == HealthStatus.WARN
    checks.append(HealthCheck("D", HealthStatus.CRITICAL))
    assert HealthMonitor._overall(checks) == HealthStatus.CRITICAL


def test_overall_all_unavailable():
    checks = [HealthCheck("A", HealthStatus.UNAVAILABLE), HealthCheck("B", HealthStatus.UNAVAILABLE)]
    assert HealthMonitor._overall(checks) == HealthStatus.UNAVAILABLE


def test_system_checks_are_real_when_psutil_present(tmp_path):
    snap = HealthMonitor(tmp_path).snapshot()
    by = {c["component"]: c for c in snap["checks"]}
    from secondbrain.monitoring.health import _HAS_PSUTIL
    if _HAS_PSUTIL:
        for comp in ("CPU", "RAM", "Disk"):
            assert by[comp]["status"] in {"ok", "warn", "critical"}
            assert "percent" in by[comp]["metrics"]


def test_broken_check_degrades_to_unavailable(tmp_path):
    class Boom(HealthMonitor):
        def _cpu(self):
            raise RuntimeError("sensor kaputt")

    snap = Boom(tmp_path).snapshot()
    cpu = next(c for c in snap["checks"] if c["component"] == "CPU")
    assert cpu["status"] == "unavailable"
    assert "sensor kaputt" in cpu["detail"]


def test_history_append_timeline_and_trend(tmp_path):
    path = tmp_path / "h.jsonl"
    for i in range(3):
        hist.append_snapshot(path, {
            "timestamp": f"t{i}", "overall": "ok", "ampel": "green",
            "checks": [{"component": "CPU", "metrics": {"percent": float(i * 10)}}],
        })
    history = hist.load_history(path)
    assert len(history) == 3
    assert len(hist.timeline(history)) == 3
    assert [p["value"] for p in hist.trend(history, "CPU")] == [0.0, 10.0, 20.0]


def test_history_skips_corrupt_lines(tmp_path):
    path = tmp_path / "h.jsonl"
    path.write_text(json.dumps({"timestamp": "t", "checks": []}) + "\nbroken\n", encoding="utf-8")
    assert len(hist.load_history(path)) == 1


def test_run_health_writes_artifacts(tmp_path):
    run_health(tmp_path)
    run_health(tmp_path)
    art = tmp_path / "OUTPUTS" / "v30.99-monitoring"
    assert (art / "health_dashboard.html").exists()
    assert (art / "health_export.json").exists()
    assert (art / "health_report.md").exists()
    assert len(hist.load_history(art / "health_history.jsonl")) == 2
    export = json.loads((art / "health_export.json").read_text(encoding="utf-8"))
    assert "checks" in export and "overall" in export


def test_export_contains_no_secret_values(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-SECRETVALUE1234567890")
    snap = HealthMonitor(tmp_path).snapshot()
    blob = json.dumps(snap, ensure_ascii=False)
    assert "sk-SECRETVALUE1234567890" not in blob  # only provider name is reported
    provider = next(c for c in snap["checks"] if c["component"] == "Provider")
    assert provider["status"] == "ok" and "OpenAI" in str(provider["value"])


def test_dashboard_and_markdown_wellformed(tmp_path):
    snap = HealthMonitor(tmp_path).snapshot()
    html = render_dashboard_html(snap, [snap])
    assert html.startswith("<!doctype html>") and "HEALTH DASHBOARD" in html
    assert "Gesamtstatus" in html
    md = render_markdown(snap, [snap])
    assert "Health Report" in md and "| Komponente |" in md
