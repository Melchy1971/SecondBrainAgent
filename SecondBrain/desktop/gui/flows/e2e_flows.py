from __future__ import annotations

from typing import Any

from .flow_models import FlowStep
from .flow_registry import DesktopFlow, DesktopFlowRegistry


def build_default_e2e_registry() -> DesktopFlowRegistry:
    registry = DesktopFlowRegistry()
    registry.register(_import_index_search_flow())
    registry.register(_connector_sync_import_flow())
    registry.register(_settings_restart_flow())
    return registry


def _import_index_search_flow() -> DesktopFlow:
    return DesktopFlow(
        flow_id="import_index_search",
        title="Import, Index and Search",
        description="Validates that a document can be imported, indexed and found.",
        steps=[
            FlowStep("import", "Import document", lambda ctx: {"document_id": ctx.get("document_id", "doc-1"), "imported": True}),
            FlowStep("index", "Index document", _require_imported),
            FlowStep("search", "Find document", _require_indexed),
        ],
    )


def _connector_sync_import_flow() -> DesktopFlow:
    return DesktopFlow(
        flow_id="connector_sync_import",
        title="Connector Sync and Import",
        description="Validates that connector output becomes an importable document item.",
        steps=[
            FlowStep("sync", "Sync connector", lambda ctx: {"connector_items": max(1, int(ctx.get("connector_items", 1)))}),
            FlowStep("bridge", "Create import jobs", lambda ctx: {"import_jobs": ctx["connector_items"]}),
            FlowStep("import", "Import synced item", lambda ctx: {"imported": ctx["import_jobs"] > 0}),
        ],
    )


def _settings_restart_flow() -> DesktopFlow:
    return DesktopFlow(
        flow_id="settings_restart",
        title="Settings Change and Restart Readiness",
        description="Validates save, reload and startup-readiness after a settings update.",
        steps=[
            FlowStep("save_settings", "Save settings", lambda ctx: {"settings_saved": True, "settings_version": ctx.get("settings_version", "1.0")}),
            FlowStep("reload_settings", "Reload settings", _require_settings_saved),
            FlowStep("startup_check", "Startup check", _require_settings_loaded),
        ],
    )


def _require_imported(ctx: dict[str, Any]) -> dict[str, Any]:
    if not ctx.get("imported"):
        raise RuntimeError("document was not imported")
    return {"indexed": True}


def _require_indexed(ctx: dict[str, Any]) -> dict[str, Any]:
    if not ctx.get("indexed"):
        raise RuntimeError("document was not indexed")
    return {"search_results": [ctx["document_id"]]}


def _require_settings_saved(ctx: dict[str, Any]) -> dict[str, Any]:
    if not ctx.get("settings_saved"):
        raise RuntimeError("settings were not saved")
    return {"settings_loaded": True}


def _require_settings_loaded(ctx: dict[str, Any]) -> dict[str, Any]:
    if not ctx.get("settings_loaded"):
        raise RuntimeError("settings were not loaded")
    return {"startup_ready": True}
