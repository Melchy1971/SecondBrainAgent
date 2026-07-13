"""Quality evaluation for imported documents using existing repository signals."""
from __future__ import annotations

import json
import hashlib
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from secondbrain.advanced_rag_v109 import quality_score as chunk_quality_score, trust_score
from secondbrain.classifier import classify_text
from secondbrain.security_v107 import PII_PATTERNS, SECRET_PATTERNS

TOKEN = re.compile(r"[\wäöüÄÖÜß]{2,}", re.UNICODE)
LANGUAGE_WORDS = {
    "de": {"der", "die", "das", "und", "ist", "für", "mit", "nicht", "eine", "von"},
    "en": {"the", "and", "is", "for", "with", "not", "this", "from", "that", "are"},
    "fr": {"le", "la", "les", "et", "est", "pour", "avec", "une", "des", "pas"},
    "es": {"el", "la", "los", "y", "es", "para", "con", "una", "de", "que"},
}


def detect_language(text: str) -> tuple[str, float]:
    words = [word.lower() for word in TOKEN.findall(text[:100_000])]
    if not words:
        return "unknown", 0.0
    counts = {language: sum(word in markers for word in words) for language, markers in LANGUAGE_WORDS.items()}
    language, hits = max(counts.items(), key=lambda item: item[1])
    if hits == 0:
        return "unknown", 0.25
    total = sum(counts.values()) or 1
    return language, round(min(0.99, 0.5 + 0.5 * hits / total), 3)


def _tokens(text: str) -> set[str]:
    return {word.lower() for word in TOKEN.findall(text[:250_000])}


def _signature(text: str) -> list[str]:
    hashes = {hashlib.sha256(word.encode("utf-8")).hexdigest()[:16] for word in _tokens(text)}
    return sorted(hashes)[:256]


