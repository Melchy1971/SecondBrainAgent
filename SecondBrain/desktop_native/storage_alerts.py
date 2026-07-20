from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def read_vector_validation(project_root: str | Path) -> dict[str, Any]:
    path = Path(project_root).resolve() / "runtime" / "reports" / "p1_rag_validation_latest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"available": False}
    if not isinstance(payload, dict):
        return {"available": False}
    return {
        "available": True,
        "ok": bool(payload.get("ok")),
        "blockers": _count(payload.get("blockers")),
        "warnings": _count(payload.get("warnings")),
    }


def _count(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def storage_alert_labels(*, backup: Mapping[str, Any], vector: Mapping[str, Any]) -> dict[str, str]:
    center = backup.get("backup_center")
    backup_center = center if isinstance(center, Mapping) else {}
    backup_count = _count(backup_center.get("backup_count"))
    backup_status = str(backup_center.get("status", "Unknown"))
    if not backup_center:
        backup_label = "Unavailable"
    elif backup_count == 0:
        backup_label = "No backups"
    elif backup_status in {"PASS", "CONDITIONAL_PASS", "BLOCKED"}:
        backup_label = f"{backup_count} / {backup_status.replace('_', ' ')}"
    else:
        backup_label = f"{backup_count} / Unknown"

    blockers = _count(vector.get("blockers"))
    warnings = _count(vector.get("warnings"))
    if not vector.get("available"):
        vector_label = "Not checked"
    elif blockers:
        vector_label = f"Blocked ({blockers})"
    elif bool(vector.get("ok")) and not warnings:
        vector_label = "Ready"
    elif bool(vector.get("ok")):
        vector_label = f"Warning ({warnings})"
    else:
        vector_label = "Blocked"
    return {"backup": backup_label, "vector_index": vector_label}
