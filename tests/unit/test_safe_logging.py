from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.safe_logging import redact

if __name__ == "__main__":
    text = "api_key: abcdefghijklmnop password=secret123"
    redacted = redact(text)
    assert "abcdefghijklmnop" not in redacted
    assert "secret123" not in redacted
    print("Safe Logging Test OK")
