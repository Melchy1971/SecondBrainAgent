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

    @classmethod
    def create_live(cls, root=None) -> "GuiApp":
        """App mit Live-Daten-Bindung: reale Modul-Factories + reale Startup-Checks."""
        from .startup_checks import StartupChecks

        state = GuiState()
        registry = ModuleRegistry.live(root)
        error_boundary = ErrorBoundary()
        lifecycle = LifecycleManager(
            state,
            startup_checks=StartupChecks.live(root),
            error_boundary=error_boundary,
        )
        return cls(
            state=state,
            registry=registry,
            router=GuiRouter(registry, state),
            shell=GuiShell(registry, state),
            lifecycle=lifecycle,
            shutdown_manager=ShutdownManager(state),
            error_boundary=error_boundary,
        )

    def start(self) -> LifecycleResult:
        return self.lifecycle.start()

    def navigate(self, module_id: str) -> RouteResult:
        return self.router.navigate(module_id)

    def render_shell(self) -> ShellModel:
        return self.shell.model()

    def render_active_live(self) -> dict:
        """Live-View-Model des aktiven Moduls (gekapselt, wirft nie)."""
        return self.render_module_live(self.state.active_module)

    def render_module_live(self, module_id: str) -> dict:
        """Live-View-Model eines Moduls ueber seine gebundene Factory."""
        try:
            module = self.registry.get(module_id)
        except KeyError:
            return {"module": module_id, "error": "unknown module"}
        factory = module.factory
        if factory is None:
            return {"module": module_id, "live": False}
        return self.error_boundary.guard(
            module_id, factory, {"module": module_id, "error": "render failed"}
        )

    def shutdown(self) -> ShutdownResult:
        return self.shutdown_manager.shutdown()
