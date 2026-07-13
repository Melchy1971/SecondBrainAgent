"""Production gate + provider-health report for RAG embedding providers.

The gate FAILs on any failing health probe and never PASSes a dev-only provider
in production. It is the single decision point that turns a provider's self-report
into an allow/block verdict, so callers cannot accidentally ship fake embeddings.
"""

from __future__ import annotations

from typing import Any

from secondbrain.rag.providers.base import ProviderHealthReport, provider_index_identity


def provider_health(provider: Any) -> ProviderHealthReport:
    """Return a provider's health report, running a live probe if it supports one.

    Providers without a ``health()`` method are reported as unknown/FAIL rather
    than assumed healthy - unknown state must never pass a production gate.
    """

    probe = getattr(provider, "health", None)
    if callable(probe):
        report = probe()
        if isinstance(report, ProviderHealthReport):
            return report
    name = str(getattr(provider, "name", "unknown"))
    return ProviderHealthReport(
        status="FAIL",
        provider=name,
        model=getattr(provider, "model", None),
        dimensions=int(getattr(provider, "dimensions", 0) or 0),
        semantic=bool(getattr(provider, "semantic", False)),
        production_ready=False,
        dev_only=bool(getattr(provider, "dev_only", False)),
        error="provider does not expose a health() probe",
    )


def embedding_production_gate(
    provider: Any,
    *,
    environment: str = "production",
    allow_dev_only: bool = False,
) -> dict[str, Any]:
    """Return an allow/block verdict for ``provider`` in ``environment``.

    Blocks when the health probe fails, and - in a production environment - when
    the provider is dev-only or not production-ready (unless ``allow_dev_only``).
    """

    report = provider_health(provider)
    is_production = environment.strip().lower().startswith("prod")
    reasons: list[str] = []

    if report.status != "PASS":
        reasons.append(f"health_probe_failed:{report.error}")
    if is_production and report.dev_only and not allow_dev_only:
        reasons.append("dev_only_provider_blocked_in_production")
    if is_production and not report.production_ready and not (report.dev_only and allow_dev_only):
        reasons.append("provider_not_production_ready")

    status = "PASS" if not reasons else "FAIL"
    result = report.to_dict()
    result["provider_health"] = result.pop("status")
    result.update(
        {
            "status": status,
            "environment": environment,
            "index_identity": provider_index_identity(provider),
            "reasons": reasons,
        }
    )
    return result
