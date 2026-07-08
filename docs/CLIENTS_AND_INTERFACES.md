# Clients und Oberflaechen

## Native Desktop

Seit v30.25 ist die native Desktop-App der Standard.

```powershell
python launcher.py
python launcher.py native-gui
python launcher.py native-status
```

Bereiche: Dashboard, Assistant, Documents, Memory, Search, Imports, Production, Settings, Voice und Developer.

Schreibende Aktionen wie Dateiimport oder Indexreparatur verlangen eine Bestaetigung. Mikrofon und TTS sind optionale Abhaengigkeiten.

## Web-HUD

```powershell
python launcher.py hud
python launcher.py gui-web
python scripts\start_hud.py
```

Adresse: `http://127.0.0.1:8851`.

Das HUD stellt lokale Status-, RAG-, Dokument-, Memory-, Connector-, Agent-, Settings- und Security-Endpunkte bereit. Es ist kein fuer das Internet gehaerteter Remote-Dienst.

Relevante Dateien:

- `secondbrain/hud_core.py`
- `secondbrain/jarvis_hud_server.py`
- `web/jarvis_hud/index.html`
- `scripts/start_hud.py`

## Voice

Die native App unterstuetzt deutsche Textkommandos. Die erweiterte Audio-Pipeline ist in [`VOICE_CONTROL_v20.md`](VOICE_CONTROL_v20.md) beschrieben.

```powershell
python launcher.py voice-status
python launcher.py voice-parse "Jarvis Status"
python launcher.py voice-status2
python launcher.py voice-handle2 "Jarvis zeige Status"
```

## Mobile Backend

```powershell
python launcher.py mobile16-status
python launcher.py mobile16-manifest
python launcher.py mobile16-pair-request "iPhone Markus" ios
python launcher.py mobile16-devices
python launcher.py mobile16-sync
```

Pairing, Offline Queue, Voice Notes, Push Outbox, Widgets und Sessions sind Backend-Foundations. Native App, echte Push-Zustellung, OCR-Abnahme und Konflikt-Merge fehlen.

## Windows-Integration

```powershell
.\Jarvis.bat
.\HUD.bat
powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Desktop.ps1
```

Startskripte sind Komfortoberflaechen. Diagnose und Fehleranalyse erfolgen weiterhin ueber den Launcher.
