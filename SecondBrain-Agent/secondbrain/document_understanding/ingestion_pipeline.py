"""P1.3.6 - End-to-end ingestion pipeline orchestration.

This module connects parser orchestration, ingestion quality gates, and the
existing text-ingestion boundary into one deterministic service. It prevents
partial side effects: rejected parser output is never ingested, while accepted
or review-worthy content is handed over with audit-friendly status metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .orchestrator import MultiFormatParserOrchestrator, ParseOrchestrationResult, default_multi_format_orchestrator
from .quality_gate import IngestionQualityGate, QualityDecision, QualityGatePolicy, QualityGateResult


class IngestionPipelineStatus(str, Enum):
    """Stable pipeline states for UI, jobs, logs, and release checks."""

    INGESTED = "ingested"
    INGESTED_WITH_REVIEW = "ingested_with_review"
    REJECTED = "rejected"
    INGESTION_FAILED = "ingestion_failed"


@runtime_checkable
class MetadataAwareTextIngestionRuntime(Protocol):
    """Optional richer ingestion boundary.

    Existing runtimes usually expose ``ingest_text(title, text, source_path,
    mime_type)``. Newer runtimes may accept metadata as a fifth argument. The
    pipeline supports both shapes without forcing a breaking change.
    """

    def ingest_text(
        self,
        title: str,
        text: str,
        source_path: str = "manual",
        mime_type: str = "text/plain",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...


@dataclass(frozen=True, slots=True)
class IngestionPipelineResult:
    """Result envelope for one file ingestion attempt."""

    path: str
    status: IngestionPipelineStatus
    orchestration: ParseOrchestrationResult
    quality: QualityGateResult
    ingested: bool = False
    ingestion_result: dict[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status in {IngestionPipelineStatus.INGESTED, IngestionPipelineStatus.INGESTED_WITH_REVIEW}

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "path": self.path,
            "status": self.status.value,
            "ingested": self.ingested,
            "parse": self.orchestration.to_dict(),
            "quality": self.quality.to_dict(),
            "ingestion_result": dict(self.ingestion_result),
            "errors": list(self.errors),
        }


class DocumentIngestionPipeline:
    """Parse, quality-check, and ingest a document path.

    Side-effect contract:
    - parser failures become ``REJECTED`` without calling ingestion runtime
    - quality rejects become ``REJECTED`` without calling ingestion runtime
    - accepted/review documents call ingestion exactly once
    - ingestion exceptions become ``INGESTION_FAILED`` and keep parse/gate data
    """

    def __init__(
        self,
        runtime: object,
        *,
        orchestrator: MultiFormatParserOrchestrator | None = None,
        quality_gate: IngestionQualityGate | None = None,
    ) -> None:
        if not hasattr(runtime, "ingest_text"):
            raise TypeError("runtime_must_expose_ingest_text")
        self.runtime = runtime
        self.orchestrator = orchestrator or default_multi_format_orchestrator()
        # File ingestion is intentionally more conservative than the generic
        # quality gate: short standalone documents remain ingestible, but are
        # surfaced for operator review.
        self.quality_gate = quality_gate or IngestionQualityGate(QualityGatePolicy(review_below_chars=80))

    def ingest_file(self, path: str | Path, mime_type: str | None = None) -> IngestionPipelineResult:
        source_path = str(path)
        orchestration = self.orchestrator.parse(path, mime_type=mime_type)
        quality = self.quality_gate.evaluate(orchestration)

        if quality.decision == QualityDecision.REJECT:
            return IngestionPipelineResult(
                path=source_path,
                status=IngestionPipelineStatus.REJECTED,
                orchestration=orchestration,
                quality=quality,
                ingested=False,
                errors=tuple(reason.value for reason in quality.reject_reasons),
            )

        parsed = orchestration.parsed
        metadata = _build_ingestion_metadata(orchestration, quality)
        try:
            ingestion_result = _call_ingest_text(
                self.runtime,
                title=parsed.title,
                text=parsed.text,
                source_path=parsed.source_path or source_path,
                mime_type=parsed.mime_type,
                metadata=metadata,
            )
        except Exception as exc:  # noqa: BLE001 - boundary must return state, not crash batch jobs
            return IngestionPipelineResult(
                path=source_path,
                status=IngestionPipelineStatus.INGESTION_FAILED,
                orchestration=orchestration,
                quality=quality,
                ingested=False,
                errors=(f"ingestion_exception:{exc}",),
            )

        result_ok = bool(ingestion_result.get("ok", True))
        if not result_ok:
            return IngestionPipelineResult(
                path=source_path,
                status=IngestionPipelineStatus.INGESTION_FAILED,
                orchestration=orchestration,
                quality=quality,
                ingested=False,
                ingestion_result=dict(ingestion_result),
                errors=(str(ingestion_result.get("reason") or "ingestion_runtime_returned_not_ok"),),
            )

        status = (
            IngestionPipelineStatus.INGESTED_WITH_REVIEW
            if quality.decision == QualityDecision.REVIEW
            else IngestionPipelineStatus.INGESTED
        )
        return IngestionPipelineResult(
            path=source_path,
            status=status,
            orchestration=orchestration,
            quality=quality,
            ingested=True,
            ingestion_result=dict(ingestion_result),
        )


def _build_ingestion_metadata(orchestration: ParseOrchestrationResult, quality: QualityGateResult) -> dict[str, Any]:
    parsed_payload = orchestration.parsed.to_ingestion_payload()
    return {
        **dict(parsed_payload.get("metadata", {})),
        "parser_selection": orchestration.selection.to_dict(),
        "parser_warnings": list(orchestration.warnings),
        "quality_decision": quality.decision.value,
        "quality_reject_reasons": [reason.value for reason in quality.reject_reasons],
        "quality_review_reasons": [reason.value for reason in quality.review_reasons],
        "quality_metrics": dict(quality.metrics),
    }


def _call_ingest_text(
    runtime: object,
    *,
    title: str,
    text: str,
    source_path: str,
    mime_type: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    ingest = getattr(runtime, "ingest_text")
    try:
        result = ingest(title, text, source_path, mime_type, metadata)
    except TypeError as exc:
        # Backward compatibility for legacy four-argument runtimes. Only fall
        # back for signature mismatch; runtime TypeError inside its own logic is
        # still surfaced by the second call.
        if "positional" not in str(exc) and "argument" not in str(exc):
            raise
        result = ingest(title, text, source_path, mime_type)
    return dict(result or {"ok": True})
