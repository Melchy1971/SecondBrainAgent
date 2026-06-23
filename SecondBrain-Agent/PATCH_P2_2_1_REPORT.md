# Patch P2.2.1 – Dashboard V2 Foundation

## Inhalt

- `secondbrain.desktop.dashboard` Package eingeführt
- Dashboard-Service mit Default-Widgets
- Widget-Registry mit Duplicate-/ID-Validierung
- Widget-Manager mit Fehlerisolation pro Widget
- Refresh-Scheduler mit Intervallprüfung
- Persistenz für Dashboard-State und Widget-Snapshots
- Dashboard-Eventlog für Load/Save/Refresh/Failure

## Standard-Widgets

- Recent Imports
- Running Jobs
- Connector Health
- RAG Status
- System Health
- Storage Usage
- Recent Errors
- Workspace Summary

## Validierung

```text
10 passed
```

## Nächster Schritt

P2.2.2 Dashboard Widgets: echte Datenadapter für Jobs, Connector Health, RAG Status, System Health und Errors.
