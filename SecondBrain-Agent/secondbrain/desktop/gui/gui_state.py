from dataclasses import dataclass, field
from typing import Any

@dataclass
class GuiState:
    active_module: str = "dashboard"
    selected_workspace: str = "default"
    open_tabs: list[str] = field(default_factory=list)
    notifications: list[dict[str, Any]] = field(default_factory=list)
    background_jobs: list[dict[str, Any]] = field(default_factory=list)
    startup_status: str = "created"
    health_snapshot: dict[str, str] = field(default_factory=dict)
    recovery_mode: bool = False

    def activate(self, module_id: str) -> None:
        self.active_module = module_id
        if module_id not in self.open_tabs:
            self.open_tabs.append(module_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "active_module": self.active_module,
            "selected_workspace": self.selected_workspace,
            "open_tabs": list(self.open_tabs),
            "notifications": list(self.notifications),
            "background_jobs": list(self.background_jobs),
            "startup_status": self.startup_status,
            "health_snapshot": dict(self.health_snapshot),
            "recovery_mode": self.recovery_mode,
        }
