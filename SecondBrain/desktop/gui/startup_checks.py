from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class StartupCheck:
    name: str
    required: bool = True
    check: Callable[[], bool] | None = None

@dataclass(frozen=True)
class StartupCheckResult:
    name: str
    status: str
    required: bool

class StartupChecks:
    def __init__(self, checks: list[StartupCheck] | None = None) -> None:
        self.checks = checks or self.default_checks()

    @staticmethod
    def default_checks() -> list[StartupCheck]:
        return [
            StartupCheck("settings", True),
            StartupCheck("workspace", True),
            StartupCheck("database", False),
            StartupCheck("rag", False),
            StartupCheck("connectors", False),
            StartupCheck("background_jobs", True),
            StartupCheck("dashboard", True),
        ]

    @classmethod
    def live(cls, root=None) -> "StartupChecks":
        """Checks, die an reale Pfade/Daten gebunden sind (Zielumgebung)."""
        from pathlib import Path
        from .data_providers import LiveDataService

        service = LiveDataService(Path(root)) if root else LiveDataService()

        def _settings_ok() -> bool:
            return (service.config_dir.exists()
                    or (service.data_dir / "desktop_app" / "settings.json").exists())

        return cls([
            StartupCheck("settings", True, _settings_ok),
            StartupCheck("workspace", True, lambda: service.vault.exists()),
            StartupCheck("database", False, lambda: service.runtime_dir.exists()),
            StartupCheck("rag", False, lambda: bool(service._vault_markdown())),
            StartupCheck("connectors", False, lambda: any(c["enabled"] for c in service._connector_list())),
            StartupCheck("background_jobs", True, lambda: service.root.exists()),
            StartupCheck("dashboard", True, lambda: service.vault.exists()),
        ])

    def run(self) -> list[StartupCheckResult]:
        results: list[StartupCheckResult] = []
        for check in self.checks:
            ok = True if check.check is None else bool(check.check())
            results.append(StartupCheckResult(check.name, "PASS" if ok else "FAIL", check.required))
        return results

    def is_blocked(self, results: list[StartupCheckResult]) -> bool:
        return any(result.required and result.status != "PASS" for result in results)
