# APPLY DELTA v30.25 — Native Desktop + deutsche Sprachsteuerung

Ziel: Jarvis nicht mehr als Webanwendung starten, sondern als eigenständiges lokales Desktop-Tool. Das Web-HUD bleibt nur als Kompatibilitätsmodus erhalten.

## Einspielen

ZIP in die Projektwurzel `SecondBrain-Agent` entpacken und vorhandene Dateien überschreiben.

## Neuer Primärstart

```powershell
python launcher.py
python launcher.py jarvis
python launcher.py native-gui
.\Jarvis.bat
.\Start-Jarvis-Native.bat
```

## Web-HUD nur noch optional

```powershell
python launcher.py hud
python launcher.py gui-web
.\Start-Jarvis-WebHUD.bat
```

## Deutsche Sprachsteuerung

Textbefehle funktionieren ohne Zusatzpakete direkt im nativen Fenster.

Beispiele:

```text
Jarvis Status
Suche PostgreSQL pgvector
Frage was fehlt noch
Öffne Dokumente
Öffne Einstellungen
Repariere Index
Importiere Datei C:\Pfad\datei.pdf
```

Mikrofon/STT ist optional:

```powershell
pip install -e ".[voice]"
```

Offline-STT optional:

```powershell
pip install -e ".[voice-offline]"
```

## Diagnose

```powershell
python launcher.py native-status
python launcher.py voice-status
python launcher.py voice-parse "Jarvis Status"
python launcher.py gui-doctor
```

## Validierung

```powershell
pytest tests/test_v3025_native_desktop_voice.py -q
pytest tests/test_v3020_gui_startup_surface.py -q
```

## Architekturentscheidung

- Primäre UI: native Tkinter Desktop-App, Standardbibliothek, keine Browserpflicht.
- Legacy UI: Web-HUD bleibt erhalten, aber nicht mehr Hauptpfad.
- Sprachschicht: Deutsch zuerst; Mikrofon/TTS optional; Text-Kommandos immer verfügbar.
