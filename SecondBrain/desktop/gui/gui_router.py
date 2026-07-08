from dataclasses import dataclass
from .module_registry import ModuleRegistry, GuiModule
from .gui_state import GuiState

@dataclass(frozen=True)
class RouteResult:
    module_id: str
    route: str
    title: str

class GuiRouter:
    def __init__(self, registry: ModuleRegistry, state: GuiState) -> None:
        self.registry = registry
        self.state = state

    def navigate(self, module_id: str) -> RouteResult:
        module = self.registry.get(module_id)
        self.state.activate(module.module_id)
        return RouteResult(module_id=module.module_id, route=module.route, title=module.title)

    def resolve_route(self, route: str) -> GuiModule:
        for module in self.registry.list_modules():
            if module.route == route:
                return module
        raise KeyError(f"unknown gui route: {route}")
