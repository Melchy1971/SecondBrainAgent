from pathlib import Path
from datetime import datetime
import shutil

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
INBOX = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox")

def import_transcript(file_path: str) -> Path:
    source = Path(file_path)
    target_dir = VAULT / "89_MeetingTranscripts"
    target_dir.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8", errors="ignore") if source.suffix.lower() in [".txt", ".md", ".vtt", ".srt"] else f"Audio/Video-Datei vorbereitet: {source}"
    target = target_dir / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{source.stem}.md"
    md = f"""---
title: "{source.stem}"
type: meeting_transcript
source: transcript_import
created: {datetime.now().strftime('%Y-%m-%d')}
tags:
  - meeting
  - transcript
---

# {source.stem}

## Transkript

{text}

## Aufgaben

## Entscheidungen

## Risiken
"""
    target.write_text(md, encoding="utf-8")
    return target

def write_transcription_status() -> Path:
    target = VAULT / "89_MeetingTranscripts" / "Meeting_Transcription_Status.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("""# Meeting Transcription

Status:
- TXT/MD/VTT/SRT Import: aktiv
- Audio/Video Transkription: vorbereitet
- Whisper lokal: vorbereitet

Nächster Schritt:
- Whisper installieren und Audio-Dateien automatisiert in Text wandeln.
""", encoding="utf-8")
    return target
