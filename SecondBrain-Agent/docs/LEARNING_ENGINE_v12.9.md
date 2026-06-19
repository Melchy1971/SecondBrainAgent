# SecondBrain OS v12.9 – Learning Engine

## Ziel
v12.9 erzeugt eine kontrollierte Lernschicht aus beobachteten Erfahrungen.

## Komponenten
- Experience Store
- Episode Memory
- Skill Metrics
- Failure Pattern Learning
- Success Pattern Learning
- Reflection Engine
- Learning Backlog

## Befehle
```powershell
python launcher.py learn-status
python launcher.py learn-experience "RAG Antwort" "Antwort korrekt" --success --capability rag --duration 2.1
python launcher.py learn-experience "Connector Sync" "Timeout" --capability connector --error timeout
python launcher.py learn-metrics
python launcher.py learn-reflect
python launcher.py learn-backlog-create
python launcher.py learn-backlog
python launcher.py learn-episode "Sprint Review" "Connector-Probleme erkannt"
```

## Entscheidungslogik
- Success Rate pro Capability
- wiederholte Fehlercluster
- priorisierte Verbesserungen
- Backlog-Einträge nur als Vorschlag, keine automatische Codeänderung

## Grenzen
Keine selbstständige Codeänderung.
Keine Policy-Änderung ohne Approval.
Keine Autonomie-Eskalation ohne Governance.
