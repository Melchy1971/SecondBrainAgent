"""Read/control facade for the Native Import Center; no additional state store."""
from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .streaming import StreamingImportService
from .quality import ImportQualityDashboard


def _duration(seconds: float | None) -> str:
    if seconds is None:
        return "--"
    value = max(0, int(seconds))
    hours, remainder = divmod(value, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class ImportCenterService:
    def __init__(self, project_root: str | Path = ".", *, engine: StreamingImportService | None = None) -> None:
        self.engine = engine or StreamingImportService(project_root)

    def status(self) -> dict[str, Any]:
        sessions = self.engine.checkpoints.list(limit=500)
        jobs = self.engine.queue.list_jobs()
        document_counts: dict[str, int] = {}
        with self.engine.checkpoints.connect() as connection:
            for row in connection.execute("SELECT json_extract(metadata_json,'$.import_session') session_id,COUNT(*) count FROM documents GROUP BY session_id"):
                if row[0]:
                    document_counts[str(row[0])] = int(row[1])
        rows = []
        now = datetime.now(UTC)
        for session in sessions:
            try:
                created = datetime.fromisoformat(session.created_at)
                elapsed = max(0.001, (now - created).total_seconds())
            except (TypeError, ValueError):
                elapsed = 0.001
            rate = session.bytes_processed / elapsed
            remaining = max(0, session.file_size - session.bytes_processed)
            eta = remaining / rate if rate > 0 and session.status not in {"completed", "failed", "stopped"} else 0 if remaining == 0 else None
            session_jobs = [job for job in jobs if str((job.payload or {}).get("session_id") or "") == session.session_id]
            rows.append({**session.to_dict(), "file": Path(session.file_path).name,
                         "progress": round(100 * session.bytes_processed / max(1, session.file_size), 2),
                         "eta_seconds": eta, "eta": _duration(eta),
                         "documents": document_counts.get(session.session_id, session.imported_chats),
                         "workers": sum(job.status == "running" for job in session_jobs),
                         "queued": sum(job.status in {"pending", "retry", "blocked"} for job in session_jobs)})
        cpu, ram = self._resources()
        quality = ImportQualityDashboard(self.engine.db_path).snapshot()
        return {"ok": True, "version": "30.57", "mode": "native_import_center", "sessions": rows,
                "workers": {"configured": self.engine.scheduler.pool.workers,
                            "active": sum(job.status == "running" and job.kind in {"chunk", "embedding", "memory", "graph", "search"} for job in jobs)},
                "cpu": cpu, "ram": ram, "quality": quality,
                "errors": [{"session_id": item.session_id, "file": item.file_path, "error": item.error}
                           for item in sessions if item.error]}

    def history(self, limit: int = 200) -> dict[str, Any]:
        status = self.status()
        events = self.engine.queue.history(limit=limit)
        return {"ok": True, "version": "30.57", "sessions": status["sessions"], "events": events,
                "errors": status["errors"]}

    def quality_dashboard(self) -> dict[str, Any]:
        return ImportQualityDashboard(self.engine.db_path).snapshot()

    def import_warnings(self) -> list[dict[str, Any]]:
        return ImportQualityDashboard(self.engine.db_path).warnings()

    def duplicates(self) -> list[dict[str, Any]]:
        return ImportQualityDashboard(self.engine.db_path).duplicates()

    def pause(self, session_id: str): return self.engine.pause(session_id)
    def continue_import(self, session_id: str): return self.engine.continue_import(session_id)
    def retry(self, session_id: str): return self.engine.retry(session_id)
    def stop(self, session_id: str): return self.engine.stop(session_id)

    @staticmethod
    def _resources() -> tuple[dict[str, Any], dict[str, Any]]:
        cpu: dict[str, Any] = {"cores": os.cpu_count() or 1, "percent": None}
        ram: dict[str, Any] = {"rss_bytes": None, "percent": None}
        try:
            import psutil  # type: ignore[import-not-found]
            process = psutil.Process()
            cpu["percent"] = psutil.cpu_percent(interval=None)
            ram.update(rss_bytes=process.memory_info().rss, percent=process.memory_percent())
        except Exception:
            pass
        return cpu, ram
