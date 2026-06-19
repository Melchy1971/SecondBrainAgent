from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    plugin = PROJECT_ROOT / "obsidian-plugin"
    files = ["manifest.json", "package.json", "src/main.ts", "styles.css"]
    print("Obsidian Plugin Status")
    for f in files:
        p = plugin / f
        print(("OK   " if p.exists() else "FEHLT"), f)
