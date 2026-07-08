from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.agent_memory_replay import write_memory_replay

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]).strip()
    if not topic:
        topic = input("Thema: ").strip()
    settings = load_settings(PROJECT_ROOT)
    target = write_memory_replay(settings, topic)
    print(f"Memory Replay erstellt: {target}")
