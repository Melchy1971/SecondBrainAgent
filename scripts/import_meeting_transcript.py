from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.meeting_transcription_v95 import import_transcript
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\import_meeting_transcript.py <transkript.txt>")
        raise SystemExit(1)
    print(import_transcript(sys.argv[1]))
