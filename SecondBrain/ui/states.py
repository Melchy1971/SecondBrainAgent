"""Async UI state machine: idle -> loading -> success | error."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AsyncState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ViewState:
    state: AsyncState = AsyncState.IDLE
    message: str = ""
    error: str | None = None
    data: Any = None
    progress: float | None = None

    def start(self, message: str = "Loading…") -> "ViewState":
        self.state = AsyncState.LOADING; self.message = message; self.error = None; self.progress = 0.0
        return self

    def set_progress(self, value: float) -> "ViewState":
        self.progress = max(0.0, min(1.0, value)); return self

    def succeed(self, data: Any = None, message: str = "") -> "ViewState":
        self.state = AsyncState.SUCCESS; self.data = data; self.message = message
        self.error = None; self.progress = 1.0
        return self

    def fail(self, error: str) -> "ViewState":
        self.state = AsyncState.ERROR; self.error = error; self.progress = None
        return self

    @property
    def is_loading(self) -> bool:
        return self.state is AsyncState.LOADING

    @property
    def is_error(self) -> bool:
        return self.state is AsyncState.ERROR

    def to_dict(self) -> dict:
        return {"state": self.state.value, "message": self.message, "error": self.error,
                "progress": self.progress, "has_data": self.data is not None}
