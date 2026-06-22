# SecondBrain OS v16.8 – Realtime Voice

## Ziel
v16.8 ergänzt eine produktnähere Voice Runtime mit Session State, Wake Word Scaffold und Approval-Grenze.

## Enthalten
- Voice Sessions
- Wake Word Stub
- Manual Streaming STT Adapter
- Console TTS Adapter
- Intent Parser
- Risk/Approval Boundary
- Voice Memory
- Interrupt Handling
- SQLite Persistence

## Befehle
```powershell
python launcher.py voice16-migrate
python launcher.py voice16-status
python launcher.py voice16-session-start
python launcher.py voice16-wake "Jarvis status"
python launcher.py voice16-transcribe "Jarvis" "zeige" "Status"
python launcher.py voice16-say "System bereit"
python launcher.py voice16-handle "notiz Tischtennis Rückschlag trainieren"
python launcher.py voice16-recall Tischtennis
python launcher.py voice16-interrupt --reason user_stop
python launcher.py voice16-turns
python launcher.py voice16-events
```

## Grenzen
- Kein echtes Mikrofonstreaming.
- Kein echtes Wake-Word-Modell.
- Kein echtes Whisper/Piper.
- Audio ist TTS-Referenz, keine Audiodatei.
