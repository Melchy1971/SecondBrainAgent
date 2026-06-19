from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Callable, Any
import json
import time
import uuid

@dataclass
class RuntimeJob:
    action: str
    payload: dict
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str = "queued"
    attempts: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RuntimeJob":
        return cls(**data)

class JsonlJobQueue:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def add(self, action: str, payload: dict) -> RuntimeJob:
        job = RuntimeJob(action=action, payload=payload)
        self._append(job)
        return job

    def all(self) -> list[RuntimeJob]:
        jobs=[]
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                jobs.append(RuntimeJob.from_dict(json.loads(line)))
        return jobs

    def pending(self) -> list[RuntimeJob]:
        return [j for j in self.all() if j.status in {"queued", "retry"}]

    def update(self, job: RuntimeJob) -> None:
        jobs = self.all()
        for idx, existing in enumerate(jobs):
            if existing.job_id == job.job_id:
                job.updated_at = time.time()
                jobs[idx] = job
                break
        else:
            jobs.append(job)
        self.path.write_text("\n".join(json.dumps(j.to_dict(), ensure_ascii=False) for j in jobs) + ("\n" if jobs else ""), encoding="utf-8")

    def _append(self, job: RuntimeJob) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(job.to_dict(), ensure_ascii=False) + "\n")

class JobRunner:
    def __init__(self, queue: JsonlJobQueue, handlers: dict[str, Callable[[dict], Any]], max_attempts: int = 2):
        self.queue = queue
        self.handlers = handlers
        self.max_attempts = max_attempts

    def run_once(self) -> dict:
        results = {"processed": 0, "failed": 0, "blocked": 0}
        for job in self.queue.pending():
            handler = self.handlers.get(job.action)
            if not handler:
                job.status = "failed"
                job.last_error = "missing_handler"
                self.queue.update(job)
                results["failed"] += 1
                continue
            try:
                job.status = "running"
                job.attempts += 1
                self.queue.update(job)
                handler(job.payload)
                job.status = "done"
                job.last_error = ""
                results["processed"] += 1
            except PermissionError as exc:
                job.status = "blocked"
                job.last_error = str(exc)
                results["blocked"] += 1
            except Exception as exc:
                job.last_error = str(exc)
                job.status = "retry" if job.attempts < self.max_attempts else "failed"
                results["failed"] += 1
            self.queue.update(job)
        return results
