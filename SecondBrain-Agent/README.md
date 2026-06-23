# SecondBrain-Agent v8.0

SecondBrain OS Ausbau auf Basis v6.4.1.

## Neu in v8.0

- Semantic Search Engine
- Hybrid Search Index
- Full Knowledge Graph
- Agent Memory v2
- Project Intelligence
- Decision Intelligence v2
- Meeting Intelligence v2
- Calendar Intelligence
- Personal Data Warehouse v2
- MCP Ecosystem Registry
- Digital Twin v5
- Self-Improving Knowledge System
- SecondBrain OS Dashboard

## Start

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\menu.py
```

Wichtig: Alle Befehle in dieser README gehen davon aus, dass die PowerShell im
Projektordner `H:\SecondBrainAgent\SecondBrain-Agent` steht. Wenn Befehle aus
`H:\SecondBrainAgent` gestartet werden, findet Python `requirements.txt` und
`launcher.py` nicht.

## Schnellstart

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python -m pip install -r requirements.txt
python launcher.py health
python scripts\menu.py
```

## Web-UI / HUD

Das aktuelle Jarvis HUD ist die primäre lokale Oberfläche:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\start_hud.py
```

Browser: `http://127.0.0.1:8851`

Alternativ startet `.\Jarvis.bat` das HUD im Hintergrund und öffnet den
Browser. Stoppen: `.\Jarvis-stop.bat`.

Das einfache lokale Dashboard bleibt für schnelle Aktionen verfügbar:

```powershell
python scripts\web_dashboard.py
```

Browser: `http://localhost:8765`

## Wichtigster Lauf

```powershell
python scripts\run_secondbrain_os_cycle.py
```

## Sicherheitsmodell

- keine destruktiven Änderungen
- keine externen Aktionen ohne Aktivierung
- alle Ergebnisse als Markdown
- Markdown bleibt Source of Truth

## v10.4/v10.5 Foundation

Neu ergänzt in diesem Paket:

- `secondbrain/runtime_events_v104.py`
- `secondbrain/normalizer_v104.py`
- `secondbrain/connector_runtime_v104.py`
- `secondbrain/ai_runtime_v105.py`
- `scripts/run_v104_connector_sync.py`
- `scripts/run_v105_ai_runtime.py`
- `docs/CONNECTOR_RUNTIME_v10.4.md`
- `docs/AI_RUNTIME_v10.5.md`

Validierung:

```bash
pytest -q tests/unit/test_runtime_v104_v105.py tests/test_smoke.py
python scripts/run_v104_connector_sync.py
python scripts/run_v105_ai_runtime.py
```


## v10.7 Security & Governance
Siehe `README_v10.7_DELTA.md` und `docs/SECURITY_V10_7.md`.

## v10.8 Unified Launcher

Startpunkt:

```bash
python launcher.py health
python launcher.py init
python launcher.py start
```

Dokumentation: `docs/LAUNCHER_v10.8.md`


## v11.0 Autonomous Agent Runtime

Start:

```bash
python launcher.py agent-status
python launcher.py agent-run "Analysiere den aktuellen Stand"
```


## v11.1 Persistent Runtime

Start:

```powershell
python launcher.py up
python launcher.py status
python launcher.py gui --snapshot
```


## v11.2 Workflow & Specialist Agents

```powershell
python launcher.py workflow-status
python launcher.py workflow-run daily "Tagesbriefing erstellen"
python launcher.py research-agent "Jarvis Entwicklungsstand zusammenfassen"
python launcher.py docs-agent "Doku aktualisieren"
```


## v11.4 Voice Assistant 2.0

```powershell
python launcher.py voice-status
python launcher.py voice-parse "Jarvis status"
python launcher.py voice-handle "Jarvis notiz Neuer Gedanke"
```


## v11.5 Mobile Bridge

```powershell
python launcher.py mobile-status
python launcher.py mobile-register "iPhone Markus" ios --trusted
python launcher.py mobile-devices
```


## v11.6 API Bridge

Start: `python launcher.py api-serve`

Manifest: `python launcher.py api-manifest`

Token: `python launcher.py api-token-create "Local Dashboard" --scopes read:status,read:metrics`


## v11.7 Automation

Start: `python launcher.py automation-status`



## v11.8 Self Improvement

```powershell
python launcher.py improve-status
python launcher.py improve-feedback user command launcher -2 --text "launcher failed"
python launcher.py improve-analyze
python launcher.py improve-recommend
```


## v12.1 Core Runtime

Startstatus:

```powershell
python launcher.py core-status
python launcher.py runtime-start
python launcher.py bus-status
python launcher.py tools
```


## v12.3 Knowledge Graph

```powershell
python launcher.py graph-status
python launcher.py graph-ingest-text "Jarvis nutzt Gmail am 2026-06-19"
python launcher.py graph-search Jarvis
python launcher.py graph-neighbors Jarvis
```

## P0 Runtime Gate v17.3

```bash
python launcher.py p0-gate
python launcher.py p0-doctor
python launcher.py health
python launcher.py command-index
```

`p0-gate` ist das strikte maschinenlesbare P0-Gate. Exit-Code `0` bedeutet PASS. Exit-Code `1` bedeutet BLOCKED.

Geprüft werden Python-Version, Projektwurzel, Pflichtkonfiguration, Runtime-Schreibbarkeit, kritische Imports, kritische Runtime-Health und kritische Command-Registrierung.
