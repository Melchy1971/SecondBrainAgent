"""P5 v30.19 - RAG Explorer with parser/store/index controls."""

from __future__ import annotations

from typing import Any


class RagExplorer:
    def render(self, results: list[dict]):
        return {
            "result_count": len(results),
            "results": results,
        }

    def render_import_center(self, ingest_result: dict[str, Any] | None = None) -> dict[str, Any]:
        result = ingest_result or {"status": "not_run"}
        parse_status = result.get("parse_status") or result.get("parser_status") or result.get("status")
        blocked = parse_status in {"error", "ocr_required", "OCR_REQUIRED", "blocked"}
        return {
            "schema": "secondbrain.gui.rag_import_center.v1",
            "status": "blocked" if blocked else "ready",
            "parse_status": parse_status,
            "commands": ["p1-rag-ingest-file", "p1-rag-ingest-dir", "p1-rag-sources", "p1-rag-validate"],
            "supported_statuses": ["parsed", "indexed", "ocr_required", "error", "blocked"],
            "latest": result,
        }

    def render_index_center(self, audit_result: dict[str, Any] | None = None) -> dict[str, Any]:
        audit = audit_result or {"status": "not_run"}
        return {
            "schema": "secondbrain.gui.rag_index_center.v1",
            "status": audit.get("status", "not_run"),
            "current_provider": audit.get("current_provider"),
            "providers": audit.get("providers", []),
            "blockers": audit.get("blockers", []),
            "commands": ["p1-vector-provider-audit", "p1-vector-index-repair", "p1-rag-reindex"],
            "latest": audit,
        }
