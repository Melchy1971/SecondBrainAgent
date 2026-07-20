# v31.79 Truthful Native Voice Gate

The native voice application gate now evaluates the desktop runtime's actual
STT, microphone and TTS readiness. Missing optional voice dependencies or
hardware produce `CONDITIONAL_PASS` warnings for voice input, output and wake
word checks instead of an incorrect full `PASS`.

Structural, privacy and workspace-isolation failures remain hard blockers. The
persisted report exposes only readiness booleans and the selected STT engine;
microphone names, dependency errors and local paths are not included.
