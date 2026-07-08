"""v30.46.1 - Volle pytest-Suite (pytest -q) fuer HUD-/CI-Ausfuehrung.

Ergaenzt run_tests.py (Smoke) um das komplette Qualitaetsgate.
Hermetisch: Operator-Umgebung (.env des HUD-Prozesses) wird fuer den
Testlauf entfernt, damit die Suite wie in der CI gegen die
Test-Defaults laeuft (deterministischer Embedding-Provider statt
OpenAI/DATABASE_URL des Betreibers).
Review-first: fuehrt nur Tests aus, loescht nichts.
"""
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STRIP_PREFIXES = ("SECONDBRAIN_",)
STRIP_KEYS = {"OPENAI_API_KEY", "DATABASE_URL", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"}

if __name__ == "__main__":
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in STRIP_KEYS and not key.startswith(STRIP_PREFIXES)
    }
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--maxfail=25"],
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    raise SystemExit(result.returncode)
