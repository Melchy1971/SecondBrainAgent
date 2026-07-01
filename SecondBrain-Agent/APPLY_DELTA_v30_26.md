# Delta v30.26 anwenden

## Inhalt

Dieses Delta konsolidiert Jarvis als eigenständige Desktop-Anwendung mit deutscher Sprachsteuerung.

## Kopieren

Alle Dateien aus dem ZIP in das Projektverzeichnis `SecondBrain-Agent` kopieren und bestehende Dateien überschreiben.

## Start

```bash
python launcher.py
```

Alternativen:

```bash
python launcher.py jarvis
python launcher.py native-gui
Jarvis.bat
```

## Web-HUD nur noch sekundär

```bash
python launcher.py hud
python launcher.py gui-web
```

## Sprachbefehl testen

```bash
python launcher.py voice-parse "Jarvis Status"
python launcher.py voice-parse "Öffne Dokumente"
python launcher.py voice-parse "Repariere Index"
```

## Validierung

```bash
pytest tests/test_v3026_native_desktop_consolidation.py -q
python launcher.py native-status
```
