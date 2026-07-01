"""Laedt die lokale .env-Datei in die Prozessumgebung (os.environ).

Hintergrund
-----------
Die Anzeige-Panels (Document/Memory Center) lesen .env direkt, die eigentliche
Embedding-/RAG-Laufzeit aber ueber os.getenv(). Bisher hat nichts die .env in die
Prozessumgebung geladen, weshalb gesetzte Werte (z. B. OpenAI-Embedding) in der
Engine nicht ankamen. Dieser Loader schliesst die Luecke.

Verhalten
---------
- Nur KEY=VALUE-Zeilen, Kommentare (#) und Leerzeilen werden ignoriert.
- Es wird os.environ.setdefault genutzt: bereits gesetzte Prozess-/System-Variablen
  gewinnen, die .env fuellt nur Luecken. So bleibt das Verhalten vorhersehbar.
- Leere Werte werden uebersprungen, damit ein leerer Platzhalter (z. B.
  OPENAI_API_KEY=) keine echte System-Variable verdeckt.
- Keine Abhaengigkeit (kein python-dotenv noetig).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def load_env_file(root: str | Path | None = None) -> dict[str, str]:
    """Liest <root>/.env und setzt fehlende Werte in os.environ.

    Gibt das Dict der aus der Datei gelesenen (nicht-leeren) Werte zurueck.
    """
    base = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    env_path = base / ".env"
    loaded: dict[str, str] = {}
    if not env_path.exists():
        return loaded
    try:
        for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            if not key or not value:
                continue
            loaded[key] = value
            os.environ.setdefault(key, value)
    except Exception:
        # Ein defektes .env darf den Start nicht verhindern.
        return loaded
    return loaded
