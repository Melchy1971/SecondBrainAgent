# PATCH P2.1.1 — Desktop Foundation

## Ziel
Desktop-Grundstruktur als testbare Applikationsschicht einführen.

## Enthalten
- `secondbrain/desktop/app.py`
- `secondbrain/desktop/shell.py`
- `secondbrain/desktop/state.py`
- `secondbrain/desktop/events.py`
- `secondbrain/desktop/router.py`
- `secondbrain/desktop/commands.py`
- `secondbrain/desktop/notifications.py`
- `secondbrain/desktop/status_service.py`
- `secondbrain/desktop/workspace_manager.py`
- Tests unter `tests/desktop/`

## Ergebnis
- Persistenter Desktop-State
- Event-Bus
- Router
- Command Palette
- Notification Center
- Status-Service
- Workspace Manager
- App-Bootstrap

## Validierung
`12 passed in 0.34s`
