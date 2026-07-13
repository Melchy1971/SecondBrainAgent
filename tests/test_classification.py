"""Tests für Klassifizierung: Regeln, PII, Engine, Review Queue, Tag-Historie."""

from __future__ import annotations

from pathlib import Path

from secondbrain.classification import (
    CONFIDENCE_REVIEW_THRESHOLD, ClassificationEngine, ReviewQueue, TagHistory,
    classify_by_rules, classify_document, detect_pii,
)


# --- Regeln ------------------------------------------------------------------

def test_rules_classify_invoice_with_tags_and_confidence():
    text = "Rechnung Nr. 2026-042, Betrag netto 100 EUR, MwSt 19%, zahlbar bis 31.07."
    result = classify_by_rules(text)
    assert result["document_type"] == "rechnung"
    assert "finanzen" in result["tags"]
    assert result["confidence"] > CONFIDENCE_REVIEW_THRESHOLD
    assert result["matched_markers"]


def test_rules_unknown_content_falls_back_to_inbox_low_confidence():
    result = classify_by_rules("xyzzy plugh 42")
    assert result["document_type"] == "inbox"
    assert result["confidence"] < CONFIDENCE_REVIEW_THRESHOLD


def test_rules_detect_process_documents():
    result = classify_by_rules("Prozessdesign für den Freigabeprozess in SAP, Ablauf in myWiki dokumentiert")
    assert result["document_type"] == "prozess"


# --- PII ---------------------------------------------------------------------

def test_pii_detects_iban_email_and_api_key():
    text = ("Kontakt: max@example.com, IBAN DE89 3704 0044 0532 0130 00, "
            "api key sk-abcdef1234567890")
    result = detect_pii(text)
    assert result["sensitive"] is True
    types = {f["type"] for f in result["findings"]}
    assert {"iban", "email", "api_key"} <= types
    # Samples sind maskiert
    assert all("…" in f["sample_masked"] for f in result["findings"])


def test_pii_clean_text_is_not_sensitive():
    assert detect_pii("Projektnotiz ohne personenbezogene Daten.")["sensitive"] is False


def test_confidential_marker_flags_sensitive():
    assert detect_pii("VERTRAULICH: interne Strategie")["sensitive"] is True


# --- Engine ---------------------------------------------------------------------

def test_engine_adds_sensitive_tag_and_review_flag():
    result = classify_document("unklarer inhalt mit iban DE89 3704 0044 0532 0130 00")
    assert result["sensitive"] is True
    assert "sensibel" in result["tags"]
    assert result["needs_review"] is True


def test_engine_llm_overrides_only_with_higher_confidence():
    def strong_llm(_text: str) -> dict:
        return {"document_type": "vertrag", "tags": ["llm"], "confidence": 0.95}

    def weak_llm(_text: str) -> dict:
        return {"document_type": "quatsch", "tags": ["llm"], "confidence": 0.1}

    invoice = "Rechnung Nr. 1, Betrag brutto, MwSt, zahlbar bis morgen"
    strong = ClassificationEngine(strong_llm).classify(invoice)
    assert strong["document_type"] == "vertrag"
    assert strong["method"] == "llm"
    weak = ClassificationEngine(weak_llm).classify(invoice)
    assert weak["document_type"] == "rechnung"
    assert "llm" in weak["tags"]  # Tags werden gemerged


def test_engine_llm_errors_degrade_silently_to_rules():
    def broken_llm(_text: str) -> dict:
        raise RuntimeError("provider down")

    result = ClassificationEngine(broken_llm).classify("Rechnung Betrag MwSt")
    assert result["document_type"] == "rechnung"
    assert result["method"] == "rules"


# --- Review Queue + Tag-Historie ---------------------------------------------------

def test_low_confidence_review_and_manual_override_is_traceable(tmp_path: Path):
    queue = ReviewQueue(tmp_path)
    item = queue.add("docs/unklar.txt",
                     {"document_type": "inbox", "tags": [], "confidence": 0.3},
                     job_id="job_x")
    assert queue.list_open()[0]["review_id"] == item["review_id"]

    resolved = queue.resolve(item["review_id"], document_type="vertrag",
                             tags=["recht", "wichtig"], editor="markus")
    assert resolved["status"] == "resolved"
    assert queue.list_open() == []

    history = TagHistory(tmp_path).for_document("docs/unklar.txt")
    assert len(history) == 1
    entry = history[0]
    assert entry["source"] == "manual"
    assert entry["editor"] == "markus"
    assert entry["old_type"] == "inbox"
    assert entry["new_type"] == "vertrag"
    assert entry["new_tags"] == ["recht", "wichtig"]


# --- Integration mit der Import-Pipeline ---------------------------------------------

def test_pipeline_classifies_and_routes_low_confidence_to_review(tmp_path: Path):
    from secondbrain.import_pipeline import UnifiedImportPipeline

    clear = tmp_path / "rechnung.txt"
    clear.write_text("Rechnung Nr. 7, Betrag netto 50 EUR, MwSt 19%, zahlbar bis 01.08. " * 5,
                     encoding="utf-8")
    unclear = tmp_path / "unklar.txt"
    unclear.write_text("lorem ipsum dolor sit amet " * 20, encoding="utf-8")

    pipeline = UnifiedImportPipeline(tmp_path, indexer=lambda t, m: {"ok": True})
    job_clear = pipeline.process(pipeline.submit_file(clear).job_id)
    job_unclear = pipeline.process(pipeline.submit_file(unclear).job_id)

    assert job_clear.document_type == "rechnung"
    assert "finanzen" in job_clear.tags

    open_reviews = ReviewQueue(tmp_path).list_open()
    assert len(open_reviews) == 1
    assert open_reviews[0]["job_id"] == job_unclear.job_id

    # Vorschläge sind in der Tag-Historie dokumentiert
    history = TagHistory(tmp_path).for_document(str(clear))
    assert history and history[0]["source"] == "suggestion"
