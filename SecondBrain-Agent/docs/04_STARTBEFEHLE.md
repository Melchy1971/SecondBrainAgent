# Betriebshandbuch

## Arbeitsverzeichnis

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Optionale Extras stehen in `pyproject.toml`, unter anderem `pdf`, `connectors`, `openai`, `desktop` und `voice`.

## Start

```powershell
python launcher.py
python launcher.py native-gui
python launcher.py native-status
```

Windows-Starter:

```powershell
.\Jarvis.bat
.\HUD.bat
powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Desktop.ps1
```

Optionales Web-HUD:

```powershell
python launcher.py hud
python launcher.py gui-web
```

Adresse: `http://127.0.0.1:8851`.

## Diagnose

```powershell
python launcher.py health
python launcher.py command-index
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py gui-bootstrap
python launcher.py gui-doctor
```

## RAG und Datenbank

```powershell
python launcher.py p1-rag-status
python launcher.py p1-embedding-status
python launcher.py p1-rag-ingest-file .\sample_docs\demo.md
python launcher.py p1-rag-hybrid-search Jarvis
python launcher.py p1-rag-answer "Was weiss Jarvis?"
python launcher.py p3-pgvector-readiness --live
```

`--apply` veraendert das konfigurierte PostgreSQL-Schema und darf nur mit gepruefter DSN und Backup verwendet werden.

## Release-Pruefung

```powershell
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

Details: [`RELEASE_WORKFLOW_v18_9.md`](RELEASE_WORKFLOW_v18_9.md).

## Fehlerbehebung

| Symptom | Pruefung |
|---|---|
| Falsche Pfade / Launcher nicht gefunden | Arbeitsverzeichnis und `python launcher.py health` pruefen |
| GUI startet nicht | `gui-bootstrap`, `gui-doctor`, belegte Ports und PID-Dateien pruefen |
| RAG nutzt lokalen Provider | `.env`/Systemvariablen und `p1-embedding-status` pruefen |
| pgvector wird uebersprungen | `SECONDBRAIN_PGVECTOR_ENABLED` und `SECONDBRAIN_PGVECTOR_DSN`/`DATABASE_URL` setzen |
| PDF/OCR fehlt | passende Extras und lokale OCR-Abhaengigkeiten installieren |
| Voice ohne Audio | Voice-Extras installieren; zuerst Textpfad und Diagnose pruefen |
| Kamera ohne Bild | MediaMTX, `stream_path`, Gateway-Ports und Kamera-Erreichbarkeit pruefen |

Secrets nie in Befehlsausgaben, Dokumentation oder Reports kopieren.
