"""PII-/Secret-Erkennung: markiert sensible Inhalte für Governance und Redaction."""

from __future__ import annotations

import re
from typing import Any

PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "iban": re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b"),
    "telefon": re.compile(r"(?<!\d)(?:\+49|0049|0)\s?[1-9]\d{1,4}[\s/-]?\d{3,}(?:[\s-]?\d{2,})?(?!\d)"),
    "kreditkarte": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "steuer_id": re.compile(r"\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b"),
    "api_key": re.compile(r"\bsk-[A-Za-z0-9_\-]{10,}\b"),
    "passwort_zuweisung": re.compile(r"(?i)(passwor[td]|kennwort)\s*[:=]\s*\S{4,}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}

# Vertraulichkeitsmarker im Text selbst
SENSITIVITY_MARKERS = ("vertraulich", "confidential", "geheim", "nur für den dienstgebrauch", "nfd")


def detect_pii(text: str, *, max_findings_per_type: int = 5) -> dict[str, Any]:
    """Returns {sensitive, findings: [{type, sample_masked, count}], markers}."""
    findings: list[dict[str, Any]] = []
    for name, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if not matches:
            continue
        first = matches[0] if isinstance(matches[0], str) else str(matches[0])
        masked = first[:3] + "…" + first[-2:] if len(first) > 6 else "…"
        findings.append({
            "type": name,
            "count": len(matches[:max_findings_per_type * 10]),
            "sample_masked": masked,
        })
    lowered = text.lower()
    markers = [marker for marker in SENSITIVITY_MARKERS if marker in lowered]
    return {
        "sensitive": bool(findings or markers),
        "findings": findings,
        "markers": markers,
    }
