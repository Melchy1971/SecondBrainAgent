from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from secondbrain.p1_golden_retrieval import evaluate_golden_retrieval

PRODUCTION_GOLDEN_SCHEMA = "secondbrain.p1_production.golden.v1"


class ProductionRuntime(Protocol):
    reports_dir: Path

    def production_gate(self, write_report: bool = False) -> dict[str, Any]:
        ...

    def hybrid_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        ...

    def answer(self, query: str, limit: int = 4) -> dict[str, Any]:
        ...


def production_gate_with_golden(runtime: ProductionRuntime, project_root: str | Path, *, write_report: bool = False) -> dict[str, Any]:
    """Run P1 production gate and require Golden Retrieval Eval.

    This wrapper keeps the existing P1 runtime gate stable while adding a
    production-only quality gate based on curated retrieval labels.
    """
    base = runtime.production_gate(write_report=False)
    golden = evaluate_golden_retrieval(runtime, project_root, write_report=write_report)
    checks = list(base.get("checks", []))
    checks.append(
        {
            "name": "golden_retrieval_eval_passes",
            "ok": bool(golden.get("ok")),
            "severity": "blocker",
            "detail": {
                "schema": golden.get("schema"),
                "dataset_id": golden.get("dataset", {}).get("dataset_id"),
                "source": golden.get("dataset", {}).get("source"),
                "query_count": golden.get("query_count", 0),
                "pass_rate": golden.get("pass_rate", 0.0),
                "blockers": golden.get("blockers", 0),
                "warnings": golden.get("warnings", 0),
            },
        }
    )
    blockers = sum(1 for check in checks if not check.get("ok") and check.get("severity") == "blocker")
    payload = {
        "schema": PRODUCTION_GOLDEN_SCHEMA,
        "generated_at": base.get("generated_at"),
        "ok": blockers == 0,
        "status": "pass" if blockers == 0 else "blocked",
        "blockers": blockers,
        "checks": checks,
        "base_production": base,
        "golden_retrieval": golden,
    }
    if write_report:
        reports_dir = Path(project_root).resolve() / "runtime" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p1_production_latest.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload
