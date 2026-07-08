"""Voice Control v20 - Intent-Routing.

Wandelt erkannten Text in eine strukturierte Absicht (Intent) um. Deutsch- und
englischtolerant. Skript-Intents bilden ausschliesslich auf die HUD-Allowlist
ab (review-first, keine destruktiven Aktionen).

Backward-compatible: ``VoiceCommandRouter.route(text) -> str`` bleibt.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Sprachbefehl -> erlaubtes HUD-Skript (Teilmenge von ALLOWED_SCRIPTS im HUD).
SCRIPT_ALIASES = {
    "import_ai_exports.py": ("ki import", "ai import", "exports importieren", "importiere ki"),
    "build_vector_rag.py": ("index bauen", "vektor", "rag neu", "rebuild index", "index aktualisieren"),
    "run_v10_cycle.py": ("v10 zyklus", "personal os", "os zyklus", "run v10"),
    "check_paths_v9.py": ("pfade pruefen", "pfade prüfen", "check paths", "pfadpruefung"),
    "release_gate_v9.py": ("release gate", "freigabe gate", "gate"),
    "run_regression_tests_v9.py": ("regression", "tests laufen", "run tests", "regressionstests"),
}

DICTATION_TRIGGERS = ("diktat", "diktiere", "notiz", "notier", "schreib auf",
                      "halt fest", "festhalten", "merke")
RAG_TRIGGERS = ("frage", "frag", "was weisst du", "was weißt du", "suche", "such",
                "finde", "wo steht", "zeig mir", "rag")
STATUS_TRIGGERS = ("status", "wie geht es", "systemstatus", "lage")
STOP_TRIGGERS = ("stopp", "stop", "beenden", "ende", "schluss", "aus", "exit", "quit")


@dataclass
class Intent:
    kind: str                      # rag | run_script | dictation | status | stop | unknown
    payload: str = ""              # Query/Diktattext/Skriptname
    raw: str = ""
    meta: dict = field(default_factory=dict)


class VoiceCommandRouter:
    def parse(self, text: str) -> Intent:
        raw = (text or "").strip()
        low = raw.lower()
        if not low:
            return Intent("unknown", raw=raw)

        # Reihenfolge bewusst: Stop > Skript > Diktat > RAG > Status > unknown.
        if any(low == t or low.startswith(t + " ") or low.endswith(" " + t)
               for t in STOP_TRIGGERS):
            return Intent("stop", raw=raw)

        for script, triggers in SCRIPT_ALIASES.items():
            if any(t in low for t in triggers):
                return Intent("run_script", payload=script, raw=raw)

        if any(t in low for t in DICTATION_TRIGGERS):
            return Intent("dictation", payload=self._strip_trigger(raw, DICTATION_TRIGGERS),
                          raw=raw)

        if any(t in low for t in RAG_TRIGGERS):
            return Intent("rag", payload=self._strip_trigger(raw, RAG_TRIGGERS), raw=raw)

        if any(t in low for t in STATUS_TRIGGERS):
            return Intent("status", raw=raw)

        # Default: als Wissensfrage ans Vault behandeln, statt nichts zu tun.
        return Intent("unknown", payload=raw, raw=raw)

    @staticmethod
    def _strip_trigger(text: str, triggers) -> str:
        low = text.lower()
        cut = text
        for t in triggers:
            idx = low.find(t)
            if idx != -1:
                cut = text[idx + len(t):]
                break
        return cut.lstrip(" :,.-").strip() or text.strip()

    # --- Back-compat ---------------------------------------------------------
    def route(self, text: str) -> str:
        text = (text or "").lower()
        if "mail" in text:
            return "gmail"
        if "kalender" in text:
            return "calendar"
        return "chat"
