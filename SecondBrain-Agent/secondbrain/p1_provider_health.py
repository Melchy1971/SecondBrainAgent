from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from secondbrain.p1_embedding_config import evaluate_embedding_config

P1_PROVIDER_HEALTH_SCHEMA = "secondbrain.p1_provider_health.v1"


class ProviderRuntime(Protocol):
    reports_dir: Path
    embedding_provider: Any


def evaluate_embedding_provider_health(runtime: ProviderRuntime, *, production: bool = True, write_report: bool = False) -> dict[str, Any]:
    """Evaluate embedding-provider readiness without allowing silent test fallback.

    Production rules:
    - local deterministic embeddings are valid for tests, but never production-ready
    - network providers must pass their own health probe
    - explicit fallback allowance is reported as a warning, not as production proof
    """
    status = runtime.embedding_provider.status()
    provider = str(status.get("provider") or getattr(runtime.embedding_provider, "name", "unknown"))
    project_root = Path(runtime.reports_dir).parent.parent
    config_health = evaluate_embedding_config(project_root, production=production, write_report=write_report)
    blockers: list[str] = list(config_health.get("blockers", []))
    warnings: list[str] = list(config_health.get("warnings", []))

    if not bool(status.get("ok")):
        blockers.append("embedding_provider_health_probe_failed")
    if production and not bool(status.get("production_ready")):
        blockers.append("embedding_provider_not_production_ready")
    if production and provider in {"local-deterministic", "local", "deterministic"}:
        blockers.append("local_deterministic_embeddings_not_allowed_for_production")
    if bool(status.get("fallback_allowed")):
        warnings.append("embedding_fallback_explicitly_allowed")
    if bool(status.get("fallback_used")):
        warnings.append("embedding_fallback_used_or_would_be_used")
    if production and bool(status.get("fallback_used")):
        blockers.append("embedding_fallback_cannot_prove_production_readiness")

    payload = {
        "schema": P1_PROVIDER_HEALTH_SCHEMA,
        "ok": not blockers,
        "status": "pass" if not blockers else "blocked",
        "production": production,
        "provider": provider,
        "blockers": blockers,
        "warnings": warnings,
        "provider_status": status,
        "config_health": config_health,
        "remediation": None if not blockers else "configure a semantic embedding provider with a passing health probe; use local fallback only for tests/dev",
    }
    if write_report:
        reports_dir = Path(runtime.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p1_provider_health_latest.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload
