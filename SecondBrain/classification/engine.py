"""ClassificationEngine: Regeln + optionale LLM-Klassifikation + PII-Markierung.

LLM-Nutzung ist strikt optional und injizierbar (Callable[[str], dict]).
Ohne LLM arbeitet die Engine rein regelbasiert und deterministisch.
"""

from __future__ import annotations

from typing import Any, Callable

from secondbrain.classification.pii import detect_pii
from secondbrain.classification.rules import classify_by_rules

CONFIDENCE_REVIEW_THRESHOLD = 0.6
SENSITIVE_TAG = "sensibel"

LlmClassifier = Callable[[str], dict[str, Any]]


class ClassificationEngine:
    def __init__(self, llm_classifier: LlmClassifier | None = None):
        self.llm_classifier = llm_classifier

    def classify(self, text: str) -> dict[str, Any]:
        """Returns {document_type, tags, confidence, needs_review, sensitive, pii, method}."""
        result = classify_by_rules(text)
        if self.llm_classifier is not None:
            result = self._merge_llm(text, result)
        pii = detect_pii(text)
        tags = list(dict.fromkeys(result["tags"]))
        if pii["sensitive"] and SENSITIVE_TAG not in tags:
            tags.append(SENSITIVE_TAG)
        return {
            "schema": "secondbrain.classification.result.v1",
            "document_type": result["document_type"],
            "tags": tags,
            "confidence": result["confidence"],
            "needs_review": result["confidence"] < CONFIDENCE_REVIEW_THRESHOLD,
            "sensitive": pii["sensitive"],
            "pii": pii,
            "method": result["method"],
            "matched_markers": result.get("matched_markers", []),
        }

    def _merge_llm(self, text: str, rule_result: dict[str, Any]) -> dict[str, Any]:
        """LLM-Ergebnis überstimmt Regeln nur bei höherer Confidence; Fehler degradieren still."""
        try:
            llm = self.llm_classifier(text)  # type: ignore[misc]
        except Exception:
            return rule_result
        llm_confidence = float(llm.get("confidence", 0.0))
        if llm_confidence <= rule_result["confidence"]:
            merged_tags = list(rule_result["tags"]) + [t for t in llm.get("tags", [])
                                                       if t not in rule_result["tags"]]
            return {**rule_result, "tags": merged_tags, "method": "rules+llm"}
        return {
            "document_type": str(llm.get("document_type", rule_result["document_type"])),
            "tags": list(dict.fromkeys(list(llm.get("tags", [])) + list(rule_result["tags"]))),
            "confidence": round(min(llm_confidence, 0.98), 2),
            "matched_markers": rule_result.get("matched_markers", []),
            "method": "llm",
        }


def classify_document(text: str, *, llm_classifier: LlmClassifier | None = None) -> dict[str, Any]:
    """Modul-Einstieg; wird u.a. von der Import-Pipeline genutzt."""
    return ClassificationEngine(llm_classifier).classify(text)
