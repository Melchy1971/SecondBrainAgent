from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD_PATTERNS = ["H:\\Obsidian", "H:\\\\Obsidian"]
EXT = {".py", ".yaml", ".yml", ".json", ".md", ".txt", ".ps1", ".js", ".ts"}

hits = []
for p in ROOT.rglob("*"):
    if p.name == "check_paths_v9.py":
        continue
    if p.is_file() and p.suffix.lower() in EXT:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if any(bad in text for bad in BAD_PATTERNS):
            hits.append(str(p.relative_to(ROOT)))

print("Path Check v9")
if hits:
    print("FAIL: alte produktive Pfade gefunden")
    for h in hits:
        print("-", h)
    raise SystemExit(2)

print("PASS: keine alten produktiven Pfade gefunden")
print("Vault: H:\\SecondBrainAgent\\SecondBrain")
print("Inbox: H:\\SecondBrainAgent\\SecondBrain-Inbox")
print("Agent: H:\\SecondBrainAgent\\SecondBrain-Agent")
