# v30.85 — Speaker Profiles + Voice-Memory + Voice-Commands

Abschluss der Voice-Kette. Alle Kernlogik offline + deterministisch testbar; nur der reale
Sprach-Embedder ist lazy.

## Neu
- `voice/speaker.py`: `SpeakerEmbedder`-Port, `SpeakerProfileStore` (persistentes JSON),
  `SpeakerMatcher` — Enrollment (Mittelung mehrerer Aufnahmen) + Identifikation via Cosine-Ähnlichkeit
  gegen Schwellwert (bekannt/unknown). Cosine ist reines Python, keine Deps.
- `voice/memory.py`: `VoiceMemoryStore` (persistenter, sprecher-attribuierter Transkript-Log) +
  `VoiceMemory.remember()` — schreibt Record und ingestet als `ConnectorItem` (mit Sprecher-Metadaten)
  über `ConnectorImportBridge` in Memory/RAG.
- `voice/commands.py`: `VoiceCommandRouter` — Regex-Intents mit Slots, `handle()` dispatcht an
  registrierte Handler oder fällt auf den injizierten **Agent-Callback** zurück (Agent-Integration).
- `engines/resemblyzer_embedder.py`: `ResemblyzerEmbedder` (offline, lazy, Integration-only).

## Testbarkeit / Abnahme
- Grün (22 Tests): Cosine, Enroll/Identify (known/unknown), Store-Persistenz, Voice-Memory-Append +
  Sprecher-Attribution + Ingest, Command-Routing (Slots/Handler/Agent-Fallback).
- Übersprungen ohne Deps: resemblyzer, sowie die STT/TTS/VAD/Wake-Engines aus v30.83/84.
- Echte Sprecher-Trennung (Genauigkeit/Threshold-Tuning) läuft auf deiner GPU-Maschine.

## Launcher
```
python launcher.py voice-enroll --speaker markus --label "Markus" --audio ref.wav
python launcher.py voice-identify --audio unknown.wav
python launcher.py voice-command --text "note: Rechnung prüfen"
```
Enroll/Identify brauchen resemblyzer (sonst `engine_unavailable`); `voice-command` läuft ohne ML.

## Voice-Kette komplett
v30.80 OCR/Ingest -> v30.81 Desktop/Klassifikation -> v30.82 Objekterkennung/Diagramme ->
v30.83 STT/TTS -> v30.84 Streaming/Conversation -> v30.85 Speaker/Memory/Commands.
Agent-Integration: `VoiceCommandRouter(agent=...)` bindet den bestehenden Agent-Layer als Callback.
