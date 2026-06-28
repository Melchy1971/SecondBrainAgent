# Release Notes v30.25 — Native Desktop + deutsche Sprachsteuerung

## Ergebnis

Jarvis ist nicht mehr primär eine Webanwendung. Der Standardstart öffnet eine eigenständige lokale Desktop-App.

## Neu

- Native Desktop-App auf Tkinter-Basis.
- `python launcher.py`, `python launcher.py jarvis`, `python launcher.py native-gui` starten nativ.
- Web-HUD bleibt über `python launcher.py hud` / `python launcher.py gui-web` verfügbar.
- Deutsche Sprachsteuerung als eigener Boundary-Layer.
- Textbefehle ohne Zusatzabhängigkeiten.
- Mikrofon/STT/TTS optional per Extras.
- Neue Diagnosen: `native-status`, `voice-status`, `voice-parse`.
- Windows-Startdateien auf Native Desktop umgestellt.

## Validierung

```powershell
pytest tests/test_v3025_native_desktop_voice.py -q
pytest tests/test_v3020_gui_startup_surface.py -q
python launcher.py native-status
python launcher.py voice-parse "Jarvis Status"
```

## Restrisiko

- Die App ist nativ, aber noch keine kompilierte `.exe`.
- Mikrofonsteuerung hängt von optionalen Paketen und lokalem Audiogerät ab.
- Offline-STT-Modelle müssen separat installiert/geladen werden.
- Alte Web-HUD-Funktionen sind weiter vorhanden, aber nicht mehr Hauptpfad.
