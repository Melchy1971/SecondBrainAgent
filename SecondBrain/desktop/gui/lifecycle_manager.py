from dataclasses import dataclass
from .gui_state import GuiState
from .startup_checks import StartupChecks, StartupCheckResult
from .error_boundary import ErrorBoundary

@dataclass(frozen=True)
class LifecycleResult:
    status: str
    checks: list[StartupCheckResult]
    recovery_mode: bool

class LifecycleManager:
    def __init__(self, state: GuiState, startup_checks: StartupChecks | None = None, error_boundary: ErrorBoundary | None = None) -> None:
        self.state = state
        self.startup_checks = startup_checks or StartupChecks()
        self.error_boundary = error_boundary or ErrorBoundary()

    def start(self) -> LifecycleResult:
        self.state.startup_status = "starting"
        results = self.startup_checks.run()
        self.state.health_snapshot = {result.name: result.status for result in results}
        blocked = self.startup_checks.is_blocked(results)
        self.state.recovery_mode = blocked or bool(self.error_boundary.errors)
        self.state.startup_status = "blocked" if blocked else "ready"
        return LifecycleResult(self.state.startup_status.upper(), results, self.state.recovery_mode)

    def enter_safe_mode(self) -> None:
        self.state.recovery_mode = True
        self.state.startup_status = "safe_mode"
