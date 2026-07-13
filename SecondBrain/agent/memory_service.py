"""Governed memory service - the only sanctioned path into long-term memory.

Every candidate produced by :class:`~secondbrain.agent.memory_extractor.MemoryExtractor`
passes through :meth:`GovernedMemoryService.submit`, which decides one of:

* **BLOCKED**  - hard rejected, never stored (secrets, credentials, active
  privacy mode, explicit ``no_memory``). Full secret content is never persisted,
  not in the candidate registry and not in the audit log.
* **REVIEW**   - routed to the human review inbox; the candidate is persisted
  but *no* memory is written until an approval decision arrives.
* **STORED**   - safe, confident, supported content written straight to memory.

A write for a review-gated candidate happens exactly once, and only after
:meth:`apply_memory_decision` is invoked with ``approved`` - normally by the
review inbox as a side effect of an operator approving the item. Repeated
approvals or resubmissions are absorbed by the deduplication guard.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from .memory import (
    InMemoryMemoryStore,
    MemoryError,
    MemoryRecord,
    MemoryScope,
    MemoryVisibility,
    create_memory_record,
)
from .memory_classification import ClassificationPolicy, DataClassification
from .memory_extractor import MemoryCandidate, detect_memory_secret, redact_memory_secrets
from .privacy import PrivacyDecision, PrivacyGuard, PrivacyMode

__all__ = [
    "GovernanceDecision",
    "GovernanceOutcome",
    "MemoryGovernanceAudit",
    "GovernedMemoryService",
    "DEFAULT_CONFIDENCE_THRESHOLD",
]

AUDIT_SCHEMA = "secondbrain.agent.memory_governance_audit.v1"
DEFAULT_CONFIDENCE_THRESHOLD = 0.6

# Review categories reused from the native review queue vocabulary.
CATEGORY_SENSITIVE = "sensitive_document"
CATEGORY_LOW_CONFIDENCE = "low_confidence_classification"
CATEGORY_RISKY_ACTION = "risky_agent_action"

_SECRET_SWEEP = PrivacyGuard(PrivacyMode.OFF)


class GovernanceDecision(StrEnum):
    STORED = "stored"
    REVIEW = "review"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    DISCARDED = "discarded"
    DUPLICATE = "duplicate"


@dataclass(frozen=True)
class GovernanceOutcome:
    decision: GovernanceDecision
    candidate_id: str
    reason: str = ""
    classification: str = ""
    review_id: str = ""
    review_category: str = ""
    memory_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "candidate_id": self.candidate_id,
            "reason": self.reason,
            "classification": self.classification,
            "review_id": self.review_id,
            "review_category": self.review_category,
            "memory_id": self.memory_id,
        }


class MemoryGovernanceAudit:
    """Append-only audit of governance decisions. Never records raw content."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self._records: list[dict[str, Any]] = []
        self.path: Path | None = None
        if project_root is not None:
            self.path = Path(project_root).resolve() / "runtime" / "native" / "memory_governance_audit.jsonl"

    def write(self, event: Mapping[str, Any]) -> dict[str, Any]:
        record = {"schema": AUDIT_SCHEMA, "timestamp": _utc_now(), **dict(event)}
        record = _redact_secrets(record)
        self._records.append(record)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def records(self) -> list[dict[str, Any]]:
        return list(self._records)


@dataclass
class _CandidateEntry:
    candidate: MemoryCandidate
    status: str  # pending | approved | rejected | deferred
    review_id: str = ""
    review_category: str = ""
    memory_id: str = ""


