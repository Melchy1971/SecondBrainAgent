from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Any

JobHandler = Callable[[dict[str, Any]], Any]


@dataclass(slots=True)
class RegisteredJob:
    name: str
    handler: JobHandler
    description: str = ""
    cancellable: bool = True
    timeout_seconds: int | None = None


@dataclass
class JobRegistry:
    _jobs: dict[str, RegisteredJob] = field(default_factory=dict)

    def register(self, name: str, handler: JobHandler, *, description: str = "", cancellable: bool = True, timeout_seconds: int | None = None) -> None:
        if not name or not name.strip():
            raise ValueError("job name is required")
        if not callable(handler):
            raise TypeError("job handler must be callable")
        self._jobs[name] = RegisteredJob(name=name, handler=handler, description=description, cancellable=cancellable, timeout_seconds=timeout_seconds)

    def get(self, name: str) -> RegisteredJob:
        try:
            return self._jobs[name]
        except KeyError as exc:
            raise KeyError(f"unknown job: {name}") from exc

    def has(self, name: str) -> bool:
        return name in self._jobs

    def list_jobs(self) -> list[RegisteredJob]:
        return [self._jobs[k] for k in sorted(self._jobs)]

    def names(self) -> Iterable[str]:
        return sorted(self._jobs)
