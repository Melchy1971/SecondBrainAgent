# APPLY DELTA v30.83 — Voice STT + TTS

## Neu
- `secondbrain/voice/` — Ports, Fake-/Whisper-/Piper-Engines, VoiceTranscriber (Voice-Memory-Ingest).
- `tests/voice/` — 6 Unit-Tests (Fakes) + Whisper/Piper-Integrationstests (importorskip).
- `requirements-voice.txt`; `launcher.py` — `voice-transcribe`, `voice-say`.

## Validierung (Sandbox)
```
pytest SecondBrain-Agent/tests/voice -q     # 6 passed, 2 skipped
pytest SecondBrain-Agent/tests/connectors SecondBrain-Agent/tests/vision SecondBrain-Agent/tests/voice -q  # 79 passed, 3 skipped
```

## Live (deine GPU-Maschine)
`pip install -r requirements-voice.txt` (+ Whisper-/Piper-Modelle), dann `voice-transcribe` / `voice-say`.
