# Installation v30.25 fuer Einsteiger

## 1. Projektordner oeffnen

PowerShell oeffnen und in den Agent-Ordner wechseln:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

Wichtig: Nicht in `H:\SecondBrainAgent` bleiben. `launcher.py`, `pytest.ini`, `pyproject.toml` und die Startskripte liegen im Unterordner `SecondBrain-Agent`.

## 2. Python-Umgebung anlegen

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Falls editable install nicht benoetigt wird:

```powershell
python -m pip install -r requirements-dev.txt
```

## 3. Jarvis vorbereiten

```powershell
python launcher.py gui-bootstrap
```

Der Bootstrap prueft Python, `.env`, Runtime-Ordner, Schreibrechte, Datenbank-URL und Embedding-Provider. Warnungen erlauben lokalen Start, blockieren aber weiterhin produktive Gates.

## 4. Diagnose ausfuehren

```powershell
python launcher.py gui-doctor
python launcher.py health
```

## 5. Jarvis starten

Standard:

```powershell
python launcher.py
```

Alternativen:

```powershell
python launcher.py jarvis
python launcher.py gui
.\Jarvis.bat
.\Start-Jarvis-GUI.bat
```

Browser:

```text
http://127.0.0.1:8851
```

## 6. Desktop-Verknuepfung erstellen

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Desktop.ps1
```

## 7. Relevante Checks vor Aenderungen

```powershell
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

## 8. Import testen

Dateien in passende Inbox-Ordner legen:

```text
H:\SecondBrainAgent\SecondBrain-Inbox\PDFs
H:\SecondBrainAgent\SecondBrain-Inbox\Webseiten
H:\SecondBrainAgent\SecondBrain-Inbox\ChatGPT
```

Danach gezielt den passenden Importer oder RAG-Ingest ausfuehren, z. B.:

```powershell
python launcher.py p1-rag-ingest-file .\sample_docs\demo.md
python launcher.py p1-rag-search Jarvis
```


# v30.25 Native Desktop Start

Jarvis wird jetzt als eigenständige Desktop-App gestartet:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python launcher.py
```

Alternativen:

```powershell
python launcher.py jarvis
python launcher.py native-gui
.\Jarvis.bat
.\Start-Jarvis-Native.bat
```

Das alte Web-HUD ist nur noch Kompatibilitätsmodus:

```powershell
python launcher.py hud
```

## Deutsche Sprachsteuerung

Textbefehle funktionieren direkt in der Desktop-App. Für Mikrofonsteuerung:

```powershell
pip install -e ".[voice]"
python launcher.py voice-status
```

Beispiele:

```text
Jarvis Status
Suche Vertrag PostgreSQL
Frage was fehlt noch
Öffne Dokumente
Repariere Index
```
