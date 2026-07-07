"""v30.71 Scheduler - persistence (recurring jobs + run history)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import JobRun, RecurringJob


def base_dir(root: str | Path) -> Path:
    return Path(root).resolve() / "runtime" / "agent" / "scheduler"


class SchedulerStore:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.dir = base_dir(self.project_root)
        self.jobs_path = self.dir / "recurring_jobs.json"
        self.runs_path = self.dir / "runs.jsonl"

    def load_jobs(self) -> dict[str, RecurringJob]:
        if not self.jobs_path.exists():
            return {}
        try:
            raw = json.loads(self.jobs_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {jid: RecurringJob.from_dict(d) for jid, d in raw.items()}

    def save_jobs(self, jobs: dict[str, RecurringJob]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        payload = {jid: j.to_dict() for jid, j in jobs.items()}
        tmp = self.jobs_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.jobs_path)

    def upsert(self, job: RecurringJob) -> RecurringJob:
        jobs = self.load_jobs()
        jobs[job.id] = job
        self.save_jobs(jobs)
        return job

    def get(self, job_id: str) -> RecurringJob | None:
        return self.load_jobs().get(job_id)

    def append_run(self, run: JobRun) -> JobRun:
        self.dir.mkdir(parents=True, exist_ok=True)
        with self.runs_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(run.to_dict(), ensure_ascii=False) + "\n")
        return run

    def runs(self, job_id: str | None = None, *, limit: int = 100) -> list[JobRun]:
        if not self.runs_path.exists():
            return []
        rows: list[JobRun] = []
        for line in self.runs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if job_id is None or d.get("job_id") == job_id:
                rows.append(JobRun.from_dict(d))
        return rows[-max(1, int(limit)):]
