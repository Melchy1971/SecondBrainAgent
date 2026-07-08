# Delta v30.32 anwenden

## Inhalt
Native Document Explorer Center.

## Kopieren
Den Inhalt dieses ZIPs in das Repository-Root entpacken und vorhandene Dateien überschreiben.

## Prüfen
```bash
python -m pytest tests/test_v3032_native_document_explorer.py -q
python launcher.py document-explorer-status
python launcher.py document-explorer-list
```

## Start GUI
```bash
python launcher.py document-explorer-gui
```

## Wichtige Kommandos
```bash
python launcher.py document-explorer-search rechnung
python launcher.py document-explorer-preview <dateiname-oder-document-id>
python launcher.py document-explorer-tag <dateiname> projekt wichtig
python launcher.py document-explorer-import C:\\Pfad\\Datei.pdf
```
