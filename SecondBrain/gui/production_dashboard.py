"""P5 v30.19 - Production Dashboard with P1 gate visibility."""

from __future__ import annotations

from typing import Any


class ProductionDashboard:
    def render(self, sections: dict):
        blocking_sections = [name for name, value in sections.items() if isinstance(value, dict) and value.get("ok") is False]
        return {
            "status": "BLOCKED" if blocking_sections else "PASS",
            "sections": sections,
            "section_count": len(sections),
            "blocking_sections": blocking_sections,
        }

    def render_p1(self, production_gate: dict[str, Any] | None = None, provider_health: dict[str, Any] | None = None, vector_audit: dict[str, Any] | None = None, golden_eval: dict[str, Any] | None = None) -> dict[str, Any]:
        sections = {
            "production_gate": production_gate or {"status": "not_run", "command": "p1-production"},
            "provider_health": provider_health or {"status": "not_run", "command": "p1-provider-health"},
            "vector_audit": vector_audit or {"status": "not_run", "command": "p1-vector-provider-audit"},
            "golden_eval": golden_eval or {"status": "not_run", "command": "p1-golden-eval"},
        }
        blockers = []
        for name, payload in sections.items():
            if payload.get("ok") is False or payload.get("status") == "blocked":
                blockers.append(name)
        return {
            "schema": "secondbrain.gui.production_dashboard.p1.v1",
            "status": "blocked" if blockers else "ready_for_checks",
            "blockers": blockers,
            "sections": sections,
            "primary_commands": ["p1-production", "p1-gate"],
            "diagnostic_commands": ["p1-provider-health", "p1-vector-provider-audit", "p1-golden-eval", "p1-embedding-config"],
        }
