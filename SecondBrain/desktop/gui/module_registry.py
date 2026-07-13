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

    _CORE_MODULES = [
        ("dashboard", "Dashboard", "/dashboard"),
        ("documents", "Documents", "/documents"),
        ("search", "Search", "/search"),
        ("connectors", "Connectors", "/connectors"),
        ("settings", "Settings", "/settings"),
        ("jobs", "Jobs", "/jobs"),
        ("status", "Status", "/status"),
        ("notifications", "Notifications", "/notifications"),
    ]

    @classmethod
    def defaults(cls) -> "ModuleRegistry":
        registry = cls()
        for module_id, title, route in cls._CORE_MODULES:
            registry.register(GuiModule(module_id=module_id, title=title, route=route))
        return registry

    @classmethod
    def live(cls, root=None) -> "ModuleRegistry":
        """Registry mit an reale Daten gebundenen Modul-Factories.

        Zusaetzlich zu den Kernmodulen wird 'desktop_foundation' registriert
        (Voraussetzung fuer das RC1-Gate). Jede Factory liefert ein
        Live-View-Model aus Vault/Inbox/Config/Runtime.
        """
        from pathlib import Path
        from .data_providers import LiveDataService

        service = LiveDataService(Path(root)) if root else LiveDataService()
        registry = cls()
        registry.register(GuiModule(
            module_id="desktop_foundation",
            title="Desktop Foundation",
            route="/foundation",
            factory=service.provider_for("desktop_foundation"),
        ))
        for module_id, title, route in cls._CORE_MODULES:
            registry.register(GuiModule(
                module_id=module_id,
                title=title,
                route=route,
                factory=service.provider_for(module_id),
            ))
        registry._service = service  # type: ignore[attr-defined]
        return registry
