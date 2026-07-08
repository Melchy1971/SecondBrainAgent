from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")

@dataclass
class GuiError:
    source: str
    message: str
    recoverable: bool = True

class ErrorBoundary:
    def __init__(self) -> None:
        self.errors: list[GuiError] = []
        self.disabled_modules: set[str] = set()

    def capture(self, source: str, error: Exception, recoverable: bool = True) -> GuiError:
        gui_error = GuiError(source=source, message=str(error), recoverable=recoverable)
        self.errors.append(gui_error)
        if recoverable:
            self.disabled_modules.add(source)
        return gui_error

    def guard(self, source: str, operation: Callable[[], T], fallback: T) -> T:
        try:
            return operation()
        except Exception as exc:
            self.capture(source, exc, recoverable=True)
            return fallback

    def has_critical_errors(self) -> bool:
        return any(not error.recoverable for error in self.errors)
