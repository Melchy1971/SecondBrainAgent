from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .document_center_rc_gate import DocumentCenterGateResult


@dataclass(frozen=True)
class DocumentCenterRCReportWriter:
    output_dir: Path

    def write_json(self, result: DocumentCenterGateResult, filename: str = "document_center_rc1.json") -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / filename
        path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return path

    def write_markdown(self, result: DocumentCenterGateResult, filename: str = "DOCUMENT_CENTER_RC1.md") -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / filename
        lines = [
            "# Document Center RC1 Gate",
            "",
            f"Status: **{result.status.value}**",
            f"Readiness: **{result.ready_count}/{result.total_count}**",
            f"Checked at: `{result.checked_at}`",
            "",
            "## Capabilities",
            "",
            "| Capability | Implemented | Tested | User Safe | Ready |",
            "|---|---:|---:|---:|---:|",
        ]
        for capability in result.capabilities:
            lines.append(
                f"| {capability.name} | {capability.implemented} | {capability.tested} | "
                f"{capability.user_safe} | {capability.is_ready()} |"
            )
        lines.extend(["", "## Findings", ""])
        if not result.findings:
            lines.append("No findings.")
        else:
            for finding in result.findings:
                lines.append(f"- **{finding.severity.value}** `{finding.code}` ({finding.component}): {finding.message}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path


def summarize_result(result: DocumentCenterGateResult) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "ready": result.ready_count,
        "total": result.total_count,
        "blockers": sum(1 for finding in result.findings if finding.severity.value == "BLOCKER"),
        "warnings": sum(1 for finding in result.findings if finding.severity.value == "WARNING"),
    }
