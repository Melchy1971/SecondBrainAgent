# v30.83 — Voice: Offline STT + TTS

Gleiche Port/Adapter/Orchestrierung wie Vision. Vorgabe offline-only, GPU vorhanden, Deps optional.

## Neu
- `voice/ports.py`: Audio/AudioClip, Transcript/TranscriptSegment, Protocols
  `SttEngine`, `StreamingStt` (für v30.84), `TtsEngine`, `MicrophoneSource`.
- `voice/engines/`: `whisper_stt.py` (`WhisperSttEngine`, faster-whisper, CUDA, lazy, Integration-only),
  `piper_tts.py` (`PiperTtsEngine`, lazy), `fake.py` (deterministische Fakes für Tests).
- `voice/transcribe.py`: `VoiceTranscriber` — STT -> `Transcript` -> **Voice-Memory-Ingest** als
  `ConnectorItem` über `ConnectorImportBridge`. Kein zweiter Ingestion-Weg.

## Testbarkeit / Abnahme
- Grün (6 Tests): Transcript-Aggregation, Ingest, TTS-Fake, Streaming-Fake.
- Übersprungen ohne Deps: faster-whisper- und Piper-Integrationstests (`importorskip`).
- Echte STT/TTS-Abnahme (WER auf Golden-Audio) läuft auf deiner GPU-Maschine.

## Launcher (Python 3.11+, mit Deps + Modellen)
```
python launcher.py voice-transcribe --audio note.wav --model medium --lang de
python launcher.py voice-say --text "Guten Morgen" --voice-model de_DE-thorsten-medium.onnx --out hallo.wav
```
Fehlende Engine -> `engine_unavailable`, kein Crash.

## Scope-Grenze (bewusst)
v30.83 = Batch-STT + TTS + Transkript-Ingest. Streaming-STT/-TTS, Wake Word, Interrupt und
Conversation Mode folgen v30.84; Speaker Profiles + Voice-Commands/Agent-Integration v30.85
(`StreamingStt`-Port ist bereits vorhanden).
