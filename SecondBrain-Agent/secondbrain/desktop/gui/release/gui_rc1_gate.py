from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

REQUIRED_MODULES = (
    "desktop_foundation",
    "dashboard",
    "documents",
    "search",
    "connectors",
    "settings",
    "jobs",
)

REQUIRED_FLOWS = (
    "import_index_search",
    "connector_sync_import",
    "settings_restart",
)

REQUIRED_ACCESSIBILITY = (
    "keyboard_navigation",
    "screenreader_labels",
    "empty_states",
    "error_states",
)


@dataclass(frozen=True)
class GateCheck:
    name: str
    status: str
    severity: str = "info"
    message: str = ""

    def is_blocking(self) -> bool:
        return self.status in {"FAIL", "BLOCKED"} and self.severity in {"critical", "blocker"}


@dataclass
class GuiRc1Input:
    modules: dict[str, str] = field(default_factory=dict)
    flows: dict[str, str] = field(default_factory=dict)
    accessibility: dict[str, str] = field(default_factory=dict)
    tests_passed: bool = True
    critical_errors: list[str] = field(default_factory=list)


@dataclass
class GuiRc1Report:
    status: str
    generated_at: str
    checks: list[GateCheck]
    blockers: list[str]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "generated_at": self.generated_at,
            "checks": [check.__dict__ for check in self.checks],
            "blockers": list(self.blockers),
        }


class GuiRc1Gate:
    def evaluate(self, payload: GuiRc1Input) -> GuiRc1Report:
        checks: list[GateCheck] = []
        checks.extend(self._check_named_statuses("module", REQUIRED_MODULES, payload.modules))
        checks.extend(self._check_named_statuses("flow", REQUIRED_FLOWS, payload.flows))
        checks.extend(self._check_named_statuses("accessibility", REQUIRED_ACCESSIBILITY, payload.accessibility))
        checks.append(
            GateCheck(
                name="tests",
                status="PASS" if payload.tests_passed else "FAIL",
                severity="critical" if not payload.tests_passed else "info",
                message="Automated tests must pass for GUI RC1.",
            )
        )
        for error in payload.critical_errors:
            checks.append(GateCheck(name="critical_error", status="FAIL", severity="critical", message=error))
        blockers = [check.message or check.name for check in checks if check.is_blocking()]
        status = "PASS" if not blockers else "BLOCKED"
        return GuiRc1Report(
            status=status,
            generated_at=datetime.now(timezone.utc).isoformat(),
            checks=checks,
            blockers=blockers,
        )

    def _check_named_statuses(self, prefix: str, required: Iterable[str], actual: dict[str, str]) -> list[GateCheck]:
        checks: list[GateCheck] = []
        for name in required:
            status = actual.get(name, "MISSING").upper()
            if status == "PASS":
                checks.append(GateCheck(name=f"{prefix}:{name}", status="PASS"))
            elif status in {"WARNING", "WARN"}:
                checks.append(GateCheck(name=f"{prefix}:{name}", status="WARNING", severity="warning"))
            else:
                checks.append(
                    GateCheck(
                        name=f"{prefix}:{name}",
                        status="FAIL",
                        severity="critical",
                        message=f"Required GUI RC1 {prefix} is not ready: {name}",
                    )
                )
        return checks
