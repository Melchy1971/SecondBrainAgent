# Voice Assistant v11.4

## Ziel
Jarvis erhält eine sichere Voice-Command-Schicht. Die Version bindet Sprache nicht direkt an Systemaktionen, sondern routet erkannte Befehle über Intent, Risk Boundary und Launcher Runtime.

## Start

```powershell
python launcher.py voice-status
```

## Befehl analysieren

```powershell
python launcher.py voice-parse "Jarvis status"
```

## Textbefehl ausführen

```powershell
python launcher.py voice-handle "Jarvis status"
python launcher.py voice-handle "Jarvis notiz Neuer Gedanke zum Agent Kernel"
python launcher.py voice-handle "Jarvis suche Digital Twin"
python launcher.py voice-handle "Jarvis frage Was ist der aktuelle Systemzustand?"
```

## Session öffnen

```powershell
python launcher.py voice-session
python launcher.py voice-sessions
```

## Risk Boundary

Folgende Intents sind blockiert, solange `allow_system_actions` nicht aktiv ist:

- `agent.run`
- `workflow.run`
- `runtime.down`

Freischalten:

```powershell
python launcher.py voice-config --allow-system-actions
```

## Architektur

```text
Voice Input
↓
STT Adapter
↓
Voice Command Router
↓
Intent + Risk Boundary
↓
Launcher Runtime
↓
Audit/Event Log
↓
Voice Session Store
```

## Provider

Aktuell enthalten:

- Manual STT: Text wird als transkribierte Eingabe behandelt
- Console TTS: Antwort wird als strukturierter Speak-Event zurückgegeben

Spätere Provider:

- Whisper lokal
- Windows Speech
- Piper TTS
- ElevenLabs optional
- Wake Word Engine
