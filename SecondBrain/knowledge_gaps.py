from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_links, extract_tags, word_tokens

IMPORTANT_SEEDS = ["sap", "obsidian", "claude", "ollama", "python", "mcp", "prozess", "projekt", "email", "pdf"]

def write_knowledge_gaps(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / settings.get("vault_folders", {}).get("knowledge_gaps", "20_KnowledgeGaps")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_knowledge-gaps.md"

    token_counts = Counter()
    notes_by_token = Counter()
    existing_stems = {p.stem.lower() for p in iter_markdown(vault)}

    for note in iter_markdown(vault):
        text = read_note(note)
        tokens = word_tokens(text)
        for token in tokens:
            if len(token) >= 5:
                token_counts[token] += text.lower().count(token)
                notes_by_token[token] += 1

    candidates = []
    for token, count in token_counts.most_common(100):
        if token in existing_stems:
            continue
        if notes_by_token[token] >= 2 or token in IMPORTANT_SEEDS:
            candidates.append((token, count, notes_by_token[token]))

    lines = ["# Wissenslücken", "", f"Datum: {now_date()}", "", "| Begriff | Vorkommen | Notizen | Empfehlung |", "|---|---:|---:|---|"]
    if not candidates:
        lines.append("| Keine klare Lücke erkannt | 0 | 0 | keine |")
    for token, count, notes in candidates[:30]:
        lines.append(f"| {token} | {count} | {notes} | eigene Wissensnotiz prüfen |")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
