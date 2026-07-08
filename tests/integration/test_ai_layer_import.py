from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.real_ai_layer import ai_classify

if __name__ == "__main__":
    print("AI Layer Integration Test ist optional, benötigt laufendes Ollama.")
