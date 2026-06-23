from dataclasses import dataclass
from .gui_state import GuiState
from .module_registry import ModuleRegistry
from .gui_router import GuiRouter, RouteResult
from .gui_shell import GuiShell, ShellModel
from .lifecycle_manager import LifecycleManager, LifecycleResult
from .shutdown_manager import ShutdownManager, ShutdownResult
from .error_boundary import ErrorBoundary

@dataclass
class GuiApp:
    state: GuiState
    registry: ModuleRegistry
    router: GuiRouter
    shell: GuiShell
    lifecycle: LifecycleManager
    shutdown_manager: ShutdownManager
    error_boundary: ErrorBoundary

    @classmethod
    def create(cls) -> "GuiApp":
        state = GuiState()
        registry = ModuleRegistry.defaults()
        error_boundary = ErrorBoundary()
        return cls(
            state=state,
            registry=registry,
            router=GuiRouter(registry, state),
            shell=GuiShell(registry, state),
            lifecycle=LifecycleManager(state, error_boundary=error_boundary),
            shutdown_manager=ShutdownManager(state),
            error_boundary=error_boundary,
        )

    def start(self) -> LifecycleResult:
        return self.lifecycle.start()

    def navigate(self, module_id: str) -> RouteResult:
        return self.router.navigate(module_id)

    def render_shell(self) -> ShellModel:
        return self.shell.model()

    def shutdown(self) -> ShutdownResult:
        return self.shutdown_manager.shutdown()
