"""Serialization helpers for dashboard RC reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .rc_gate import DashboardRCReport


def write_dashboard_rc_report(report: DashboardRCReport, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target


def dashboard_rc_markdown(report: DashboardRCReport) -> str:
    lines = [
        "# Dashboard RC1 Gate",
        "",
        f"Status: {report.status.value}",
        f"Score: {report.score}",
        "",
        "## Summary",
    ]
    for key, value in report.summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Findings"])
    if not report.findings:
        lines.append("- none")
    else:
        for finding in report.findings:
            lines.append(f"- [{finding.severity.value}] {finding.code}: {finding.message}")
    return "\n".join(lines) + "\n"


def write_dashboard_rc_markdown(report: DashboardRCReport, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dashboard_rc_markdown(report), encoding="utf-8")
    return target
