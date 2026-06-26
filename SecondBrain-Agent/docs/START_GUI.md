# Jarvis starten ab v30.21

## Standard

```powershell
python launcher.py
```

Dieser Befehl startet automatisch den Jarvis-GUI-Bootstrap und danach die lokale Oberflaeche.

## Alternative Befehle

```powershell
python launcher.py jarvis
python launcher.py gui
python launcher.py gui-start
python launcher.py gui-open
python launcher.py gui-status
python launcher.py gui-bootstrap
python launcher.py gui-doctor
```

## Windows

Doppelklick auf:

```text
Jarvis.bat
Start-Jarvis-GUI.bat
```

Desktop-Verknuepfung erstellen:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Desktop.ps1
```

## Browser

```text
http://127.0.0.1:8851
```

## Bootstrap-Pruefungen

Der Start prueft und repariert lokal:

- `.env` Defaults
- Runtime-Ordner
- Datenordner
- Schreibrechte
- Python-Version
- `DATABASE_URL`-Format
- Embedding-Provider-Konfiguration
- Ollama-Erreichbarkeit bei Ollama-Provider
- OpenAI-Key bei OpenAI-Provider

Blocker verhindern den GUI-Start. Warnungen erlauben lokalen Start, blockieren aber weiterhin Production Gates.
