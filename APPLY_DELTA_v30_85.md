# APPLY DELTA v30.85 — Speaker + Voice-Memory + Commands

## Neu
- `secondbrain/voice/speaker.py`, `memory.py`, `commands.py`, `engines/resemblyzer_embedder.py`.
- `tests/voice/test_speaker.py`, `test_memory.py`, `test_commands.py`, `test_embedder_integration.py`.
- `launcher.py` — `voice-enroll`, `voice-identify`, `voice-command`.

## Validierung (Sandbox)
```
pytest SecondBrain-Agent/tests/voice -q     # 22 passed, 5 skipped
pytest SecondBrain-Agent/tests/connectors SecondBrain-Agent/tests/vision SecondBrain-Agent/tests/voice -q  # 95 passed, 6 skipped
```

## Live (deine GPU-Maschine)
`pip install resemblyzer` für Sprecher-Embeddings; `voice-command` benötigt keine ML-Deps.
