# v30.30 Native Workspace Center

Ziel: eine zentrale native Arbeitsoberfläche zwischen Chat, Dokumenten, Suche, Memory, Aufgaben, Agenten, Aktivitäten und Einstellungen.

## Neue Befehle

```bash
python launcher.py workspace
python launcher.py workspace-status
python launcher.py workspace-activity
python launcher.py workspace-open documents
python launcher.py workspace-log "Import geprüft" --section documents --kind note
```

## Runtime-Datei

```text
runtime/native/activity_log.jsonl
```

## Abgrenzung

Web-HUD bleibt sekundär. v30.30 führt die native Workspace-Oberfläche ein, ersetzt aber noch keinen vollständigen Installer und keinen produktiven Agent-Planner.
