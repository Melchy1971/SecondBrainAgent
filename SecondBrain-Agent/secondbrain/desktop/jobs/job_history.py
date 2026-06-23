from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .job_state import DesktopJob


@dataclass
class JobHistory:
    max_entries: int = 200
    entries: list[DesktopJob] = field(default_factory=list)

    def add(self, job: DesktopJob) -> None:
        self.entries.append(job)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def latest(self, limit: int = 20) -> list[DesktopJob]:
        return list(reversed(self.entries[-max(0, limit):]))

    def failed(self) -> list[DesktopJob]:
        return [job for job in self.entries if job.state.value in {"failed", "timeout"}]

    def to_dict(self) -> dict:
        return {"max_entries": self.max_entries, "entries": [job.to_dict() for job in self.entries]}

    @classmethod
    def from_dict(cls, data: dict) -> "JobHistory":
        history = cls(max_entries=int(data.get("max_entries", 200)))
        history.entries = [DesktopJob.from_dict(item) for item in data.get("entries", [])]
        return history

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "JobHistory":
        source = Path(path)
        if not source.exists():
            return cls()
        return cls.from_dict(json.loads(source.read_text(encoding="utf-8")))
