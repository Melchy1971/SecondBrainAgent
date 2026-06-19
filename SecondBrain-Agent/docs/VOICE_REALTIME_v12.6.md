# Voice Realtime v12.6

## Ziel
Lokale, sichere Realtime-Voice-Foundation ohne harte Audio- oder Cloud-Abhängigkeit.

## Architektur

```text
Speech Input
↓
Wake Word Detector
↓
Streaming STT Adapter
↓
Voice Command Router
↓
Approval Boundary
↓
Tool Registry / Agent Runtime
↓
Streaming TTS Adapter
↓
Voice Memory
```

## Befehle

```powershell
python launcher.py voice-status2
python launcher.py voice-session2
python launcher.py voice-wake "Jarvis Status"
python launcher.py voice-transcribe "Jarvis" "zeige" "Status"
python launcher.py voice-parse2 "Jarvis erstelle eine Notiz"
python launcher.py voice-handle2 "Jarvis zeige Status"
python launcher.py voice-handle2 "Jarvis lösche Daten" --approved
python launcher.py voice-speak2 "System bereit"
python launcher.py voice-interrupt --reason user_stop
python launcher.py voice-events
python launcher.py voice-memory
```

## Designentscheidung
Die Adapter sind bewusst offline und austauschbar. Produktive Adapter für Whisper, faster-whisper, Vosk, Piper, ElevenLabs oder Azure werden in separaten Provider-Modulen ergänzt.
