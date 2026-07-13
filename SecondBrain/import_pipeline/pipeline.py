"""UnifiedImportPipeline: ein Pfad für lokale Dateien und Connector-Inhalte.

Stufen je Job: parsing -> classified -> chunked -> embedded -> indexed.
Parserfehler blockieren die Queue nicht (Partial Failure); fehlgeschlagene
Jobs werden mit Retry erneut versucht und landen nach max_attempts im
Dead Letter. OCR_REQUIRED wird als eigener Wartestatus abgebildet.
Jede Aktion erhält einen Audit-Eintrag (Observability).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from secondbrain.agent.review_service import UnifiedReviewInbox
from secondbrain.events.domain_events import sanitize_metadata
from secondbrain.import_pipeline.dedup import DuplicateDetector, content_hash_bytes, content_hash_text
from secondbrain.import_pipeline.models import ImportJob, ImportStatus, REVIEW_HOLD_STATUSES
from secondbrain.import_pipeline.store import ImportJobStore
from secondbrain.observability import ObservabilityService, new_correlation_id, new_sync_id
from secondbrain.observability.taxonomy import classify_error
from secondbrain.security_v107 import SECRET_PATTERNS

SCHEMA = "secondbrain.import_pipeline.v1"

Classifier = Callable[[str], dict[str, Any]]
Indexer = Callable[[str, dict[str, Any]], dict[str, Any]]
Chunker = Callable[[str], list[str]]


def default_classifier(text: str) -> dict[str, Any]:
    """Klassifikations-Engine (Regeln + PII); Fallback: Alt-Klassifikator."""
    try:
        from secondbrain.classification import classify_document
        return classify_document(text)
    except ImportError:
        from secondbrain.classifier import classify_text
        return {"document_type": classify_text(text), "tags": [], "confidence": 0.5,
                "needs_review": True, "sensitive": False}


def default_chunker(text: str, *, size: int = 1200, overlap: int = 150) -> list[str]:
    if not text.strip():
        return []
    chunks: list[str] = []
    step = max(size - overlap, 1)
    for start in range(0, len(text), step):
        chunk = text[start:start + size].strip()
        if chunk:
            chunks.append(chunk)
        if start + size >= len(text):
            break
    return chunks


class UnifiedImportPipeline:
    def __init__(
        self,
        project_root: str | Path = ".",
        *,
        parser_registry: Any | None = None,
        classifier: Classifier | None = None,
        chunker: Chunker | None = None,
        indexer: Indexer | None = None,
        review_inbox: UnifiedReviewInbox | None = None,
        classification_confidence_threshold: float = 0.6,
        pii_review_threshold: int = 3,
    ):
        self.project_root = Path(project_root)
        self.store = ImportJobStore(self.project_root)
        self.dedup = DuplicateDetector(self.project_root)
        self.observability = ObservabilityService(self.project_root)
        self._parser_registry = parser_registry
        self.classifier = classifier or default_classifier
        self.chunker = chunker or default_chunker
        self._indexer = indexer
        self.review_inbox = review_inbox or UnifiedReviewInbox(self.project_root)
        self.classification_confidence_threshold = min(1.0, max(0.0, float(classification_confidence_threshold)))
        self.pii_review_threshold = max(1, int(pii_review_threshold))

    # ---------------------------------------------------------- Abhängigkeiten
    @property
    def parser_registry(self) -> Any:
        if self._parser_registry is None:
            from secondbrain.document_understanding.parsers import default_parser_registry
            self._parser_registry = default_parser_registry()
        return self._parser_registry

    def _index(self, text: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Inkrementelles Indexieren: ein Dokument je Aufruf über die P1-Runtime."""
        if self._indexer is not None:
            return self._indexer(text, metadata)
        from secondbrain.p1_rag_runtime import P1RagRuntime
        runtime = P1RagRuntime(self.project_root)
        return runtime.ingest_text(
            text,
            source=metadata.get("source", "import"),
            title=metadata.get("title"),
            metadata=metadata,
        )

    # ------------------------------------------------------------------ Submit
    def submit_file(self, path: str | Path, *, connector: str = "",
                    sync_id: str = "", correlation_id: str = "") -> ImportJob:
        """Lokale Datei einreihen. Connector-Downloads nutzen denselben Aufruf."""
        file_path = Path(path)
        job = ImportJob(
            source_kind="connector" if connector else "local",
            source_ref=str(file_path),
            connector=connector,
            sync_id=sync_id or (new_sync_id() if connector else ""),
            correlation_id=correlation_id or new_correlation_id(),
        )
        try:
            digest = content_hash_bytes(file_path.read_bytes())
        except OSError as exc:
            return self._fail(job, exc, retryable=False)
        return self._register_submission(job, digest, title=file_path.name)

    def submit_text(self, text: str, *, source_ref: str, connector: str = "",
                    sync_id: str = "", correlation_id: str = "",
                    title: str = "") -> ImportJob:
        """Bereits extrahierter Connector-Inhalt — identischer Pfad ab Klassifikation."""
        job = ImportJob(
            source_kind="connector" if connector else "local",
            source_ref=source_ref,
            connector=connector,
            sync_id=sync_id or (new_sync_id() if connector else ""),
            correlation_id=correlation_id or new_correlation_id(),
        )
        job.lineage["inline_text"] = True
        job.lineage["text"] = text  # bis zur Verarbeitung; wird danach entfernt
        return self._register_submission(job, content_hash_text(text), title=title or source_ref)

    def _register_submission(self, job: ImportJob, digest: str, *, title: str) -> ImportJob:
        job.content_hash = digest
        job.lineage.update({
            "source_kind": job.source_kind,
            "source_ref": job.source_ref,
            "connector": job.connector,
            "sync_id": job.sync_id,
            "content_hash": digest,
            "title": title,
            "correlation_id": job.correlation_id,
        })
        first_job = self.dedup.known(digest)
        if first_job:
            job.duplicate_of = first_job
            job.transition(ImportStatus.DUPLICATE, f"Inhalt bereits importiert als {first_job}")
            self.store.upsert(job)
            self._audit(job, status="ok", action="import.duplicate")
            return job
        job.transition(ImportStatus.QUEUED, "eingereiht")
        self.store.upsert(job)
        self._audit(job, status="ok", action="import.queued")
        return job

    # ----------------------------------------------------------------- Verarbeiten
    def process(self, job_id: str) -> ImportJob:
        job = self.store.get(job_id)
        if job is None:
            raise KeyError(f"unbekannter ImportJob: {job_id}")
        if job.terminal or job.status in REVIEW_HOLD_STATUSES:
            return job
        job.attempts += 1
        try:
            text, title = self._stage_parsing(job)
            if job.status == ImportStatus.OCR_REQUIRED:
                self.store.upsert(job)
                self._audit(job, status="pending", action="import.ocr_required")
                return job
            classification = self._stage_classified(job, text)
            review = self._classification_review(job, text, classification)
            if review is not None and not self._review_was_approved(job, review[0]):
                return self._hold_for_review(
                    job,
                    category=review[0],
                    error_code=review[1],
                    sanitized_error=review[2],
                    retry_allowed=True,
                )
            chunks = self._stage_chunked(job, text)
            self._stage_embedded_indexed(job, text, title, chunks)
            self.dedup.register(job.content_hash, job.job_id)
            job.lineage.pop("text", None)
            self.store.upsert(job)
            self._audit(job, status="ok", action="import.indexed")
            return job
        except Exception as exc:  # Partial Failure: Fehler bleibt am Job, Queue läuft weiter
            return self._fail(job, exc)

    def process_batch(self, job_ids: list[str] | None = None) -> dict[str, Any]:
        """Verarbeitet alle offenen Jobs; Fehler einzelner Jobs stoppen den Lauf nicht."""
        pending = job_ids or [j.job_id for j in self.store.list(status=ImportStatus.QUEUED, limit=10_000)]
        results = {"processed": 0, "indexed": 0, "failed": 0, "dead_letter": 0,
                   "ocr_required": 0, "duplicate": 0, "review_required": 0,
                   "failed_reviewable": 0, "review_deferred": 0, "rejected": 0}
        for job_id in pending:
            job = self.process(job_id)
            results["processed"] += 1
            key = job.status if job.status in results else "failed"
            results[key] = results.get(key, 0) + 1
            if job.status == ImportStatus.FAILED_REVIEWABLE:
                results["failed"] += 1
        results["schema"] = SCHEMA
        return results

    def retry(self, job_id: str) -> ImportJob:
        """Manuelles Requeue aus failed/dead_letter/ocr_required."""
        job = self.store.get(job_id)
        if job is None:
            raise KeyError(f"unbekannter ImportJob: {job_id}")
        if job.status in REVIEW_HOLD_STATUSES:
            return job
        if job.status not in (ImportStatus.FAILED, ImportStatus.DEAD_LETTER, ImportStatus.OCR_REQUIRED):
            return job
        job.error = ""
        job.error_category = ""
        if job.status == ImportStatus.DEAD_LETTER:
            job.attempts = 0
        job.transition(ImportStatus.QUEUED, "manuell erneut eingereiht")
        self.store.upsert(job)
        self._audit(job, status="ok", action="import.requeued")
        return job

    # ------------------------------------------------------------------ Stufen
    def _stage_parsing(self, job: ImportJob) -> tuple[str, str]:
        job.transition(ImportStatus.PARSING)
        self.store.upsert(job)
        if job.lineage.get("inline_text"):
            job.parser = "inline_text"
            return job.lineage.get("text", ""), job.lineage.get("title", job.source_ref)
        parsed = self.parser_registry.parse(job.source_ref)
        metadata = getattr(parsed, "metadata", {})
        job.parser = (
            str(metadata.get("parser") or type(self.parser_registry).__name__)
            if isinstance(metadata, dict)
            else type(self.parser_registry).__name__
        )
        status = getattr(parsed, "status", None)
        status_value = getattr(status, "value", str(status))
        if status_value == "ocr_required":
            job.ocr_required = True
            job.transition(ImportStatus.OCR_REQUIRED, "Scan ohne Textebene; wartet auf OCR")
            return "", getattr(parsed, "title", job.source_ref)
        if status_value in ("failed", "unsupported") or not getattr(parsed, "text", ""):
            errors = ", ".join(getattr(parsed, "errors", []) or [status_value])
            raise ValueError(f"Parser: {errors}")
        return parsed.text, getattr(parsed, "title", job.source_ref)

    def _stage_classified(self, job: ImportJob, text: str) -> dict[str, Any]:
        result = self.classifier(text)
        job.document_type = str(result.get("document_type", ""))
        job.tags = list(result.get("tags", []))
        job.confidence = float(result.get("confidence", 0.0))
        job.transition(ImportStatus.CLASSIFIED, f"Typ={job.document_type}")
        self.store.upsert(job)
        self._record_classification(job, result)
        return result

    def _record_classification(self, job: ImportJob, result: dict[str, Any]) -> None:
        """Keep classification lineage; review routing uses the unified inbox."""
        try:
            from secondbrain.classification import TagHistory
        except ImportError:
            return
        try:
            TagHistory(self.project_root).record(
                self._safe_text(job.source_ref), new_type=job.document_type, new_tags=job.tags,
                source="suggestion", note=f"Import {job.job_id}")
            if result.get("sensitive"):
                self.observability.track_action(
                    "import", "import.sensitive_content", resource=self._safe_text(job.source_ref),
                    status="ok", correlation_id=job.correlation_id, job_id=job.job_id)
        except Exception:
            pass

    def _classification_review(
        self,
        job: ImportJob,
        text: str,
        result: dict[str, Any],
    ) -> tuple[str, str, str] | None:
        pii = result.get("pii") if isinstance(result.get("pii"), dict) else {}
        findings = pii.get("findings") if isinstance(pii.get("findings"), list) else []
        finding_types = {str(item.get("type") or "").lower() for item in findings if isinstance(item, dict)}
        pii_count = sum(int(item.get("count") or 0) for item in findings if isinstance(item, dict))
        markers = [str(item).lower() for item in pii.get("markers", [])]
        credential_types = {"api_key", "passwort_zuweisung", "password", "private_key", "credential"}
        credential_detected = bool(finding_types & credential_types) or any(pattern.search(text) for pattern in SECRET_PATTERNS)
        classification = str(result.get("classification") or job.document_type or "").lower()
        confidential = bool(markers) or classification in {"confidential", "vertraulich", "secret", "restricted"}
        explicit_sensitive = bool(result.get("contains_credentials") or result.get("credential_detected"))
        if credential_detected or explicit_sensitive:
            return "sensitive_document", "credentials_detected", "Sensitive credentials require manual review."
        if confidential or (bool(result.get("sensitive")) and not findings):
            return "sensitive_document", "confidential_classification", "Confidential content requires manual review."
        if pii_count >= self.pii_review_threshold:
            return "sensitive_document", "pii_threshold_exceeded", "PII threshold exceeded; manual review required."

        conflicting = bool(
            result.get("conflict")
            or result.get("conflicting_classifications")
            or result.get("classification_conflict")
        )
        missing_type = not job.document_type.strip()
        low_confidence = job.confidence < self.classification_confidence_threshold
        if conflicting:
            return "low_confidence_classification", "conflicting_classifications", "Conflicting classifications."
        if missing_type:
            return "low_confidence_classification", "missing_document_type", "Document type is missing."
        if low_confidence or bool(result.get("needs_review")):
            return "low_confidence_classification", "low_confidence", "Classification confidence is below threshold."
        return None

    def _hold_for_review(
        self,
        job: ImportJob,
        *,
        category: str,
        error_code: str,
        sanitized_error: str,
        retry_allowed: bool,
    ) -> ImportJob:
        safe_error = self._safe_text(sanitized_error)
        review = self._find_review(job.job_id, category)
        if review is None:
            review = self.review_inbox.create_review(
                category=category,
                title=f"Import review required: {category}",
                description=safe_error,
                source="import_pipeline",
                target=job.job_id,
                metadata={
                    "import_job_id": job.job_id,
                    "document_id": job.document_id,
                    "source": self._safe_text(job.source_ref),
                    "parser": job.parser,
                    "error_code": error_code,
                    "confidence": job.confidence,
                    "classification": job.document_type,
                    "sanitized_error": safe_error,
                    "retry_allowed": bool(retry_allowed),
                    "created_at": job.created_at,
                },
                workspace_id=str(job.lineage.get("workspace_id") or ""),
                actor="import_pipeline",
                correlation_id=job.correlation_id,
            )
        job.review_id = str(review.get("review_id") or "")
        job.review_category = category
        job.review_status = str(review.get("status") or "pending")
        job.retry_allowed = bool(retry_allowed)
        job.indexing_blocked = True
        if category == "sensitive_document":
            job.memory_forwarding_blocked = True
            job.connector_forwarding_blocked = True
        if category == "low_confidence_classification":
            job.classification_blocked = True
        hold_status = ImportStatus.FAILED_REVIEWABLE if category == "failed_import" else ImportStatus.REVIEW_REQUIRED
        job.transition(hold_status, safe_error)
        self.store.upsert(job)
        self._audit(job, status="pending", action=f"import.review_required.{category}")
        return job

    def approve_review(
        self,
        review_id: str,
        actor: str,
        note: str = "",
        *,
        classification: str = "",
    ) -> ImportJob:
        review, job = self._job_for_review(review_id)
        if str(review.get("status") or "pending") != "approved":
            self.review_inbox.approve(review_id, actor, self._safe_text(note))
        approved = list(job.lineage.get("approved_review_categories") or [])
        if job.review_category not in approved:
            approved.append(job.review_category)
        job.lineage["approved_review_categories"] = approved
        if classification:
            job.document_type = classification
        job.review_status = "approved"
        job.error = ""
        job.error_category = ""
        job.indexing_blocked = False
        job.classification_blocked = False
        job.memory_forwarding_blocked = False
        job.connector_forwarding_blocked = False
        job.transition(ImportStatus.QUEUED, "manual review approved")
        self.store.upsert(job)
        self._audit(job, status="ok", action="import.review_approved")
        return self.process(job.job_id)

    def reject_review(self, review_id: str, actor: str, note: str = "") -> ImportJob:
        review, job = self._job_for_review(review_id)
        if str(review.get("status") or "pending") != "rejected":
            self.review_inbox.reject(review_id, actor, self._safe_text(note))
        job.review_status = "rejected"
        job.retry_allowed = False
        job.indexing_blocked = True
        job.memory_forwarding_blocked = True
        job.connector_forwarding_blocked = True
        job.lineage.pop("text", None)
        job.transition(ImportStatus.REJECTED, "manual review rejected")
        self.store.upsert(job)
        self._audit(job, status="blocked", action="import.review_rejected")
        return job

    def defer_review(
        self,
        review_id: str,
        actor: str,
        *,
        until: str = "",
        note: str = "",
    ) -> ImportJob:
        review, job = self._job_for_review(review_id)
        if str(review.get("status") or "pending") != "deferred":
            self.review_inbox.defer(review_id, actor, until=until, note=self._safe_text(note))
        job.review_status = "deferred"
        job.indexing_blocked = True
        job.transition(ImportStatus.REVIEW_DEFERRED, "manual review deferred")
        self.store.upsert(job)
        self._audit(job, status="pending", action="import.review_deferred")
        return job

    def _job_for_review(self, review_id: str) -> tuple[dict[str, Any], ImportJob]:
        review = self.review_inbox.reviews.get(review_id)
        if review is None:
            raise KeyError(f"unknown_import_review:{review_id}")
        metadata = review.get("metadata") if isinstance(review.get("metadata"), dict) else {}
        job_id = str(metadata.get("import_job_id") or "")
        job = self.store.get(job_id)
        if job is None:
            raise KeyError(f"import_job_for_review_not_found:{review_id}")
        return review, job

    def _find_review(self, job_id: str, category: str) -> dict[str, Any] | None:
        for review in self.review_inbox.reviews.list(category=category):
            metadata = review.get("metadata") if isinstance(review.get("metadata"), dict) else {}
            if metadata.get("import_job_id") == job_id:
                return review
        return None

    @staticmethod
    def _review_was_approved(job: ImportJob, category: str) -> bool:
        return category in set(job.lineage.get("approved_review_categories") or [])

    def _stage_chunked(self, job: ImportJob, text: str) -> list[str]:
        chunks = self.chunker(text)
        if not chunks:
            raise ValueError("Chunker lieferte keine Chunks (leerer Inhalt)")
        job.chunk_count = len(chunks)
        job.transition(ImportStatus.CHUNKED, f"{len(chunks)} Chunks")
        self.store.upsert(job)
        return chunks

    def _stage_embedded_indexed(self, job: ImportJob, text: str, title: str,
                                chunks: list[str]) -> None:
        metadata = {
            "source": job.lineage.get("connector") or "local_import",
            "title": title,
            "job_id": job.job_id,
            "content_hash": job.content_hash,
            "document_type": job.document_type,
            "tags": job.tags,
            "lineage": {k: v for k, v in job.lineage.items() if k != "text"},
        }
        result = self._index(text, metadata)
        if isinstance(result, dict) and result.get("ok") is False:
            raise RuntimeError(f"Indexierung fehlgeschlagen: {result.get('error', result)}")
        job.transition(ImportStatus.EMBEDDED, "Embeddings erzeugt")
        job.transition(ImportStatus.INDEXED, "inkrementell in den RAG-Index übernommen")

    # ------------------------------------------------------------------ Fehler
    def _fail(self, job: ImportJob, exc: BaseException, *, retryable: bool = True) -> ImportJob:
        failed_stage = job.status
        job.error = self._safe_text(str(exc))[:500]
        job.error_category = self._error_code(failed_stage, job.error) or classify_error(RuntimeError(job.error))
        retry_allowed = (
            bool(retryable)
            and job.attempts < job.max_attempts
            and job.error_category not in {"unsupported_format", "corrupted_file"}
        )
        return self._hold_for_review(
            job,
            category="failed_import",
            error_code=job.error_category,
            sanitized_error=job.error,
            retry_allowed=retry_allowed,
        )

    def _audit(self, job: ImportJob, *, status: str, action: str,
               error: BaseException | None = None) -> None:
        try:
            safe_error = RuntimeError(self._safe_text(str(error))) if error is not None else None
            self.observability.track_action(
                "import", action, resource=self._safe_text(job.source_ref), status=status, error=safe_error,
                correlation_id=job.correlation_id, job_id=job.job_id,
                sync_id=job.sync_id or "")
        except Exception:
            pass

    @staticmethod
    def _safe_text(value: str) -> str:
        return str(sanitize_metadata({"message": value}).get("message") or "")[:500]

    @staticmethod
    def _error_code(stage: str, message: str) -> str:
        value = f"{stage} {message}".lower()
        if "unsupported" in value or "nicht unterst" in value:
            return "unsupported_format"
        if any(token in value for token in ("corrupt", "beschäd", "beschaed", "invalid archive")):
            return "corrupted_file"
        if "ocr" in value:
            return "ocr_failed"
        if "embedding" in value or "vector" in value:
            return "embedding_failed"
        if "index" in value or stage in {ImportStatus.CHUNKED, ImportStatus.EMBEDDED}:
            return "indexing_failed"
        if stage == ImportStatus.PARSING or "parser" in value:
            return "parser_failed"
        if stage == ImportStatus.CLASSIFIED:
            return "classification_failed"
        return "import_failed"
