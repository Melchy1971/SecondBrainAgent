from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.validator import validate_environment
from secondbrain.rag import chunk_text
from secondbrain.extractor import extract_tasks

def test_config_loads():
    settings = load_settings(PROJECT_ROOT)
    assert "vault_path" in settings

def test_chunking():
    chunks = chunk_text("abc " * 1000, size=100, overlap=10)
    assert len(chunks) > 1

def test_task_extraction():
    tasks = extract_tasks("Aufgabe: Test durchführen")
    assert "Test durchführen" in tasks

if __name__ == "__main__":
    test_config_loads()
    test_chunking()
    test_task_extraction()
    print("Smoke Tests OK")
