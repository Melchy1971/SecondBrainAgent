"""Health orchestration + Markdown report + HTML live dashboard.

``run_health`` builds a snapshot, appends it to the history/timeline and writes
the artifacts under ``OUTPUTS/v30.99-monitoring/``: a self-contained live HTML
dashboard (Ampelsystem, timeline, history sparklines), a JSON health export and
a Markdown report.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from secondbrain.monitoring import history as _history
from secondbrain.monitoring.health import AMPEL, HealthMonitor, HealthStatus

__all__ = ["ARTIFACT_DIR", "run_health", "render_dashboard_html", "render_markdown", "write_artifacts"]

ARTIFACT_DIR = "OUTPUTS/v30.99-monitoring"
HISTORY_FILE = "health_history.jsonl"
DASHBOARD_FILE = "health_dashboard.html"
EXPORT_FILE = "health_export.json"
REPORT_FILE = "health_report.md"

_AMPEL_HEX = {"green": "#2fe6a0", "yellow": "#e6c02f", "red": "#ff5c5c", "grey": "#5a6b7a"}


def run_health(project_root: str | Path = ".", *, monitor: HealthMonitor | None = None, write: bool = True) -> dict[str, Any]:
    root = Path(project_root).resolve()
    mon = monitor or HealthMonitor(root)
    snapshot = mon.snapshot()
    if write:
        history_path = root / ARTIFACT_DIR / HISTORY_FILE
        _history.append_snapshot(history_path, snapshot)
        write_artifacts(root, snapshot, _history.load_history(history_path))
    return snapshot


def write_artifacts(project_root: str | Path, snapshot: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, str]:
    directory = Path(project_root).resolve() / ARTIFACT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    (directory / DASHBOARD_FILE).write_text(render_dashboard_html(snapshot, history), encoding="utf-8")
    (directory / EXPORT_FILE).write_text(_history.export_snapshot(snapshot), encoding="utf-8")
    (directory / REPORT_FILE).write_text(render_markdown(snapshot, history), encoding="utf-8")
    return {"dashboard": str(directory / DASHBOARD_FILE), "export": str(directory / EXPORT_FILE), "report": str(directory / REPORT_FILE)}


# -- Markdown ----------------------------------------------------------------

def render_markdown(snapshot: dict[str, Any], history: list[dict[str, Any]]) -> str:
    lines = ["# Health Report - v30.99", ""]
    lines.append(f"- Zeitpunkt: {snapshot.get('timestamp')}")
    lines.append(f"- Gesamtstatus: **{snapshot.get('overall', 'n/a').upper()}** ({snapshot.get('ampel')})")
    counts = snapshot.get("counts", {})
    lines.append(f"- Ampel: ok={counts.get('ok', 0)}, warn={counts.get('warn', 0)}, critical={counts.get('critical', 0)}, unavailable={counts.get('unavailable', 0)}")
    lines.append(f"- Snapshots (History): {len(history)}")
    lines.append("")
    lines.append("| Komponente | Ampel | Status | Wert | Detail |")
    lines.append("|---|---|---|---|---|")
    for c in snapshot.get("checks", []):
        lines.append(f"| {c['component']} | {c['ampel']} | {c['status']} | {c.get('value', '')} | {c.get('detail', '')} |")
    lines.append("")
    return "\n".join(lines)


# -- HTML --------------------------------------------------------------------

def _sparkline(values: list[float], color: str, *, width: int = 130, height: int = 26) -> str:
    pts = [float(v) for v in values if isinstance(v, (int, float))]
    if len(pts) < 2:
        return "<span style='color:#5a6b7a'>—</span>"
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1.0
    step = width / (len(pts) - 1)
    coords = " ".join(f"{round(i * step, 1)},{round(height - ((v - lo) / span) * (height - 4) - 2, 1)}" for i, v in enumerate(pts))
    return f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}'><polyline fill='none' stroke='{color}' stroke-width='1.6' points='{coords}'/></svg>"


def render_dashboard_html(snapshot: dict[str, Any], history: list[dict[str, Any]]) -> str:
    e = html.escape
    overall = snapshot.get("ampel", "grey")
    overall_hex = _AMPEL_HEX.get(overall, "#5a6b7a")

    cards = []
    for c in snapshot.get("checks", []):
        hexc = _AMPEL_HEX.get(c["ampel"], "#5a6b7a")
        metric_key = next(iter(c.get("metrics", {})), None)
        series = [p["value"] for p in _history.trend(history, c["component"], metric_key)] if metric_key else []
        spark = _sparkline(series, hexc) if series else ""
        cards.append(
            f"<div class='card'><div class='dot' style='background:{hexc}'></div>"
            f"<div class='cn'>{e(c['component'])}</div>"
            f"<div class='cv'>{e(str(c.get('value', '') or c['status']))}</div>"
            f"<div class='cd'>{e(c.get('detail', ''))}</div>"
            f"<div class='sp'>{spark}</div></div>"
        )

    tl = _history.timeline(history)
    strip = "".join(f"<span class='tick' title='{e(str(t.get('timestamp')))}' style='background:{_AMPEL_HEX.get(t.get('ampel'), '#5a6b7a')}'></span>" for t in tl)

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="15">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Health Dashboard v30.99</title>
<style>
  body{{margin:0;background:#0a0e14;color:#d8ecf5;font:14px/1.5 system-ui,Segoe UI,Roboto,sans-serif}}
  .wrap{{max-width:1180px;margin:0 auto;padding:26px}}
  h1{{font-size:20px;letter-spacing:.04em;margin:0}}
  .banner{{display:flex;align-items:center;gap:12px;margin:14px 0 22px}}
  .big{{width:16px;height:16px;border-radius:50%;box-shadow:0 0 12px}}
  .sub{{color:#7a93a6}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}}
  .card{{background:#111823;border:1px solid #1e2b3a;border-radius:10px;padding:14px;position:relative}}
  .dot{{width:11px;height:11px;border-radius:50%;position:absolute;top:14px;right:14px}}
  .cn{{color:#8fb0c4;font-size:12px;text-transform:uppercase;letter-spacing:.07em}}
  .cv{{font-size:20px;font-weight:600;margin:4px 0}}
  .cd{{color:#6d8497;font-size:12px;min-height:16px}}
  .sp{{margin-top:8px}}
  .timeline{{margin:26px 0 6px;display:flex;gap:3px;align-items:center}}
  .tick{{width:10px;height:22px;border-radius:2px;display:inline-block}}
</style></head>
<body><div class="wrap">
  <h1>HEALTH DASHBOARD &middot; v30.99</h1>
  <div class="banner">
    <div class="big" style="background:{overall_hex};box-shadow:0 0 12px {overall_hex}"></div>
    <div><b>Gesamtstatus: {e(str(snapshot.get('overall','n/a')).upper())}</b>
    <span class="sub"> &middot; {e(snapshot.get('timestamp',''))} &middot; {len(history)} Snapshots</span></div>
  </div>
  <div class="grid">{''.join(cards)}</div>
  <div class="sub" style="margin-top:24px;text-transform:uppercase;letter-spacing:.07em;font-size:12px">Timeline (Gesamtstatus, alt &rarr; neu)</div>
  <div class="timeline">{strip or "<span class='sub'>noch keine Historie</span>"}</div>
  <div class="sub" style="margin-top:18px;font-size:12px">Auto-Refresh alle 15 s &middot; Ampel: gruen=ok, gelb=warn, rot=critical, grau=unavailable (Dienst im Sandbox nicht erreichbar)</div>
</div></body></html>"""
