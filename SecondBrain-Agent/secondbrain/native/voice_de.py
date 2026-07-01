from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GermanVoiceIntent:
    intent: str
    text: str = ""
    command: str = ""
    target: str = ""
    requires_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GermanVoiceCommandParser:
    """Deterministischer Parser fuer deutsche Jarvis-Sprachbefehle.

    Der Parser ist absichtlich offline-faehig. STT/TTS Engines koennen spaeter
    davor/dahinter geschaltet werden; die Intent-Logik bleibt testbar und ohne
    Mikrofonzugriff nutzbar.
    """

    OPEN_TARGETS = {
        "dashboard": "dashboard",
        "start": "dashboard",
        "dokumente": "documents",
        "dokument": "documents",
        "dateien": "documents",
        "suche": "search",
        "rag": "rag",
        "wissen": "rag",
        "memory": "memory",
        "gedächtnis": "memory",
        "gedaechtnis": "memory",
        "einstellungen": "settings",
        "settings": "settings",
        "jobs": "jobs",
        "status": "status",
    }

    def parse(self, text: str) -> GermanVoiceIntent:
        raw = (text or "").strip()
        low = raw.lower().strip()
        low = low.replace("öffne", "oeffne").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        if not low:
            return GermanVoiceIntent("unknown", text=raw)

        if low in {"stopp", "stop", "abbrechen", "beenden", "ende", "jarvis beenden"}:
            return GermanVoiceIntent("stop", text=raw, command="voice-stop")

        if low.startswith("jarvis "):
            low = low[len("jarvis "):].strip()

        if low in {"status", "systemstatus", "wie ist der status", "zeige status"}:
            return GermanVoiceIntent("status", text=raw, command="native-status", target="status")

        for prefix in ("oeffne ", "zeige ", "gehe zu ", "wechsel zu "):
            if low.startswith(prefix):
                target_raw = low[len(prefix):].strip()
                target = self._resolve_target(target_raw)
                return GermanVoiceIntent("open", text=raw, command=f"native-open:{target}", target=target)

        for prefix in ("suche nach ", "suche ", "finde "):
            if low.startswith(prefix):
                query = raw[len(prefix):].strip() if raw.lower().startswith(prefix.replace("oe", "ö")) else raw.split(" ", 1)[1].strip()
                return GermanVoiceIntent("search", text=query, command="p1-rag-hybrid-search", target="search")

        for prefix in ("frage ", "frag ", "beantworte "):
            if low.startswith(prefix):
                query = raw.split(" ", 1)[1].strip() if " " in raw else ""
                return GermanVoiceIntent("ask", text=query, command="p1-rag-answer", target="rag")

        if low.startswith("importiere datei ") or low.startswith("datei importieren "):
            value = raw.split(" ", 2)[2].strip() if len(raw.split(" ", 2)) > 2 else ""
            return GermanVoiceIntent("import_file", text=value, command="p1-rag-ingest-file", target="documents", requires_confirmation=True)

        if low in {"repariere index", "index reparieren", "vektor index reparieren"}:
            return GermanVoiceIntent("repair_index", text=raw, command="p1-vector-index-repair", target="rag", requires_confirmation=True)

        if low in {"production gate", "produkt status", "produktionsstatus", "pruefe produktion", "prüfe produktion"}:
            return GermanVoiceIntent("production_gate", text=raw, command="p1-production", target="status")

        if low.startswith("notiere ") or low.startswith("merke ") or low.startswith("schreib auf "):
            note = raw.split(" ", 1)[1].strip() if " " in raw else ""
            return GermanVoiceIntent("dictation", text=note, command="memory-note", target="memory", requires_confirmation=True)

        return GermanVoiceIntent("ask", text=raw, command="p1-rag-answer", target="rag")

    def _resolve_target(self, text: str) -> str:
        normalized = text.strip().lower()
        for key, target in self.OPEN_TARGETS.items():
            if key in normalized:
                return target
        return "dashboard"
