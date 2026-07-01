# v30.34 Native Agent Control Center

## Ziel
Jarvis erhält eine native Agentensteuerung als Bindeglied zwischen Chat, Dokumenten, Memory, RAG, Command Center und deutscher Sprachsteuerung.

## Enthalten
- Agentenstatus
- deterministische Aufgabenplanung
- Task Queue
- Approval Gate für schreibende Aktionen
- Agent Activity Audit
- native Tkinter-GUI
- Launcher-Kommandos für Agentensteuerung

## Neue Kommandos
```bash
python launcher.py agent-control-status
python launcher.py agent-list
python launcher.py agent-plan "Importiere Datei test.pdf"
python launcher.py agent-task-add "Prüfe den Systemstatus"
python launcher.py agent-tasks
python launcher.py agent-task-run <task_id> --confirmed
python launcher.py agent-logs
python launcher.py agent-control-gui
```

## Runtime-Dateien
```text
runtime/native/agent_tasks.jsonl
runtime/native/agent_activity.jsonl
```
