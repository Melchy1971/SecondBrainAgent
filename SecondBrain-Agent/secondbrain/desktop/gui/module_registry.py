from dataclasses import dataclass, field
from typing import Callable, Any

@dataclass(frozen=True)
class GuiModule:
    module_id: str
    title: str
    route: str
    factory: Callable[[], Any] | None = None
    required: bool = True

class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, GuiModule] = {}

    def register(self, module: GuiModule) -> None:
        if not module.module_id.strip():
            raise ValueError("module_id is required")
        if not module.route.startswith("/"):
            raise ValueError("route must start with '/'")
        self._modules[module.module_id] = module

    def get(self, module_id: str) -> GuiModule:
        try:
            return self._modules[module_id]
        except KeyError as exc:
            raise KeyError(f"unknown gui module: {module_id}") from exc

    def list_modules(self) -> list[GuiModule]:
        return list(self._modules.values())

    def has(self, module_id: str) -> bool:
        return module_id in self._modules

    @classmethod
    def defaults(cls) -> "ModuleRegistry":
        registry = cls()
        for module_id, title, route in [
            ("dashboard", "Dashboard", "/dashboard"),
            ("documents", "Documents", "/documents"),
            ("search", "Search", "/search"),
            ("connectors", "Connectors", "/connectors"),
            ("settings", "Settings", "/settings"),
            ("jobs", "Jobs", "/jobs"),
            ("status", "Status", "/status"),
            ("notifications", "Notifications", "/notifications"),
        ]:
            registry.register(GuiModule(module_id=module_id, title=title, route=route))
        return registry
