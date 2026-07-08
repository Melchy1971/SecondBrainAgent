![Jarvis](jarvis.jpg)

# SecondBrain-Agent v30.77.0

## Version (Single Source of Truth)

Die Version wird **ausschliesslich** in `pyproject.toml` (`[project].version`) gepflegt.
Alles andere leitet sich daraus ab:

- `secondbrain/version.py` liest pyproject (Fallback: installierte Paket-Metadaten) und liefert
  `get_version()`, `get_build_number()` und `version_info()`. Die Buildnummer wird deterministisch
  aus der Version berechnet (30.77.0 -> Build 307700).
- Paket (`secondbrain.__version__`), GUI (`secondbrain.gui.version`), CLI (`secondbrain.cli.version`)
  und Launcher (`python launcher.py version`) beziehen die Version von dort.
- `python launcher.py version-sync` schreibt die abgeleiteten Anker (README-Titel,
  `docs/09_MASTERPLAN_STATUS.json`) neu. Historische `vXX`-Referenzen im Fliesstext bleiben unberuehrt.

Version anheben: nur `pyproject.toml` aendern, dann `version-sync` ausfuehren.


Lokaler Jarvis-/SecondBrain-Agent mit modularer Runtime, nativer Desktop-Oberflaeche, deutscher Sprachsteuerung, P1-RAG, Desktop-Kommandos, Voice, Knowledge Graph, Mobile Companion und Release-Gates.

## Projektwurzel

Alle Befehle laufen aus dem Projektordner:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

Wenn Befehle aus `H:\SecondBrainAgent` gestartet werden, findet Python `launcher.py`, `pytest.ini`, `pyproject.toml` und die lokalen Runtime-Pfade nicht zuverlaessig.

## Installation

Empfohlen fuer Entwicklung und lokale Ausfuehrung:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Optionale Feature-Sets:

```powershell
pip install -e ".[pdf]"
pip install -e ".[connectors]"
pip install -e ".[openai]"
pip install -e ".[all]"
```

Minimaler Installationspfad:

```powershell
python -m pip install -r requirements-dev.txt
```

## Schnellstart

```powershell
python launcher.py gui-bootstrap
python launcher.py gui-doctor
python launcher.py
```

`python launcher.py` startet seit v30.25 die native Desktop-App. Der Browser ist nicht mehr die Hauptoberflaeche.

Alternative Startbefehle:

```powershell
python launcher.py jarvis
python launcher.py native-gui
python launcher.py gui
python launcher.py gui-start
```

Web-HUD nur bei Bedarf:

```powershell
python launcher.py hud
python launcher.py gui-web
```

Nach editable install zusaetzlich:

```powershell
secondbrain health
secondbrain command-index
```

## Windows-Start

```powershell
.\Jarvis.bat
.\HUD.bat
powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Desktop.ps1
```

Die Desktop-/Startmenue-Verknuepfungen zeigen auf die native Jarvis-App. `Jarvis.bat` startet den nativen Desktop, `HUD.bat` das Web-HUD (127.0.0.1:8851).

## Pfad- und Settings-Override

Die UI-konfigurierten Pfade sind die kanonische Quelle fuer Vault- und Inbox-Aufloesung.

- `data/desktop_app/settings.json` ueberschreibt `config/settings.yaml` fuer `paths.vault` und `paths.incoming`.
- `secondbrain/path.py` kapselt die zentrale Pfadauflösung.
- Verbraucher mit `vault_path`/`incoming_path` sind auf die zentrale Aufloesung umgestellt.
- Import-Kollisionen bei `secondbrain.goal_engine` und `secondbrain.recommendations` bleiben ueber Kompatibilitaets-Wrapper stabil.

## Lokale Oberflaechen

Primaer:

```powershell
python launcher.py native-gui
```

Optionaler Web-Kompatibilitaetsmodus:

```text
http://127.0.0.1:8851
```

```powershell
python launcher.py hud
python scripts\start_hud.py
```

Einfaches lokales Dashboard:

```powershell
python scripts\web_dashboard.py
```

```text
http://localhost:8765
```


## Deutsche Sprachsteuerung

Textbefehle funktionieren direkt in der nativen App. Mikrofon/TTS sind optional.

```powershell
python launcher.py voice-status
python launcher.py voice-parse "Jarvis Status"
pip install -e ".[voice]"
```

Beispiele:

