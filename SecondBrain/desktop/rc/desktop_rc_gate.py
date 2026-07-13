from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .desktop_rc_checklist import DesktopRCChecklist, DesktopRCChecklistState
from .desktop_rc_manifest import DesktopRCManifest, DesktopRCManifestBuilder
from .desktop_rc_status import DesktopRCStatus, DesktopRCStatusSnapshot


@dataclass(frozen=True)
class DesktopRCGateResult:
    status: DesktopRCStatus
    checklist: DesktopRCChecklist
    manifest: DesktopRCManifest
    status_snapshot: DesktopRCStatusSnapshot

    @property
    def passed(self) -> bool:
        return self.status == DesktopRCStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status.value,
            "checklist": self.checklist.to_dict(),
            "manifest": self.manifest.to_dict(),
            "status_snapshot": self.status_snapshot.to_dict(),
        }


class DesktopRCGate:
    """Evaluates whether the P2.1 desktop foundation can be tagged as RC1."""

    REQUIRED_COMPONENTS = [
        "shell",
        "state",
        "router",
        "commands",
        "notifications",
        "status_service",
        "workspace_persistence",
        "background_jobs",
    ]

    def __init__(self, manifest_builder: DesktopRCManifestBuilder | None = None) -> None:
        self.manifest_builder = manifest_builder or DesktopRCManifestBuilder()

    def evaluate(
        self,
        *,
        rc_version: str,
        components: dict[str, bool],
        tests_passed: int,
        tests_failed: int = 0,
        warnings: list[str] | None = None,
    ) -> DesktopRCGateResult:
        warnings = list(warnings or [])
        checklist = DesktopRCChecklist()

        for component in self.REQUIRED_COMPONENTS:
            available = bool(components.get(component, False))
            checklist.add(
                key=component,
                title=f"Desktop component available: {component}",
                state=DesktopRCChecklistState.PASS if available else DesktopRCChecklistState.FAIL,
                evidence="present" if available else "missing",
                blocking=True,
            )

        checklist.add(
            key="tests",
            title="Desktop RC tests passed",
            state=DesktopRCChecklistState.PASS if tests_failed == 0 and tests_passed > 0 else DesktopRCChecklistState.FAIL,
            evidence=f"passed={tests_passed}; failed={tests_failed}",
            blocking=True,
        )

        for index, warning in enumerate(warnings, start=1):
            checklist.add(
                key=f"warning_{index}",
                title=warning,
                state=DesktopRCChecklistState.WARNING,
                evidence=warning,
                blocking=False,
            )

        status = DesktopRCStatus.PASS if checklist.passed else DesktopRCStatus.FAIL
        snapshot_components = {
            item.key: DesktopRCStatus.PASS if item.state == DesktopRCChecklistState.PASS else (
                DesktopRCStatus.WARNING if item.state == DesktopRCChecklistState.WARNING else DesktopRCStatus.FAIL
            )
            for item in checklist.items
        }
        status_snapshot = DesktopRCStatusSnapshot.from_components(
            snapshot_components,
            metrics={"tests_passed": tests_passed, "tests_failed": tests_failed},
        )
        manifest = self.manifest_builder.build(
            rc_version=rc_version,
            gate_status=status.value,
            test_summary={"passed": tests_passed, "failed": tests_failed},
            notes=warnings,
        )
        return DesktopRCGateResult(
            status=status,
            checklist=checklist,
            manifest=manifest,
            status_snapshot=status_snapshot,
        )
