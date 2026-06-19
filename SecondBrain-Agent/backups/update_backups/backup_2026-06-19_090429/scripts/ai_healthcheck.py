from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.ai_layer_real import ai_summarize

if __name__ == "__main__":
    try:
        result = ai_summarize(PROJECT_ROOT, "SecondBrain-Agent nutzt Ollama für lokale KI.")
        print("AI Layer OK")
        print(result[:1000])
    except Exception as exc:
        print("AI Layer FAIL")
        print(exc)
        print("Prüfen: ollama serve")
        raise SystemExit(2)
