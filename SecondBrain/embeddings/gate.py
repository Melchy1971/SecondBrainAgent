"""Production gate. FAILs on any error and never PASSes a non-production provider."""

from __future__ import annotations

from secondbrain.embeddings.base import EmbeddingProvider


def embedding_production_gate(provider: EmbeddingProvider, *, environment: str = "production") -> dict:
    health = provider.health()
    reasons: list[str] = []
    if health.status != "PASS":
        reasons.append(f"health={health.status}:{health.error}")
    if environment.lower().startswith("prod") and not health.production_ready:
        reasons.append("provider is not production-ready (fake/local not allowed in production)")
    status = "PASS" if not reasons else "FAIL"
    result = health.to_dict()
    result["provider_health"] = result.pop("status")   # keep provider health separately
    result.update({"status": status, "environment": environment, "reasons": reasons})
    return result
