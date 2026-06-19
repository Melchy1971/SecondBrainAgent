
# Desktop OS v12.5

v12.5 ergänzt eine Desktop-fähige Betriebsschicht ohne harte GUI-Abhängigkeit. Die Architektur ist PySide6-kompatibel, aber auch headless über `launcher.py` nutzbar.

## Start
```powershell
python launcher.py desktop-status
python launcher.py desktop-open --view dashboard
python launcher.py desktop-dashboard
```

## Komponenten
- DesktopOSKernel
- DashboardBackend
- WidgetRegistry
- NotificationCenter
- CommandPalette
- DesktopSessionManager

## Daten
```text
data/runtime/desktop_v125/
├── widgets.json
├── notifications.json
└── session.json
```

## Ziel
Die spätere PySide6-App ruft diese Backends direkt auf. Dadurch bleibt GUI austauschbar und testbar.
