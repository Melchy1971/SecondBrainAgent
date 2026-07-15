"""Job monitor GUI view model and headless HTML renderer.

The monitor lists jobs without blocking on execution. Payload references and
raw exception text stay out of the primary view.
"""

from __future__ import annotations

import html
from typing import Any

from secondbrain.jobs.models import JobStatus, priority_rank
from secondbrain.jobs.service import JobManager

__all__ = ["JobMonitorViewModel", "render_jobs_html"]


class JobMonitorViewModel:
    def __init__(self, manager: JobManager) -> None:
        self.manager = manager

    def build(self, *, workspace_id: str | None = None) -> dict[str, Any]:
        jobs = self.manager.store.all(workspace_id=workspace_id)
        rows = [self._row(j) for j in sorted(
            jobs, key=lambda j: (-priority_rank(j.priority), j.created_at))]
        counts: dict[str, int] = {}
        for j in jobs:
            counts[j.status] = counts.get(j.status, 0) + 1
        return {
            "jobs": rows,
            "counts": counts,
            "active_queue": [self._row(j) for j in self.manager.queue_snapshot(workspace_id=workspace_id)],
            "needs_attention": [self._row(j) for j in jobs
                                if j.status in (JobStatus.RECOVERY_REQUIRED.value, JobStatus.FAILED.value)],
        }

    @staticmethod
    def _row(j: Any) -> dict[str, Any]:
        return {"type": j.type, "status": j.status, "priority": j.priority,
                "progress": j.progress, "attempts": j.attempts, "max_attempts": j.max_attempts,
                "error_code": j.error_code, "error_summary": j.error_summary,
                "checkpoint_available": bool(j.checkpoint),
                "approval_required": j.approval_required, "approved": j.approved}


class RepositoryJobMonitor:
    """Workspace-bound actions for the PostgreSQL-backed monitor."""

    def __init__(self, repository: Any, *, workspace_id: str) -> None:
        if not workspace_id:
            raise ValueError("workspace_required")
        self.repository = repository
        self.workspace_id = workspace_id

    def build(self) -> dict[str, Any]:
        jobs = self.repository.list_jobs(workspace_id=self.workspace_id)
        rows = [JobMonitorViewModel._row(job) for job in jobs]
        return {
            "jobs": rows,
            "counts": {status.value: sum(job.status == status.value for job in jobs)
                       for status in JobStatus},
        }

    def pause(self, job_id: str) -> None:
        self.repository.pause_job(job_id, workspace_id=self.workspace_id)

    def resume(self, job_id: str) -> None:
        self.repository.resume_job(job_id, workspace_id=self.workspace_id)

    def retry(self, job_id: str) -> None:
        self.repository.resume_job(job_id, workspace_id=self.workspace_id)

    def cancel(self, job_id: str) -> None:
        self.repository.cancel_job(job_id, workspace_id=self.workspace_id)

    def checkpoint(self, job_id: str) -> dict[str, Any]:
        job = self.repository.get_job(job_id, workspace_id=self.workspace_id)
        if job is None:
            raise KeyError("unknown_job")
        return dict(job.checkpoint)

    def approval_link(self, job_id: str) -> str:
        job = self.repository.get_job(job_id, workspace_id=self.workspace_id)
        if job is None or not job.approval_required:
            raise KeyError("approval_not_available")
        return "approval://inbox"

    @staticmethod
    def audit_link() -> str:
        return "audit://jobs"


def render_jobs_html(view: dict[str, Any]) -> str:
    def esc(v: Any) -> str:
        return html.escape(str(v))

    rows = "".join(
        f"<tr class='s-{esc(r['status'])}'><td>{esc(r['type'])}</td><td>{esc(r['status'])}</td>"
        f"<td>{esc(r['priority'])}</td><td>{esc(int(r['progress'] * 100))}%</td>"
        f"<td>{esc(r['attempts'])}/{esc(r['max_attempts'])}</td>"
        f"<td>{'🔒' if r['approval_required'] and not r['approved'] else ''}</td></tr>"
        for r in view["jobs"])
    counts = " · ".join(f"{esc(k)}: {esc(v)}" for k, v in sorted(view["counts"].items()))
    return f"""<!doctype html><html lang='de'><head><meta charset='utf-8'>
<title>Job Monitor</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;margin:24px;color:#111;background:#f6f6f8}}
h1{{color:#e20074}}
table{{border-collapse:collapse;width:100%;background:#fff}}
td,th{{border:1px solid #ddd;padding:6px 8px;text-align:left}}
.s-running{{background:#eef7ff}}
.s-recovery_required,.s-failed{{background:#fde2e2}}
.s-completed{{color:#3a6d00}}
</style></head><body>
<h1>Job Monitor</h1>
<p>{counts}</p>
<table><thead><tr><th>Typ</th><th>Status</th><th>Prio</th><th>Fortschritt</th><th>Versuche</th><th>Approval</th></tr></thead>
<tbody>{rows}</tbody></table>
</body></html>"""
