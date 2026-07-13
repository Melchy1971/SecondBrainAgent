"""Robuste Dokumentklassifizierung.

- rules: regelbasierte Basisklassifikation (deutsch, deterministisch)
- pii: PII-/Secret-Erkennung; sensitive Inhalte werden markiert
- llm: optionale LLM-Klassifikation (injizierbar, kein Provider-Zwang)
- engine: kombiniert Regeln + optionales LLM zu Typ, Tags, Confidence
- review_queue: niedrige Confidence landet zur manuellen Prüfung
- tag_history: jede Tag-Änderung (Vorschlag wie manuell) ist nachvollziehbar
"""

from .rules import RULE_SETS, classify_by_rules
from .pii import PII_PATTERNS, detect_pii
from .engine import CONFIDENCE_REVIEW_THRESHOLD, ClassificationEngine, classify_document
from .review_queue import ReviewQueue
from .tag_history import TagHistory

__all__ = [
    "CONFIDENCE_REVIEW_THRESHOLD", "ClassificationEngine", "PII_PATTERNS",
    "RULE_SETS", "ReviewQueue", "TagHistory",
    "classify_by_rules", "classify_document", "detect_pii",
]
