from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from hashlib import sha256
from typing import Any
from uuid import uuid4


class MemoryScope(StrEnum):
    SESSION = "session"
    WORKSPACE = "workspace"
    USER = "user"


class MemoryVisibility(StrEnum):
    PRIVATE = "private"
    WORKSPACE = "workspace"
    PUBLIC = "public"


class MemoryError(ValueError):
    pass


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    text: str
    scope: MemoryScope = MemoryScope.SESSION
    visibility: MemoryVisibility = MemoryVisibility.PRIVATE
    workspace_id: str | None = None
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def fingerprint(self) -> str:
        raw = "|".join([self.scope.value, self.workspace_id or "", self.text.strip().lower()])
        return sha256(raw.encode("utf-8")).hexdigest()


def create_memory_record(
    text: str,
    *,
    scope: MemoryScope = MemoryScope.SESSION,
    visibility: MemoryVisibility = MemoryVisibility.PRIVATE,
    workspace_id: str | None = None,
    tags: list[str] | tuple[str, ...] | None = None,
    metadata: dict[str, Any] | None = None,
) -> MemoryRecord:
    normalized = (text or "").strip()
    if not normalized:
        raise MemoryError("memory_text_required")
    if scope == MemoryScope.WORKSPACE and not workspace_id:
        raise MemoryError("workspace_id_required")
    return MemoryRecord(
        memory_id=str(uuid4()),
        text=normalized,
        scope=scope,
        visibility=visibility,
        workspace_id=workspace_id,
        tags=tuple(tags or ()),
        metadata=metadata or {},
    )


class InMemoryMemoryStore:
    def __init__(
        self,
        *,
        privacy_mode: str = "off",
        confidence_threshold: float = 0.6,
        enforce_governance: bool = True,
    ) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._fingerprints: set[str] = set()
        self._privacy_mode = str(privacy_mode or "off").strip().lower()
        self._confidence_threshold = max(0.0, min(1.0, float(confidence_threshold)))
        self._enforce_governance = bool(enforce_governance)
        self._governance_token: object | None = None

    def bind_governance(
        self,
        token: object,
        *,
        privacy_mode: str,
        confidence_threshold: float,
    ) -> None:
        """Bind internal governed writes while keeping direct calls policy-checked."""

        if self._governance_token is not None and self._governance_token is not token:
            raise MemoryError("memory_store_governance_already_bound")
        self._governance_token = token
        self._enforce_governance = True
        self._privacy_mode = str(privacy_mode or "off").strip().lower()
        self._confidence_threshold = max(0.0, min(1.0, float(confidence_threshold)))

    def add(self, record: MemoryRecord, *, governance_token: object | None = None) -> MemoryRecord:
        if self._enforce_governance and (
            governance_token is not self._governance_token or self._governance_token is None
        ):
            self._enforce_direct_write_policy(record)
        if record.fingerprint in self._fingerprints:
            raise MemoryError("duplicate_memory")
        self._records[record.memory_id] = record
        self._fingerprints.add(record.fingerprint)
        return record

    def _enforce_direct_write_policy(self, record: MemoryRecord) -> None:
        """Defence in depth for callers attempting to bypass MemoryService."""

        from .memory_classification import ClassificationPolicy
        from .memory_extractor import detect_memory_secret
        from .privacy import PrivacyDecision, PrivacyGuard, PrivacyMode

        metadata = dict(record.metadata or {})
        tags = {str(tag).strip().lower() for tag in record.tags}
        if self._privacy_mode != PrivacyMode.OFF.value:
            raise MemoryError("memory_write_blocked:privacy_mode_active")
        if bool(metadata.get("no_memory")) or "no_memory" in tags:
            raise MemoryError("memory_write_blocked:no_memory_flag")
        if _contains_secret(metadata):
            raise MemoryError("memory_write_blocked:secret_metadata")
        privacy = PrivacyGuard(PrivacyMode.OFF)
        secret = privacy.inspect_memory_write(record.text)
        if detect_memory_secret(record.text) or (
            secret.decision != PrivacyDecision.ALLOW and secret.reason == "secret_redacted"
        ):
            raise MemoryError("memory_write_blocked:secret")

        classification = ClassificationPolicy(privacy).classify(
            record.text,
            metadata=metadata,
            source_id=str(metadata.get("source_id") or ""),
        )
        if classification.is_blocking:
            raise MemoryError("memory_write_blocked:credential")
        if classification.requires_review:
            raise MemoryError(f"memory_review_required:{classification.classification.value}")
        confidence = metadata.get("confidence")
        if confidence is not None:
            try:
                if float(confidence) < self._confidence_threshold:
                    raise MemoryError("memory_review_required:low_confidence")
            except (TypeError, ValueError) as exc:
                raise MemoryError("memory_review_required:invalid_confidence") from exc
        if metadata.get("source_trusted") is False:
            raise MemoryError("memory_review_required:untrusted_source")
        if bool(metadata.get("contradicts")):
            raise MemoryError("memory_review_required:contradicting_fact")
        if bool(metadata.get("unsupported_preference")) or (
            "preference" in tags and not metadata.get("evidence")
        ):
            raise MemoryError("memory_review_required:unsupported_preference")

    def list(self, *, workspace_id: str | None = None, scope: MemoryScope | None = None) -> list[MemoryRecord]:
        records = list(self._records.values())
        if workspace_id is not None:
            records = [record for record in records if record.workspace_id == workspace_id]
        if scope is not None:
            records = [record for record in records if record.scope == scope]
        return sorted(records, key=lambda record: record.created_at)

    def search(self, query: str, *, workspace_id: str | None = None, limit: int = 10) -> list[MemoryRecord]:
        normalized = (query or "").strip().lower()
        if not normalized:
            return []
        matches = [record for record in self.list(workspace_id=workspace_id) if normalized in record.text.lower()]
        return matches[: max(0, limit)]


def _contains_secret(value: Any, *, key: str = "") -> bool:
    normalized_key = "".join(character for character in key.lower() if character.isalnum())
    sensitive_keys = {
        "apikey", "authorization", "clientsecret", "credential", "credentials",
        "password", "passwd", "privatekey", "secret", "token", "accesstoken", "authtoken",
    }
    if normalized_key in sensitive_keys and value not in (None, "", "***", "[REDACTED_SECRET]"):
        return True
    if isinstance(value, dict):
        return any(_contains_secret(item, key=str(item_key)) for item_key, item in value.items())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_secret(item) for item in value)
    if isinstance(value, str):
        from .memory_extractor import detect_memory_secret
        from .privacy import PrivacyDecision, PrivacyGuard, PrivacyMode

        result = PrivacyGuard(PrivacyMode.OFF).inspect_memory_write(value)
        return detect_memory_secret(value) or (
            result.decision != PrivacyDecision.ALLOW and result.reason == "secret_redacted"
        )
    return False
