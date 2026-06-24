"""Voice Control v20 - Diktat in die Inbox.

Schreibt diktierten Freitext als strukturierte Markdown-Notiz in
``SecondBrain-Inbox/Voice/Dictation``. Frontmatter-Format kompatibel zum
v103-Diktatimport, damit run_v103_cycle die Notizen weiterverarbeiten kann.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


def _slug(text: str, words: int = 6) -> str:
    toks = [t for t in text.lower().split() if t.isalnum() or t.isalpha()]
    base = "-".join(toks[:words]) if toks else "diktat"
    safe = "".join(c for c in base if c.isalnum() or c in "-_")
    return safe[:60] or "diktat"


def write_dictation(text: str, target_dir: str | Path, now: datetime | None = None) -> Path:
    """Legt eine Diktat-Notiz an und gibt den Pfad zurueck."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Leeres Diktat - nichts zu speichern.")
    now = now or datetime.now()
    folder = Path(target_dir)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y-%m-%d_%H%M%S")
    title = text.split("\n", 1)[0][:80]
    path = folder / f"{stamp}_{_slug(text)}.md"
    path.write_text(
        "---\n"
        f'title: "{title}"\n'
        "type: dictation\n"
        "source: voice\n"
        f"created: {now.strftime('%Y-%m-%d')}\n"
        "tags:\n  - voice\n  - dictation\n"
        "---\n\n"
        f"# {title}\n\n"
        "## Diktat\n\n"
        f"{text}\n\n"
        "## erkannte naechste Schritte\n\n"
        "- [ ] pruefen und strukturieren\n",
        encoding="utf-8",
    )
    return path
