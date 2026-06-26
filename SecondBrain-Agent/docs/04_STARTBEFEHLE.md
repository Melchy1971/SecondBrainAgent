# Startbefehle v30.21

## Voraussetzung

Alle Befehle aus dem Projektordner ausfuehren:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

Empfohlene Installation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Jarvis starten

Standard ab v30.21:

```powershell
python launcher.py
```

Explizite GUI-Befehle:

```powershell
python launcher.py jarvis
python launcher.py gui
python launcher.py gui-start
python launcher.py gui-open
python launcher.py gui-status
python launcher.py gui-doctor
python launcher.py gui-bootstrap
python launcher.py gui-shortcuts
```

Browser:

```text
http://127.0.0.1:8851
```

## Windows

```powershell
.\Jarvis.bat
.\Start-Jarvis-GUI.bat
powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Desktop.ps1
```

## Hygiene und Gates

```powershell
python launcher.py health
python launcher.py command-index
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

## P1 RAG

```powershell
python launcher.py p1-rag-status
python launcher.py p1-rag-ingest-file .\sample_docs\demo.md
python launcher.py p1-rag-search Jarvis
python launcher.py p1-rag-vector-search Jarvis
python launcher.py p1-rag-hybrid-search Jarvis
python launcher.py p1-rag-answer "Was weiss Jarvis?"
python launcher.py p1-vector-provider-audit
python launcher.py p1-vector-index-repair
python launcher.py p1-provider-health
python launcher.py p1-golden-eval
python launcher.py p1-production
```

## Desktop-Kommandos

```powershell
python launcher.py desktop-status
python launcher.py desktop-dashboard
python launcher.py desktop-activity
python launcher.py desktop-widgets
python launcher.py desktop-commands
python launcher.py desktop-notifications
python launcher.py desktop-session
python launcher.py desktop-notify "Test" --body "Nachricht" --level info
```

## Voice

```powershell
python launcher.py voice-status2
python launcher.py voice-session2
python launcher.py voice-wake "Jarvis status"
python launcher.py voice-parse2 "Jarvis notiz Neuer Gedanke"
python launcher.py voice-handle2 "Jarvis status"
```

## Knowledge Graph

```powershell
python launcher.py graph-status
python launcher.py graph-ingest-text "Jarvis nutzt RAG"
python launcher.py graph-search Jarvis
python launcher.py graph-neighbors Jarvis
python launcher.py graph-timeline
```

## Mobile Companion

```powershell
python launcher.py mobile16-status
python launcher.py mobile16-manifest
python launcher.py mobile16-pair-request "iPhone Markus" ios
python launcher.py mobile16-devices
python launcher.py mobile16-sync
```
