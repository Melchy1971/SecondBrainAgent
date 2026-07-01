# APPLY DELTA v30.27 — Native Action Bridge

## Dateien kopieren

Kopiere die Delta-Dateien in dein Repository und überschreibe vorhandene Dateien.

## Danach ausführen

```bash
python launcher.py gui-bootstrap
pytest tests/test_v3027_native_action_bridge.py -q
python launcher.py voice-parse "Jarvis Status"
python launcher.py voice-run "Öffne Dokumente" --dry-run
python launcher.py native-action "Repariere Index" --dry-run
```

## Start

```bash
python launcher.py
```

oder per Windows:

```text
Jarvis.bat
```

## Ergebnis

Die native GUI bleibt Primärstart. Deutsche Sprachbefehle sind jetzt mit einer Action Bridge verbunden. Schreibende Aktionen laufen nicht ohne Bestätigung.
