"""v30.19 - P1 GUI control panel for RAG, embeddings and production gates.

The panel is intentionally side-effect free. It exposes all P0/P1 runtime actions
as UI descriptors so desktop/web shells can render buttons without executing
migration, repair or network calls during view rendering.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GuiAction:
    id: str
    title: str
    command: str
    group: str
    risk: str = "read"
    description: str = ""
    requires_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


P1_ACTIONS: tuple[GuiAction, ...] = (
    GuiAction("p1.rag.status", "RAG Status", "p1-rag-status", "rag", description="Show active RAG store, source and index status."),
    GuiAction("p1.rag.ingest.file", "Import File", "p1-rag-ingest-file", "rag", risk="write", description="Import one document through the parser-backed RAG path.", requires_confirmation=True),
    GuiAction("p1.rag.ingest.dir", "Import Folder", "p1-rag-ingest-dir", "rag", risk="write", description="Batch-import supported files; parser errors and OCR_REQUIRED remain visible.", requires_confirmation=True),
    GuiAction("p1.rag.reindex", "Reindex Vectors", "p1-rag-reindex", "rag", risk="write", description="Rebuild vectors for the active embedding provider identity.", requires_confirmation=True),
    GuiAction("p1.rag.migrate_postgres", "Migrate SQLite to PostgreSQL", "p1-rag-migrate-postgres", "store", risk="destructive", description="Copy local SQLite RAG data into the configured PostgreSQL/pgvector store.", requires_confirmation=True),
    GuiAction("p1.store.pgvector.readiness", "pgvector Readiness", "p3-pgvector-readiness", "store", description="Check DATABASE_URL and pgvector extension readiness."),
    GuiAction("p1.store.status", "RAG Store Status", "p3-rag-store-status", "store", description="Show selected RAG store backend and validation snapshot."),
    GuiAction("p1.embedding.config", "Embedding Config", "p1-embedding-config", "embedding", description="Validate provider/model/dimension/fallback configuration."),
    GuiAction("p1.embedding.health", "Provider Health", "p1-provider-health", "embedding", description="Check production readiness of the active embedding provider."),
    GuiAction("p1.embedding.audit", "Vector Provider Audit", "p1-vector-provider-audit", "embedding", description="Detect stale vectors, missing vectors and dimension drift."),
    GuiAction("p1.embedding.repair", "Repair Vector Index", "p1-vector-index-repair", "embedding", risk="write", description="Repair provider/model/dimension drift via deterministic reindex.", requires_confirmation=True),
    GuiAction("p1.quality.golden", "Golden Retrieval Eval", "p1-golden-eval", "quality", description="Run curated retrieval quality checks with recall/MRR/nDCG."),
    GuiAction("p1.quality.production", "Production Gate", "p1-production", "quality", description="Run technical, provider, vector and Golden Retrieval production gate."),
    GuiAction("p1.quality.gate", "P1 Gate", "p1-gate", "quality", description="Run the P1 release gate."),
)


class P1ControlPanel:
    """Render metadata needed by GUI shells for the current P1 runtime surface."""

    def __init__(self, actions: tuple[GuiAction, ...] = P1_ACTIONS):
        self._actions = actions

    def actions(self, group: str | None = None) -> list[dict[str, Any]]:
        items = [action for action in self._actions if group is None or action.group == group]
        return [item.to_dict() for item in sorted(items, key=lambda item: (item.group, item.title))]

    def groups(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for action in self.actions():
            grouped.setdefault(action["group"], []).append(action)
        return grouped

    def render(self, latest: dict[str, Any] | None = None) -> dict[str, Any]:
        latest = latest or {}
        blockers = _extract_blockers(latest)
        return {
            "schema": "secondbrain.gui.p1_control_panel.v1",
            "status": "blocked" if blockers else "ready_for_checks",
            "blockers": blockers,
            "groups": self.groups(),
            "action_count": len(self._actions),
            "write_actions": [action.id for action in self._actions if action.risk in {"write", "destructive"}],
            "confirmation_required": [action.id for action in self._actions if action.requires_confirmation],
            "latest": latest,
        }


def _extract_blockers(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("blockers", [])
    if isinstance(raw, int):
        return ["production_gate_blockers"] if raw else []
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if raw:
        return [str(raw)]
    return []