```text
Jarvis Status
Suche PostgreSQL pgvector
Frage was fehlt noch
Öffne Dokumente
Repariere Index
Importiere Datei C:\Pfad\datei.pdf
```

## Native Desktop Health (seit v30.46)

```powershell
python launcher.py native-desktop-health
python launcher.py native-desktop-doctor
python launcher.py native-desktop-report
```

Reports liegen unter `runtime/reports`.

## PostgreSQL / pgvector einrichten

Ohne `DATABASE_URL` laeuft der SQLite/RAG-Prototyp; die App startet im Status DEGRADED. Umstellung auf PostgreSQL 16 + pgvector:

1. Treiber installieren (nicht in den pyproject-Extras enthalten):

```powershell
pip install "psycopg[binary]"
```

2. Datenbank und Extension anlegen (psql oder pgAdmin):

```sql
CREATE DATABASE secondbrain;
\c secondbrain
CREATE EXTENSION IF NOT EXISTS vector;
```

Schlaegt `CREATE EXTENSION vector` fehl, ist pgvector nicht installiert. Windows-Build oder Release-Paket von https://github.com/pgvector/pgvector einspielen, dann erneut ausfuehren.

3. DSN in `.env` eintragen (Datei liegt im Projektordner, Passwort selbst einsetzen):

```text
DATABASE_URL=postgresql://postgres:PASSWORT@127.0.0.1:5432/secondbrain
```

4. Validieren und Migration ausfuehren:

```powershell
python launcher.py p3-pgvector-readiness
python launcher.py p1-rag-migrate-postgres
```

5. Jarvis neu starten. Der Dashboard-Status `database` wechselt von `degraded_sqlite` auf `ready`.

### Produktionsstatus DB/pgvector (Gate-relevant)

Die Produktionsbewertung verwendet genau diese Statuswerte:

- `ready`: PostgreSQL erreichbar, pgvector-Erweiterung vorhanden, Similarity-Smoke erfolgreich.
- `degraded_sqlite`: keine produktive PostgreSQL-Konfiguration aktiv (z. B. fehlende `DATABASE_URL` oder SQLite aktiv).
- `blocked_missing_database`: PostgreSQL erwartet, aber nicht erreichbar/ungueltig.
- `blocked_missing_pgvector`: PostgreSQL erreichbar, aber pgvector nicht produktiv validiert.

Auswirkung auf Gates:

- `p1-production` kann nur mit Status `ready` passieren.
- `degraded_sqlite` fuehrt immer zu einem blockierten Production-Gate.
- Dashboard-Karte `database` zeigt diese Statuswerte direkt als `ready`/`warning`/`blocked` mit Grund an.

## Release-Gate-Reihenfolge

Vor Featureentwicklung oder Merge:

```powershell
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py gui-bootstrap
python launcher.py gui-doctor
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

Logische Reihenfolge:

```text
repo-doctor
  -> dependency-inventory
  -> gui-bootstrap/gui-doctor
  -> p0-gate
  -> p1-gate
  -> feature-specific tests
  -> release report
```

## Aktueller Stand

Source of Truth fuer Paketstaende und Sprint-Ergebnisse:

```text
docs/releases/
docs/09_MASTERPLAN_STATUS.json
```

Aktueller dokumentierter Stand: v30.77.0 UI Path Override and Import Consolidation (Quelle: `RELEASE_NOTES.md`; strukturierter Status in `docs/09_MASTERPLAN_STATUS.json`).

Bekannte lokale Warnungen:

- Ohne `DATABASE_URL` bleibt SQLite/RAG-Prototyp aktiv.
- Der lokale deterministische Embedding-Provider erlaubt Entwicklung, blockiert aber Production-Gates.
- Live-Validierung fuer OpenAI/Ollama und PostgreSQL/pgvector bleibt umgebungsabhaengig.

## Hygiene-Gates

### Repo Doctor

```powershell
python launcher.py repo-doctor
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py repo-doctor --write-report
```

Report:

```text
release/repo_doctor_latest.json
```

### Dependency Inventory

```powershell
python launcher.py dependency-inventory
python launcher.py dependency-inventory --write-report
```

Report:

```text
release/dependency_inventory_latest.json
```

## Core-Kommandos

```powershell
python launcher.py health
python launcher.py status
python launcher.py module-status
python launcher.py module-health
python launcher.py command-index
python launcher.py core-status
```
