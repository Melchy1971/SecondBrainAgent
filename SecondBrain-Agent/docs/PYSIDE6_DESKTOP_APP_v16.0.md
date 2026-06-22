# SecondBrain OS v16.0 – PySide6 Desktop App

## Ziel
Erste echte Desktop-Anwendung statt reiner CLI-/Backend-Struktur.

## Enthalten
- Main Window
- Dashboard
- Chat UI
- Knowledge Explorer
- Task Board
- Notification Center
- Settings View
- CLI-Fallback
- Persistente JSON-Daten unter `data/desktop_app`

## Installation
```powershell
pip install -r requirements.txt
```

## GUI starten
```powershell
python launcher.py desktop16-gui
```

## CLI testen
```powershell
python launcher.py desktop16-status
python launcher.py desktop16-seed
python launcher.py desktop16-chat "Hallo Jarvis"
python launcher.py desktop16-knowledge-add "Jarvis Architektur" --tags jarvis,system
python launcher.py desktop16-task-add "GUI testen" --priority high
python launcher.py desktop16-notify "SecondBrain" "Desktop bereit"
```

## Grenzen
- Chat ist Echo-Modus.
- Kein echter Agentenanschluss.
- Tab-UI statt Docking Framework.
- System Tray noch nicht final.
