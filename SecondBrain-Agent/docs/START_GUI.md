# Jarvis starten ab v30.21

## Standard

```bash
python launcher.py
```

Dieser Befehl startet automatisch den Jarvis-GUI-Bootstrap und danach die Oberfläche.

## Alternative Befehle

```bash
python launcher.py jarvis
python launcher.py gui
python launcher.py gui-bootstrap
python launcher.py gui-doctor
```

## Windows

Doppelklick auf:

```text
Jarvis.bat
Start-Jarvis-GUI.bat
```

Desktop-Verknüpfung erstellen:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Desktop.ps1
```

## Bootstrap-Prüfungen

Der Start prüft und repariert lokal:

- `.env` Defaults
- Runtime-Ordner
- Schreibrechte
- Python-Version
- DATABASE_URL-Format
- Embedding-Provider-Konfiguration
- Ollama-Erreichbarkeit bei Ollama-Provider
- OpenAI-Key bei OpenAI-Provider

Blocker verhindern den GUI-Start. Warnungen erlauben lokalen Start, blockieren aber weiterhin Production Gates.