def _similarity(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(1, len(a | b))


class ImportQualityEvaluator:
    """Writes quality results into existing document metadata JSON."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def evaluate(self, document_ids: list[str]) -> list[dict[str, Any]]:
        if not document_ids:
            return []
        reports = []
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            for document_id in document_ids:
                report = self._evaluate_one(connection, document_id)
                if report:
                    row = connection.execute("SELECT metadata_json FROM documents WHERE id=?", (document_id,)).fetchone()
                    metadata = json.loads(row[0] or "{}")
                    metadata["knowledge_quality_score"] = report["knowledge_quality_score"]
                    metadata["knowledge_quality"] = report
                    connection.execute("UPDATE documents SET metadata_json=? WHERE id=?",
                                       (json.dumps(metadata, ensure_ascii=False, sort_keys=True), document_id))
                    reports.append(report)
        return reports

    def _evaluate_one(self, connection: sqlite3.Connection, document_id: str) -> dict[str, Any] | None:
        document = connection.execute("SELECT id,source,title,content_hash,metadata_json FROM documents WHERE id=?", (document_id,)).fetchone()
        if document is None:
            return None
        metadata = json.loads(document["metadata_json"] or "{}")
        chunks = connection.execute("SELECT id,text,token_count FROM chunks WHERE document_id=? ORDER BY ordinal", (document_id,)).fetchall()
        text = "\n\n".join(str(row["text"]) for row in chunks)
        embeddings = connection.execute("SELECT dimensions,vector_json FROM chunk_embeddings WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id=?)", (document_id,)).fetchall()

        language, language_confidence = detect_language(text)
        pii_count = sum(len(pattern.findall(text)) for pattern in PII_PATTERNS)
        secret_count = sum(len(pattern.findall(text)) for pattern in SECRET_PATTERNS)
        classification = classify_text(text, str(document["source"]))
        chunk_scores = [chunk_quality_score(str(row["text"])) for row in chunks]
        chunk_quality = sum(chunk_scores) / max(1, len(chunk_scores))
        valid_vectors = 0
        for row in embeddings:
            try:
                vector = [float(value) for value in json.loads(row["vector_json"])]
                valid_vectors += int(bool(vector) and int(row["dimensions"]) == len(vector) and all(math.isfinite(value) for value in vector) and any(value != 0 for value in vector))
            except Exception:
                continue
        embedding_quality = valid_vectors / max(1, len(chunks))

        ocr_status = str(metadata.get("ocr_status") or "not_required")
        ocr_quality = {"completed": 0.9, "not_required": 1.0, "required": 0.15, "failed": 0.0}.get(ocr_status, 0.6)
        parse_status = str((metadata.get("document") or {}).get("parse_status") or "parsed")
        parser_quality = {"parsed": 1.0, "empty": 0.25, "ocr_required": 0.35, "unsupported": 0.0, "failed": 0.0}.get(parse_status, 0.7)
        source = metadata.get("source") or {}
        source_path = str(source.get("file") if isinstance(source, dict) else source)
        source_trust = trust_score(source_path or str(document["source"]))

        exact = connection.execute("SELECT id FROM documents WHERE content_hash=? AND id<>? LIMIT 1", (document["content_hash"], document_id)).fetchone()
        signature = _signature(text)
        near_id, near_score = "", 0.0
        candidates = connection.execute("SELECT id,metadata_json FROM documents WHERE id<>? AND json_extract(metadata_json,'$.knowledge_quality.token_signature') IS NOT NULL LIMIT 1000", (document_id,)).fetchall()
        for candidate in candidates:
            candidate_quality = json.loads(candidate["metadata_json"] or "{}").get("knowledge_quality") or {}
            similarity = _similarity(set(signature), set(candidate_quality.get("token_signature") or []))
            if similarity > near_score:
                near_id, near_score = str(candidate["id"]), similarity
        is_near = near_score >= 0.82

        length_quality = min(1.0, len(text.strip()) / 800.0)
        security_quality = max(0.0, 1.0 - min(1.0, secret_count * 0.7 + pii_count * 0.12))
        duplicate_quality = 0.0 if exact else (max(0.2, 1.0 - near_score) if is_near else 1.0)
        confidence = round((language_confidence + chunk_quality + embedding_quality + parser_quality + ocr_quality) / 5, 3)
        score = round(100 * (0.16 * length_quality + 0.15 * chunk_quality + 0.16 * embedding_quality +
                             0.12 * parser_quality + 0.08 * ocr_quality + 0.12 * source_trust +
                             0.11 * security_quality + 0.10 * duplicate_quality))
        score = max(0, min(100, score))
        warnings = []
        if exact: warnings.append("duplicate_detected")
        if is_near: warnings.append("near_duplicate_detected")
        if pii_count: warnings.append("pii_detected")
        if secret_count: warnings.append("secret_detected")
        if chunk_quality < 0.4: warnings.append("low_chunk_quality")
        if embedding_quality < 0.8: warnings.append("low_embedding_quality")
        if ocr_quality < 0.5: warnings.append("low_ocr_quality")
        if parser_quality < 0.5: warnings.append("low_parser_quality")
        if score < 50: warnings.append("low_knowledge_quality")
        return {"knowledge_quality_score": score, "confidence_score": confidence, "language": language,
                "language_confidence": language_confidence, "classification": classification,
                "pii_detected": bool(pii_count), "pii_count": pii_count,
                "secret_detected": bool(secret_count), "secret_count": secret_count,
                "duplicate_detected": bool(exact), "duplicate_document_id": str(exact[0]) if exact else "",
                "near_duplicate_detected": is_near, "near_duplicate_document_id": near_id if is_near else "",
                "near_duplicate_similarity": round(near_score, 4), "chunk_quality": round(chunk_quality, 4),
                "embedding_quality": round(embedding_quality, 4), "ocr_quality": ocr_quality,
                "parser_quality": parser_quality, "source_trust": source_trust, "token_signature": signature,
                "warnings": warnings}


class ImportQualityDashboard:
    """Dashboard projections over documents and existing delta audit entries."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def snapshot(self) -> dict[str, Any]:
        documents, warnings, near = self._documents()
        scores = [row["score"] for row in documents]
        classes = Counter(row["classification"] for row in documents)
        languages = Counter(row["language"] for row in documents)
        return {"ok": True, "documents": len(documents), "scored": len(scores),
                "average_score": round(sum(scores) / max(1, len(scores)), 2),
                "low_quality": sum(score < 50 for score in scores), "warnings": len(warnings),
                "classifications": dict(classes), "languages": dict(languages)}

    def warnings(self) -> list[dict[str, Any]]:
        return self._documents()[1]

    def duplicates(self) -> list[dict[str, Any]]:
        near = self._documents()[2]
        with sqlite3.connect(self.db_path) as connection:
            exact = [{"type": row[0], "document_id": row[1], "duplicate_document_id": row[3] or "",
                      "similarity": 1.0, "session_id": row[2]}
                     for row in connection.execute("""SELECT e.action,e.document_id,e.session_id,d.id
                        FROM import_delta_entries e LEFT JOIN documents d ON d.content_hash=e.content_hash AND d.id<>e.document_id
                        WHERE e.action='duplicate' ORDER BY e.id DESC""")]
        return exact + near

    def _documents(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        documents, warnings, near = [], [], []
        with sqlite3.connect(self.db_path) as connection:
            for document_id, title, raw in connection.execute("SELECT id,title,metadata_json FROM documents ORDER BY created_at DESC"):
                quality = (json.loads(raw or "{}").get("knowledge_quality") or {})
                if not quality:
                    continue
                row = {"document_id": document_id, "title": title, "score": int(quality.get("knowledge_quality_score", 0)),
                       "classification": quality.get("classification", "unknown"), "language": quality.get("language", "unknown")}
                documents.append(row)
                warnings.extend({**row, "warning": warning} for warning in quality.get("warnings", []))
                if quality.get("near_duplicate_detected"):
                    near.append({"type": "near_duplicate", "document_id": document_id,
                                 "duplicate_document_id": quality.get("near_duplicate_document_id"),
                                 "similarity": quality.get("near_duplicate_similarity", 0)})
        return documents, warnings, near
