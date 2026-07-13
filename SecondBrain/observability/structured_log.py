"""Strukturierter JSONL-Logger mit Correlation-/Job-/Plan-/Sync-IDs.

Jede Zeile ist ein JSON-Objekt; Payloads laufen durch die Redaction-Middleware.
Zielpfad: runtime/observability/logs.jsonl (relativ zum Workspace).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.observability.redaction import RedactionMiddleware

LEVELS = ("debug", "info", "warning", "error", "critical")


class StructuredLogger:
    def __init__(self, project_root: str | Path = ".", *, filename: str = "logs.jsonl"):
        self.project_root = Path(project_root)
        self.path = self.project_root / "runtime" / "observability" / filename
        self.redaction = RedactionMiddleware()

    def log(
        self,
        level: str,
        event: str,
        message: str = "",
        *,
        correlation_id: str | None = None,
        job_id: str | None = None,
        plan_id: str | None = None,
        sync_id: str | None = None,
        category: str | None = None,
        error_type: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if level not in LEVELS:
            level = "info"
        record: dict[str, Any] = {
            "schema": "secondbrain.observability.log.v1",
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            "message": self.redaction.redact_text(message),
        }
        for key, value in (
            ("correlation_id", correlation_id), ("job_id", job_id),
            ("plan_id", plan_id), ("sync_id", sync_id),
            ("category", category), ("error_type", error_type),
        ):
            if value:
                record[key] = value
        if payload:
            record["payload"] = self.redaction.redact_payload(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def info(self, event: str, message: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log("info", event, message, **kwargs)

    def warning(self, event: str, message: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log("warning", event, message, **kwargs)

    def error(self, event: str, message: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log("error", event, message, **kwargs)

    def tail(self, limit: int = 50, *, level: str | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if level and record.get("level") != level:
                continue
            records.append(record)
        return records[-limit:]
