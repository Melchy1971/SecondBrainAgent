from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

scripts = [
    "import_chatgpt_folder.py",
    "import_gemini_folder.py",
    "import_perplexity_folder.py",
]

if __name__ == "__main__":
    for script in scripts:
        p = PROJECT_ROOT / "scripts" / script
        if p.exists():
            subprocess.run([sys.executable, str(p)], cwd=str(PROJECT_ROOT))
    print("AI Export Sammelimport abgeschlossen.")
