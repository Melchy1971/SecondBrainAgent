"""Regelbasierte Basisklassifikation: deterministisch, deutschsprachig, erklärbar."""

from __future__ import annotations

from typing import Any

# Dokumenttyp -> (Marker, Tag-Vorschläge)
RULE_SETS: dict[str, dict[str, Any]] = {
    "rechnung": {
        "markers": ("rechnung", "rechnungsnummer", "invoice", "netto", "brutto",
                    "mwst", "ust-id", "zahlbar bis", "zahlungsziel", "betrag"),
        "tags": ("finanzen", "beleg"),
    },
    "vertrag": {
        "markers": ("vertrag", "vereinbarung", "kündigungsfrist", "laufzeit",
                    "vertragspartner", "agb", "nda", "geheimhaltung"),
        "tags": ("recht", "vertrag"),
    },
    "protokoll": {
        "markers": ("protokoll", "meeting", "teilnehmer", "agenda", "besprechung",
                    "ergebnis:", "nächste schritte", "action items"),
        "tags": ("meeting",),
    },
    "task": {
        "markers": ("aufgabe:", "- [ ]", "todo", "erledigen", "nächster schritt",
                    "deadline", "fällig"),
        "tags": ("aufgabe",),
    },
    "projekt": {
        "markers": ("projekt", "masterplan", "roadmap", "sprint", "backlog",
                    "release", "mvp", "meilenstein"),
        "tags": ("projekt",),
    },
    "prozess": {
        "markers": ("prozess", "prozessdesign", "workflow", "ablauf", "bpmn",
                    "prozessschritt", "freigabeprozess", "sap", "jira", "mywiki"),
        "tags": ("prozess",),
    },
    "person": {
        "markers": ("kontakt", "person:", "ansprechpartner", "stakeholder", "visitenkarte"),
        "tags": ("kontakt",),
    },
    "quelle": {
        "markers": ("http://", "https://", "quelle", "artikel", "recherche",
                    "youtube", "perplexity"),
        "tags": ("quelle",),
    },
    "wissen": {
        "markers": ("definition", "konzept", "architektur", "erklärung",
                    "entscheidung", "wissen", "howto", "anleitung"),
        "tags": ("wissen",),
    },
}

BASE_CONFIDENCE = 0.5
PER_MARKER = 0.12
MAX_RULE_CONFIDENCE = 0.9


def classify_by_rules(text: str) -> dict[str, Any]:
    """Returns {document_type, tags, confidence, matched_markers, method}."""
    lowered = text.lower()
    best_type = "inbox"
    best_hits: list[str] = []
    best_tags: tuple[str, ...] = ()
    for doc_type, spec in RULE_SETS.items():
        hits = [marker for marker in spec["markers"] if marker in lowered]
        if len(hits) > len(best_hits):
            best_type, best_hits, best_tags = doc_type, hits, spec["tags"]
    if not best_hits:
        return {"document_type": "inbox", "tags": [], "confidence": 0.3,
                "matched_markers": [], "method": "rules"}
    confidence = min(BASE_CONFIDENCE + PER_MARKER * len(best_hits), MAX_RULE_CONFIDENCE)
    return {
        "document_type": best_type,
        "tags": list(best_tags),
        "confidence": round(confidence, 2),
        "matched_markers": best_hits,
        "method": "rules",
    }
