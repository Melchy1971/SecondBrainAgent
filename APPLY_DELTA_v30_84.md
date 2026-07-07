# APPLY DELTA v30.84 — Streaming + Conversation

## Neu
- `secondbrain/voice/streaming.py`, `conversation.py`; Ports erweitert (Wake/VAD/StreamingTts).
- `engines/webrtc_vad.py`, `openwakeword_detector.py`, `whisper_streaming.py` (lazy).
- `tests/voice/test_streaming_session.py`, `test_conversation.py`, `test_streaming_engines_integration.py`.
- `launcher.py` — `voice-converse` (Verfügbarkeitscheck).

## Validierung (Sandbox)
```
pytest SecondBrain-Agent/tests/voice -q     # 12 passed, 4 skipped
pytest SecondBrain-Agent/tests/connectors SecondBrain-Agent/tests/vision SecondBrain-Agent/tests/voice -q  # 85 passed, 5 skipped
```

## Live (deine GPU-Maschine + Mikrofon)
`pip install -r requirements-voice.txt` (inkl. webrtcvad/openwakeword/sounddevice), dann Live-Loop.
