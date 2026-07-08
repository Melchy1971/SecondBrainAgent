from pathlib import Path
import re
from collections import Counter
from .v9_common import iter_md, read, now_date, ensure

EMAIL_RE = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")
NAME_HINT_RE = re.compile(r"\b[A-ZÄÖÜ][a-zäöüß]+(?:\s[A-ZÄÖÜ][a-zäöüß]+){0,2}\b")

def write_crm_index(vault: Path) -> Path:
    folder = ensure(vault / "80_PersonalCRM")
    target = folder / "Personal_CRM_Index.md"
    emails = Counter()
    names = Counter()
    for p in iter_md(vault):
        text = read(p)
        emails.update(EMAIL_RE.findall(text))
        # lightweight names, filtered by frequency
        names.update(NAME_HINT_RE.findall(text[:5000]))

    lines = ["# Personal CRM", "", f"Aktualisiert: {now_date()}", "", "## E-Mail-Kontakte", ""]
    for e, c in emails.most_common(50):
        lines.append(f"- {e}: {c}")
    lines += ["", "## Namenssignale", ""]
    for n, c in names.most_common(50):
        lines.append(f"- {n}: {c}")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
