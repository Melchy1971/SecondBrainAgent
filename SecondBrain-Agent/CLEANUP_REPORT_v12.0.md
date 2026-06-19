# SecondBrain OS v12.0 – Bereinigung

## Entfernt

- Python Bytecode: `__pycache__/`, `*.pyc`
- Pytest-Artefakte: `.pytest_cache/`, `.coverage`
- lokale Laufzeitdaten: `runtime/`
- Event-Ausgaben: `events/runtime/`, generierte Event-Markdown-Dateien
- Cache-Dateien: `cache/`
- Log-Dateien: `logs/`
- verarbeitete Beispielimporte: `archive/processed/`
- Betriebssystem-Artefakte: `.DS_Store`

## Behalten

- `launcher.py`
- `requirements.txt`
- `secondbrain/`
- `config/`
- `docs/`
- `tests/`
- `scripts/`
- `modules/`
- `runtime/` wird beim Start durch `python launcher.py init` neu erzeugt

## Korrektur

- `launcher_runtime_v120.py` delegiert ältere CLI-Befehle wieder korrekt an v11.9.
- Damit funktionieren neben den v12-Befehlen auch ältere Befehle wie `improve-feedback`, `ops-backup`, `api-status`, `mobile-status`, `voice-status`.

## Validierung

- Testlauf vor finaler Bereinigung: `81 passed`
