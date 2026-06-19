# SecondBrain OS v11.1 – Persistent Runtime & Desktop GUI

## Ziel

v11.1 verbindet Launcher, Agent Runtime, RAG, Connectors, Monitoring und Desktop-Bedienung zu einer persistenten Runtime.

## Neue Befehle

```powershell
python launcher.py up
python launcher.py status
python launcher.py metrics
python launcher.py diagnose
python launcher.py gui --snapshot
python launcher.py gui
python launcher.py restart
python launcher.py down
python launcher.py recover
```

## Startprofil

`up` startet Services in Abhängigkeitsreihenfolge:

```text
eventbus -> connectors -> rag -> ai -> agent -> monitoring -> desktop_commands
```

## Persistenz

```text
runtime/state/services.json
runtime/state/session_current.json
runtime/state/activity.json
runtime/dashboard_snapshot.json
```

## GUI

`python launcher.py gui` startet ein kleines Tk-Dashboard.

In headless Umgebungen wird automatisch ein Dashboard-Snapshot geschrieben.

## Grenzen

- Kein echter Windows-Service.
- Kein Autostart nach Reboot.
- Keine Hintergrundprozesse außerhalb des aktuellen Python-Prozesses.
- GUI ist Foundation, nicht finale Produktoberfläche.

## Nächste Version

v11.2: Workflow Engine + spezialisierte Agenten für E-Mail, Kalender, Research und Dokumentation.
