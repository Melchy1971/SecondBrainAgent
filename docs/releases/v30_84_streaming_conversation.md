# v30.84 — Streaming STT + Wake Word + Interrupt/Conversation

Baut auf v30.83. Kern: die **Conversation-Logik** ist reine State-Machine, voll testbar; Modelle/
Hardware (Wake-Word, VAD, Streaming-Whisper, Mikrofon) sind injiziert und lazy.

## Neu
- Ports: `WakeWordDetector`, `VoiceActivityDetector`, `StreamingTts`.
- `voice/streaming.py`: `StreamingSttSession` — VAD-Endpointing (Endpunkt bei Stille nach Sprache),
  frischer STT-Engine je Äußerung.
- `voice/conversation.py`: `ConversationController` — Zustände IDLE → LISTENING → THINKING → SPEAKING,
  Wake-Gating, **Barge-in/Interrupt** (Sprache während SPEAKING bricht die Ausgabe ab -> LISTENING),
  `conversation_mode` (weiterhören vs. erneut Wake-Wort). Turns werden protokolliert.
- Engines (lazy, Integration-only): `WebRtcVad`, `OpenWakeWordDetector`, `WhisperStreamingStt`.

## Testbarkeit / Abnahme
- Grün (12 Tests): Endpointing, Session-Reset, Wake-Gating, voller Turn, **Interrupt/Barge-in**,
  Non-Conversation-Mode -> IDLE.
- Übersprungen ohne Deps: webrtcvad/openwakeword/faster-whisper/piper (`importorskip`).
- Latenz-/WER-Abnahme (Wake→STT→Reply→TTS < ~1 s) läuft auf deiner GPU-Maschine mit Mikrofon.

## Launcher
```
python launcher.py voice-converse     # prüft, ob der Stack verfügbar ist
```
Der Live-Duplex-Loop braucht einen Mikrofon-Stack (sounddevice) und wird am Zielsystem gestartet;
`voice-converse` meldet fehlende Deps sauber statt zu crashen.

## Scope-Grenze
Speaker Profiles, persistente Voice-Memory-Ablage und Voice-Command/Agent-Integration sind v30.85.
