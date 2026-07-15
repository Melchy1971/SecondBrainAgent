"""Benchmark orchestration plus Markdown report and HTML dashboard rendering.

``run_benchmarks`` executes every registered case, compares the result against
the last recorded run (baseline), applies the >10 % regression gate, appends the
run to history and writes the artifacts under ``OUTPUTS/v30.97-performance/``.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from secondbrain.perf import history as _history
from secondbrain.perf import regression as _regression
from secondbrain.perf.harness import BenchmarkResult, has_psutil, measure
from secondbrain.perf.registry import BenchmarkCase, default_registry

__all__ = [
    "SCHEMA",
    "ARTIFACT_DIR",
    "run_case",
    "run_benchmarks",
    "render_markdown",
    "render_dashboard_html",
    "write_artifacts",
]

SCHEMA = "secondbrain.perf.run.v1"
ARTIFACT_DIR = "OUTPUTS/v30.97-performance"
HISTORY_FILE = "history.jsonl"
REPORT_FILE = "performance_report.md"
DASHBOARD_FILE = "performance_dashboard.html"

_METRIC_COLUMNS = [
    ("per_iter_ms", "Zeit/Iter (ms)"),
    ("cpu_percent", "CPU %"),
    ("ram_delta_mb", "RAM Δ (MB)"),
    ("io_read_kb", "IO R (KB)"),
    ("io_write_kb", "IO W (KB)"),
    ("db_ms", "DB (ms)"),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_case(case: BenchmarkCase) -> BenchmarkResult:
    if case.requires_service or case.fn is None:
        return BenchmarkResult(case.component, case.name, "requires_service", {}, detail=case.note)
    try:
        m = measure(case.fn, iterations=case.iterations)
        return BenchmarkResult(
            case.component,
            case.name,
            "ok",
            {
                "per_iter_ms": m.per_iter_ms,
                "seconds": m.seconds,
                "cpu_percent": m.cpu_percent,
                "ram_delta_mb": m.ram_delta_mb,
                "io_read_kb": m.io_read_kb,
                "io_write_kb": m.io_write_kb,
                "db_ms": m.db_ms,
                "iterations": float(m.iterations),
            },
        )
    except Exception as exc:  # noqa: BLE001 - a broken case must not abort the run
        return BenchmarkResult(case.component, case.name, "error", {}, detail=f"{type(exc).__name__}: {exc}")


def run_benchmarks(
    project_root: str | Path = ".",
    *,
    cases: Sequence[BenchmarkCase] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    selected = list(cases) if cases is not None else default_registry()
    results = [run_case(case).to_dict() for case in selected]

    history_path = root / ARTIFACT_DIR / HISTORY_FILE
    prior = _history.load_history(history_path)
    baseline = _history.latest_baseline(prior)
    regressions = _regression.compare_runs(results, baseline.get("results", []) if baseline else [])
    gate = _regression.gate(regressions)

    run = {
        "schema": SCHEMA,
        "timestamp": _utc_now(),
        "psutil": has_psutil(),
        "baseline_timestamp": baseline.get("timestamp") if baseline else None,
        "results": results,
        "regressions": [r.to_dict() for r in regressions],
        "gate": gate,
        "summary": {
            "total": len(results),
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "requires_service": sum(1 for r in results if r["status"] == "requires_service"),
            "error": sum(1 for r in results if r["status"] == "error"),
        },
    }

    if write:
        _history.append_run(history_path, run)
        write_artifacts(root, run, _history.load_history(history_path))
    return run


def write_artifacts(project_root: str | Path, run: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, str]:
    directory = Path(project_root).resolve() / ARTIFACT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / REPORT_FILE
    dashboard_path = directory / DASHBOARD_FILE
    report_path.write_text(render_markdown(run, history), encoding="utf-8")
    dashboard_path.write_text(render_dashboard_html(run, history), encoding="utf-8")
    return {"report": str(report_path), "dashboard": str(dashboard_path)}


# -- Markdown ----------------------------------------------------------------

def render_markdown(run: dict[str, Any], history: list[dict[str, Any]]) -> str:
    gate = run.get("gate", {})
    summary = run.get("summary", {})
    lines: list[str] = []
    lines.append("# Performance Report - v30.97")
    lines.append("")
    lines.append(f"- Zeitpunkt: {run.get('timestamp')}")
    lines.append(f"- Gate: **{gate.get('status', 'n/a')}** (Schwelle {gate.get('threshold_pct', 10)} %, {gate.get('compared', 0)} verglichen)")
    lines.append(f"- Baseline: {run.get('baseline_timestamp') or 'keine (erste Messung = neue Baseline)'}")
    lines.append(f"- psutil: {'ja' if run.get('psutil') else 'nein (nur Zeit gemessen)'}")
    lines.append(f"- Cases: {summary.get('ok', 0)} gemessen, {summary.get('requires_service', 0)} benoetigen Dienste, {summary.get('error', 0)} Fehler")
    lines.append("")
    lines.append("## Messwerte")
    lines.append("")
    header = "| Komponente | Case | Status | " + " | ".join(label for _, label in _METRIC_COLUMNS) + " | Δ Baseline % |"
    lines.append(header)
    lines.append("|" + "---|" * (3 + len(_METRIC_COLUMNS) + 1))
    reg_by_key = {r["key"]: r for r in run.get("regressions", [])}
    for r in run.get("results", []):
        key = f"{r['component']}/{r['case']}"
        metrics = r.get("metrics", {})
        cells = [r["component"], r["case"], r["status"]]
        if r["status"] == "ok":
            cells += [f"{metrics.get(m, 0):g}" for m, _ in _METRIC_COLUMNS]
            reg = reg_by_key.get(key)
            cells.append(("+" if reg and reg["delta_pct"] >= 0 else "") + (f"{reg['delta_pct']:g}" if reg else "—"))
        else:
            cells += ["—"] * (len(_METRIC_COLUMNS) + 1)
            if r.get("detail"):
                cells[-1] = ""
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    lines.append("")

    if gate.get("regressions"):
        lines.append("## Regressionen (>10 %)")
        lines.append("")
        for reg in gate["regressions"]:
            lines.append(f"- {reg['key']}: {reg['baseline']:g} → {reg['current']:g} ms ({reg['delta_pct']:+g} %)")
        lines.append("")

    service = [r for r in run.get("results", []) if r["status"] == "requires_service"]
    if service:
        lines.append("## Benoetigen Dienste (auf provisionierter Maschine messen)")
        lines.append("")
        for r in service:
            lines.append(f"- {r['component']} / {r['case']}: {r.get('detail', '')}")
        lines.append("")

    lines.append(f"## History")
    lines.append("")
    lines.append(f"- Laeufe insgesamt: {len(history)}")
    lines.append("")
    return "\n".join(lines)


# -- HTML dashboard ----------------------------------------------------------

def _sparkline(values: list[float], *, width: int = 120, height: int = 26) -> str:
    pts = [float(v) for v in values if isinstance(v, (int, float))]
    if len(pts) < 2:
        return "<span style='color:#5b7'>—</span>"
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1.0
    step = width / (len(pts) - 1)
    coords = []
    for i, v in enumerate(pts):
        x = round(i * step, 1)
        y = round(height - ((v - lo) / span) * (height - 4) - 2, 1)
        coords.append(f"{x},{y}")
    up = pts[-1] > pts[0]
    color = "#ff6b6b" if up else "#2fe6a0"
    return (
        f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
        f"<polyline fill='none' stroke='{color}' stroke-width='1.6' points='{' '.join(coords)}'/></svg>"
    )


def render_dashboard_html(run: dict[str, Any], history: list[dict[str, Any]]) -> str:
    e = html.escape
    gate = run.get("gate", {})
    summary = run.get("summary", {})
    gate_status = gate.get("status", "n/a")
    gate_color = {"PASS": "#2fe6a0", "FAIL": "#ff6b6b"}.get(gate_status, "#6b8")
    reg_by_key = {r["key"]: r for r in run.get("regressions", [])}

    rows = []
    for r in run.get("results", []):
        key = f"{r['component']}/{r['case']}"
        metrics = r.get("metrics", {})
        status = r["status"]
        badge = {"ok": "#2fe6a0", "requires_service": "#e6c02f", "error": "#ff6b6b"}.get(status, "#889")
        if status == "ok":
            cells = "".join(f"<td>{e(f'{metrics.get(m, 0):g}')}</td>" for m, _ in _METRIC_COLUMNS)
            reg = reg_by_key.get(key)
            if reg:
                dcol = "#ff6b6b" if reg["regressed"] else ("#2fe6a0" if reg["delta_pct"] <= 0 else "#e6c02f")
                delta = f"<td style='color:{dcol}'>{reg['delta_pct']:+g}%</td>"
            else:
                delta = "<td style='color:#5b7'>neu</td>"
            series = [p["value"] for p in _history.trend(history, r["component"], r["case"])]
            spark = f"<td>{_sparkline(series)}</td>"
        else:
            cells = "".join("<td style='color:#667'>—</td>" for _ in _METRIC_COLUMNS)
            delta = "<td style='color:#667'>—</td>"
            spark = f"<td style='color:#889;font-size:11px'>{e(r.get('detail', ''))}</td>"
        rows.append(
            f"<tr><td><b>{e(r['component'])}</b></td><td>{e(r['case'])}</td>"
            f"<td><span style='color:{badge}'>&#9679;</span> {e(status)}</td>"
            f"{cells}{delta}{spark}</tr>"
        )

    metric_headers = "".join(f"<th>{e(label)}</th>" for _, label in _METRIC_COLUMNS)
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Performance Dashboard v30.97</title>
<style>
  body{{margin:0;background:#0a0e14;color:#cfe;font:14px/1.5 system-ui,Segoe UI,Roboto,sans-serif}}
  .wrap{{max-width:1180px;margin:0 auto;padding:28px}}
  h1{{font-size:20px;letter-spacing:.04em;margin:0 0 4px}}
  .sub{{color:#7a93a6;margin-bottom:20px}}
  .cards{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:22px}}
  .card{{background:#111823;border:1px solid #1e2b3a;border-radius:10px;padding:14px 18px;min-width:150px}}
  .card .k{{color:#7a93a6;font-size:12px;text-transform:uppercase;letter-spacing:.08em}}
  .card .v{{font-size:22px;font-weight:600;margin-top:4px}}
  table{{width:100%;border-collapse:collapse;background:#0e141d;border:1px solid #1e2b3a;border-radius:10px;overflow:hidden}}
  th,td{{padding:9px 11px;text-align:left;border-bottom:1px solid #16202c;font-variant-numeric:tabular-nums}}
  th{{color:#8fb0c4;font-size:12px;text-transform:uppercase;letter-spacing:.06em;background:#0c1621}}
  tr:hover td{{background:#111c27}}
</style></head>
<body><div class="wrap">
  <h1>PERFORMANCE DASHBOARD &middot; v30.97</h1>
  <div class="sub">{e(run.get('timestamp',''))} &middot; psutil: {'ja' if run.get('psutil') else 'nein'} &middot; Baseline: {e(str(run.get('baseline_timestamp') or 'keine'))}</div>
  <div class="cards">
    <div class="card"><div class="k">Gate</div><div class="v" style="color:{gate_color}">{e(gate_status)}</div></div>
    <div class="card"><div class="k">Schwelle</div><div class="v">{e(str(gate.get('threshold_pct',10)))}%</div></div>
    <div class="card"><div class="k">Gemessen</div><div class="v">{summary.get('ok',0)}</div></div>
    <div class="card"><div class="k">Dienste noetig</div><div class="v" style="color:#e6c02f">{summary.get('requires_service',0)}</div></div>
    <div class="card"><div class="k">Fehler</div><div class="v" style="color:{'#ff6b6b' if summary.get('error',0) else '#2fe6a0'}">{summary.get('error',0)}</div></div>
    <div class="card"><div class="k">Laeufe (History)</div><div class="v">{len(history)}</div></div>
  </div>
  <table>
    <thead><tr><th>Komponente</th><th>Case</th><th>Status</th>{metric_headers}<th>Δ Baseline</th><th>Trend</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <div class="sub" style="margin-top:16px">Regression-Gate: Fehl, wenn eine gemessene Komponente ihre Baseline (Zeit/Iter) um mehr als {e(str(gate.get('threshold_pct',10)))} % ueberschreitet.</div>
</div></body></html>"""
