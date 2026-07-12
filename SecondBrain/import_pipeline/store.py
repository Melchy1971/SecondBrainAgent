"""Persistenz der ImportJobs: Zustands-JSON + Übergangs-Historie als JSONL."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.import_pipeline.models import ImportJob


class ImportJobStore:
    def __init__(self, project_root: str | Path = "."):
        self.project_root = Path(project_root)
        base = self.project_root / "runtime" / "import_pipeline"
        self.state_path = base / "jobs.json"
        self.history_path = base / "transitions.jsonl"

    def _load_state(self) -> dict[str, dict[str, Any]]:
        if not self.state_path.exists():
            return {}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_state(self, state: dict[str, dict[str, Any]]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    def upsert(self, job: ImportJob) -> None:
        state = self._load_state()
        state[job.job_id] = job.to_dict()
        self._write_state(state)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "job_id": job.job_id,
                "status": job.status,
                "attempts": job.attempts,
                "error": job.error,
            }, ensure_ascii=False) + "\n")

    def get(self, job_id: str) -> ImportJob | None:
        record = self._load_state().get(job_id)
        return ImportJob.from_dict(record) if record else None

    def list(self, *, status: str | None = None, source_kind: str | None = None,
             limit: int = 200) -> list[ImportJob]:
        jobs = [ImportJob.from_dict(r) for r in self._load_state().values()]
        if status:
            jobs = [j for j in jobs if j.status == status]
        if source_kind:
            jobs = [j for j in jobs if j.source_kind == source_kind]
        jobs.sort(key=lambda j: j.created_at)
        return jobs[-limit:]

    def counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self._load_state().values():
            counts[record.get("status", "?")] = counts.get(record.get("status", "?"), 0) + 1
        return counts
