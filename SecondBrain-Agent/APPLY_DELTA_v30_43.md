# APPLY DELTA v30.43 - Native Notification Center

## Inhalt
- `secondbrain/native/notification_center/`
- Launcher-Kommandos für Benachrichtigungen
- AI-Workspace-Navigation: `Benachrichtigungen`
- Tests: `tests/test_v3043_native_notification_center.py`

## Anwendung
ZIP im Projektroot entpacken. Bestehende Dateien überschreiben.

## Prüfung
```bash
python -m compileall secondbrain/native/notification_center secondbrain/native/ai_workspace launcher.py
pytest tests/test_v3043_native_notification_center.py -q
python launcher.py notification-center-status
```

## Neue Kommandos
```bash
python launcher.py notification-center-status
python launcher.py notification-list
python launcher.py notification-send "Titel" "Nachricht" --level warning
python launcher.py notification-read <id>
python launcher.py notification-read-all
python launcher.py notification-clear
python launcher.py notification-center-gui
```
