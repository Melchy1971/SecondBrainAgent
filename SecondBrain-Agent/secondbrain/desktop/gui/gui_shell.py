from dataclasses import dataclass
from .module_registry import ModuleRegistry
from .gui_state import GuiState

@dataclass(frozen=True)
class ShellModel:
    sidebar: list[dict[str, str]]
    active_module: str
    status: str

class GuiShell:
    def __init__(self, registry: ModuleRegistry, state: GuiState) -> None:
        self.registry = registry
        self.state = state

    def model(self) -> ShellModel:
        return ShellModel(
            sidebar=[{"id": m.module_id, "title": m.title, "route": m.route} for m in self.registry.list_modules()],
            active_module=self.state.active_module,
            status=self.state.startup_status,
        )
