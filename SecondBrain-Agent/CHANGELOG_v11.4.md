# SecondBrain OS v11.4 - Voice Assistant 2.0

## Neu
- Voice Runtime mit persistenter Session-Verwaltung
- Voice Command Router für Status, Health, Capture, RAG, Ask, Agent und Workflow
- STT/TTS-Abstraktion mit Offline-Manual-STT und Console-TTS
- Approval-Grenze für riskante Voice-Kommandos
- Launcher-Kommandos: voice-status, voice-session, voice-sessions, voice-parse, voice-say, voice-handle, voice-config

## Designentscheidung
Voice bleibt zunächst Push-to-Talk/Manual-STT. Wake Word ist vorbereitet, aber bewusst nicht als dauerhafter Mikrofonprozess aktiviert. Grund: Datenschutz, Windows-Rechte, Fehltrigger-Risiko.
