from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.real_ai_layer import ai_summarize

if __name__ == "__main__":
    sample = "SecondBrain-Agent importiert Wissen nach Obsidian und erzeugt Reports, Aufgaben und Graphen."
    try:
        result = ai_summarize(PROJECT_ROOT, sample)
        print(result)
    except Exception as exc:
        print("AI Layer Fehler:", exc)
        print("Prüfe Ollama: ollama serve")
        raise SystemExit(2)