class GovernedMemoryService:
    def __init__(
        self,
        *,
        store: InMemoryMemoryStore | None = None,
        inbox: Any | None = None,
        privacy_mode: PrivacyMode = PrivacyMode.OFF,
        classifier: ClassificationPolicy | None = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        project_root: str | Path | None = None,
        audit: MemoryGovernanceAudit | None = None,
    ) -> None:
        self.store = store or InMemoryMemoryStore()
        self.inbox = inbox
        self.privacy = PrivacyGuard(privacy_mode)
        self.classifier = classifier or ClassificationPolicy()
        self.confidence_threshold = max(0.0, min(1.0, float(confidence_threshold)))
        self.audit = audit or MemoryGovernanceAudit(project_root)
        self._candidates: dict[str, _CandidateEntry] = {}
        self._candidate_statuses: dict[str, str] = {}
        self._committed_dedup_keys: set[str] = set()
        self._committed_candidate_ids: set[str] = set()
        self._store_governance_token = object()
        self.store.bind_governance(
            self._store_governance_token,
            privacy_mode=self.privacy.mode.value,
            confidence_threshold=self.confidence_threshold,
        )
        # Register with the inbox so decisions route back here.
        if inbox is not None:
            setattr(inbox, "memory_governance", self)

    # -- Ingestion --------------------------------------------------------

    def submit(self, candidate: MemoryCandidate) -> GovernanceOutcome:
        block_reason = self._blocking_reason(candidate)
        if block_reason is not None:
            return self._blocked(candidate, block_reason)

        review_reason = self._review_reason(candidate)
        if review_reason is not None:
            return self._route_to_review(candidate, review_reason)

        return self._store_direct(candidate, reason="auto_stored_non_sensitive")

    # -- Decisions (invoked by the review inbox or directly) --------------

    def apply_memory_decision(
        self,
        candidate_id: str,
        status: str,
        *,
        actor: str = "system",
    ) -> GovernanceOutcome:
        entry = self._candidates.get(candidate_id)
        if entry is None:
            raise KeyError(f"unknown_memory_candidate:{candidate_id}")
        status = status.strip().lower()
        self._require_persisted_decision(entry, status)
        if status == "approved":
            return self._commit(entry, actor=actor)
        if status == "rejected":
            self._set_status(entry, "rejected")
            self.audit.write(
                {
                    "decision": GovernanceDecision.DISCARDED.value,
                    "actor": actor,
                    "reason": "review_rejected",
                    **entry.candidate.sanitized_dict(),
                    "review_id": entry.review_id,
                    "review_category": entry.review_category,
                }
            )
            return GovernanceOutcome(
                decision=GovernanceDecision.DISCARDED,
                candidate_id=candidate_id,
                reason="review_rejected",
                classification=entry.candidate.classification.value,
                review_id=entry.review_id,
                review_category=entry.review_category,
            )
        if status == "deferred":
            self._set_status(entry, "deferred")
            self.audit.write(
                {
                    "decision": GovernanceDecision.DEFERRED.value,
                    "actor": actor,
                    "reason": "review_deferred",
                    **entry.candidate.sanitized_dict(),
                    "review_id": entry.review_id,
                    "review_category": entry.review_category,
                }
            )
            return GovernanceOutcome(
                decision=GovernanceDecision.DEFERRED,
                candidate_id=candidate_id,
                reason="review_deferred",
                classification=entry.candidate.classification.value,
                review_id=entry.review_id,
                review_category=entry.review_category,
            )
        raise ValueError(f"unsupported_memory_decision:{status}")

    # -- Introspection ----------------------------------------------------

    def get_candidate(self, candidate_id: str) -> MemoryCandidate | None:
        entry = self._candidates.get(candidate_id)
        return entry.candidate if entry is not None else None

    def candidate_status(self, candidate_id: str) -> str | None:
        entry = self._candidates.get(candidate_id)
        return entry.status if entry is not None else self._candidate_statuses.get(candidate_id)

    def list_candidates(self, *, status: str | None = None) -> list[MemoryCandidate]:
        entries = self._candidates.values()
        if status is not None:
            entries = [entry for entry in entries if entry.status == status]
        return [entry.candidate for entry in entries]

    # -- Internal ---------------------------------------------------------

    def _blocking_reason(self, candidate: MemoryCandidate) -> str | None:
        if candidate.no_memory:
            return "no_memory_flag"
        if self.privacy.mode != PrivacyMode.OFF:
            return "privacy_mode_active"
        if candidate.status == "blocked" or detect_memory_secret(candidate.content):
            return "secret_blocked"
        if candidate.classification == DataClassification.CREDENTIAL:
            return "credential_blocked"
        # Defence in depth: re-scan raw content for secrets regardless of class.
        result = self.privacy.inspect_memory_write(candidate.content)
        if result.decision != PrivacyDecision.ALLOW and result.reason == "secret_redacted":
            return "secret_blocked"
        return None

    def _review_reason(self, candidate: MemoryCandidate) -> str | None:
        if bool(candidate.metadata.get("external_consequences")):
            return "external_consequences"
        if candidate.classification in {
            DataClassification.SENSITIVE_PERSONAL,
            DataClassification.HEALTH,
            DataClassification.FINANCIAL,
            DataClassification.PRIVATE_COMMUNICATION,
        }:
            return f"sensitive_classification:{candidate.classification.value}"
        if candidate.confidence < self.confidence_threshold:
            return "low_confidence"
        if candidate.contradicts:
            return "contradicts_known_fact"
        if candidate.unsupported_preference:
            return "unsupported_preference"
        if not candidate.source_trusted:
            return "untrusted_source"
        return None

    def _review_category(self, candidate: MemoryCandidate, reason: str) -> str:
        if reason == "external_consequences":
            return CATEGORY_RISKY_ACTION
        if candidate.classification in {
            DataClassification.SENSITIVE_PERSONAL,
            DataClassification.HEALTH,
            DataClassification.FINANCIAL,
            DataClassification.PRIVATE_COMMUNICATION,
        }:
            return CATEGORY_SENSITIVE
        return CATEGORY_LOW_CONFIDENCE

    def _blocked(self, candidate: MemoryCandidate, reason: str) -> GovernanceOutcome:
        # Do not persist the candidate: blocked content (esp. secrets) must not
        # linger in the registry. Only sanitized metadata reaches the audit.
        self._candidate_statuses[candidate.candidate_id] = "blocked"
        self.audit.write(
            {
                "decision": GovernanceDecision.BLOCKED.value,
                "reason": reason,
                **candidate.sanitized_dict(),
                "status": "blocked",
            }
        )
        return GovernanceOutcome(
            decision=GovernanceDecision.BLOCKED,
            candidate_id=candidate.candidate_id,
            reason=reason,
            classification=candidate.classification.value,
        )

    def _route_to_review(self, candidate: MemoryCandidate, reason: str) -> GovernanceOutcome:
        category = self._review_category(candidate, reason)
        review_id = ""
        safe_candidate = candidate.sanitized_dict()
        if self.inbox is not None:
            review = self.inbox.create_review(
                category=category,
                title=f"Memory review: {candidate.memory_type}",
                description=candidate.sanitized_content_preview,
                source=str(safe_candidate["source_id"]),
                # Unique per candidate so the queue's content-hashed review id
                # never collides for two same-second same-title candidates.
                target=candidate.candidate_id,
                workspace_id=candidate.workspace_id,
                metadata={
                    "governance": "memory",
                    "candidate_id": candidate.candidate_id,
                    "workspace_id": candidate.workspace_id,
                    "classification": candidate.classification.value,
                    "confidence": candidate.confidence,
                    "review_reason": reason,
                },
            )
            review_id = str(review.get("review_id") or "")
        self._candidates[candidate.candidate_id] = _CandidateEntry(
            candidate=replace(candidate, status="pending"),
            status="pending",
            review_id=review_id,
            review_category=category,
        )
        self._candidate_statuses[candidate.candidate_id] = "pending"
        self.audit.write(
            {
                "decision": GovernanceDecision.REVIEW.value,
                "reason": reason,
                "review_id": review_id,
                "review_category": category,
                **candidate.sanitized_dict(),
            }
        )
        return GovernanceOutcome(
            decision=GovernanceDecision.REVIEW,
            candidate_id=candidate.candidate_id,
            reason=reason,
            classification=candidate.classification.value,
            review_id=review_id,
            review_category=category,
        )

    def _store_direct(self, candidate: MemoryCandidate, *, reason: str) -> GovernanceOutcome:
        if candidate.deduplication_key in self._committed_dedup_keys:
            return GovernanceOutcome(
                decision=GovernanceDecision.DUPLICATE,
                candidate_id=candidate.candidate_id,
                reason="duplicate_deduplication_key",
                classification=candidate.classification.value,
            )
        self._candidates[candidate.candidate_id] = _CandidateEntry(
            candidate=replace(candidate, status="pending"),
            status="pending",
        )
        self._candidate_statuses[candidate.candidate_id] = "pending"
        return self._commit(self._candidates[candidate.candidate_id], actor="system", auto=True, reason=reason)

    def _commit(
        self,
        entry: _CandidateEntry,
        *,
        actor: str,
        auto: bool = False,
        reason: str = "review_approved",
    ) -> GovernanceOutcome:
        candidate = entry.candidate
        # Idempotency: never write the same candidate or dedup key twice.
        if candidate.candidate_id in self._committed_candidate_ids or candidate.deduplication_key in self._committed_dedup_keys:
            self._set_status(entry, "stored")
            return GovernanceOutcome(
                decision=GovernanceDecision.DUPLICATE,
                candidate_id=candidate.candidate_id,
                reason="already_committed",
                classification=candidate.classification.value,
                review_id=entry.review_id,
                review_category=entry.review_category,
                memory_id=entry.memory_id,
            )
        self._set_status(entry, "approved")
        memory_id = self._write_memory(candidate)
        self._set_status(entry, "stored")
        candidate = entry.candidate
        entry.memory_id = memory_id
        self._committed_candidate_ids.add(candidate.candidate_id)
        self._committed_dedup_keys.add(candidate.deduplication_key)
        self.audit.write(
            {
                "decision": GovernanceDecision.STORED.value,
                "actor": actor,
                "reason": reason,
                "auto_stored": auto,
                "memory_id": memory_id,
                "review_id": entry.review_id,
                "review_category": entry.review_category,
                **candidate.sanitized_dict(),
            }
        )
        return GovernanceOutcome(
            decision=GovernanceDecision.STORED,
            candidate_id=candidate.candidate_id,
            reason=reason,
            classification=candidate.classification.value,
            review_id=entry.review_id,
            review_category=entry.review_category,
            memory_id=memory_id,
        )

    def _write_memory(self, candidate: MemoryCandidate) -> str:
        scope = MemoryScope.WORKSPACE if candidate.workspace_id else MemoryScope.SESSION
        tags = tuple({tag for tag in (candidate.memory_type, candidate.classification.value) if tag})
        safe_candidate = candidate.sanitized_dict()
        record = create_memory_record(
            candidate.content,
            scope=scope,
            visibility=MemoryVisibility.PRIVATE,
            workspace_id=candidate.workspace_id or None,
            tags=tags,
            metadata={
                "candidate_id": candidate.candidate_id,
                "source_id": safe_candidate["source_id"],
                "classification": candidate.classification.value,
                "deduplication_key": candidate.deduplication_key,
                "retention_policy": candidate.retention_policy,
                "expires_at": candidate.expires_at,
                "expiration": candidate.expires_at,
                "evidence": safe_candidate["evidence"],
                "confidence": candidate.confidence,
            },
        )
        try:
            stored = self.store.add(record, governance_token=self._store_governance_token)
        except MemoryError:
            # Underlying store already holds an identical fingerprint.
            return record.memory_id
        return stored.memory_id

    def _require_persisted_decision(self, entry: _CandidateEntry, status: str) -> None:
        if status not in {"approved", "rejected", "deferred"}:
            return
        if self.inbox is None or not entry.review_id:
            raise PermissionError("memory_review_decision_not_persisted")
        item = self.inbox.get(entry.review_id)
        if item is None or str(item.get("status") or "") != status:
            raise PermissionError("memory_review_decision_not_persisted")

    def _set_status(self, entry: _CandidateEntry, status: str) -> None:
        entry.status = status
        entry.candidate = replace(entry.candidate, status=status)
        self._candidate_statuses[entry.candidate.candidate_id] = status


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _redact_secrets(record: Mapping[str, Any]) -> dict[str, Any]:
    """Final safety sweep: redact any secret-looking substring anywhere."""

    def _scrub(value: Any) -> Any:
        if isinstance(value, str):
            if detect_memory_secret(value):
                return redact_memory_secrets(value)
            result = _SECRET_SWEEP.inspect_memory_write(value)
            return result.redacted_text if result.reason == "secret_redacted" else value
        if isinstance(value, Mapping):
            return {key: _scrub(item) for key, item in value.items()}
        if isinstance(value, list):
            return [_scrub(item) for item in value]
        if isinstance(value, tuple):
            return tuple(_scrub(item) for item in value)
        return value

    return {key: _scrub(item) for key, item in record.items()}
