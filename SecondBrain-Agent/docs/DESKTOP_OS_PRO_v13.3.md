# SecondBrain OS v13.3 – Desktop OS Pro

## Ziel
v13.3 liefert die produktnahe Desktop-Backend-Struktur für eine spätere PySide6-Anwendung.

## Komponenten
- Dock Layout Manager
- Command Palette
- Knowledge Explorer
- Memory Explorer
- Kanban Board
- Project Center
- PySide6-ready Runtime Backend

## Befehle
```powershell
python launcher.py desktop13-status
python launcher.py desktop13-layout
python launcher.py desktop13-window kanban true
python launcher.py desktop13-commands
python launcher.py desktop13-command-search dashboard
python launcher.py desktop13-command open_dashboard
python launcher.py desktop13-knowledge-add "Jarvis Architektur" --tags jarvis,system
python launcher.py desktop13-knowledge-search jarvis
python launcher.py desktop13-memory-add "Neue Erinnerung"
python launcher.py desktop13-kanban-add "GUI bauen"
python launcher.py desktop13-project-add "Desktop OS Pro" --risk high
```

## Grenzen
- Keine echte PySide6 UI in diesem Paket.
- Backend ist GUI-fähig, aber UI-Rendering folgt separat.
