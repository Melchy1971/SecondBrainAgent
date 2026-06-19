# SecondBrain OS v11.2 – Workflow & Specialist Agents

## Ziel

v11.2 ergänzt eine deterministische Workflow Engine und erste Specialist Agents. Die Ausführung bleibt auditierbar: jeder Schritt läuft über `ToolHost`, persistiert Status und schreibt Ergebnisse in den Runtime Store.

## Neue Befehle

```powershell
python launcher.py workflow-status
python launcher.py workflow-run daily "Erstelle mein Tagesbriefing"
python launcher.py workflow-run project "Prüfe Jarvis v11.2"
python launcher.py email-agent "Fasse wichtige E-Mails zusammen"
python launcher.py calendar-agent "Plane meinen Tag"
python launcher.py research-agent "Recherchiere den aktuellen SecondBrain Stand"
python launcher.py docs-agent "Aktualisiere die Entwicklungsdokumentation"
```

## Architektur

```text
Launcher
↓
Workflow Engine
↓
ToolHost
↓
Connectors / RAG / AI / Desktop Commands
↓
Runtime Store + Event Log
```

## Specialist Agents

- Email Agent: Connector Sync → Mail-Kontextsuche → Brief → Capture
- Calendar Agent: Connector Sync → Kalender-Kontext → Planung → Capture
- Research Agent: RAG Search → RAG Answer → Critique → Capture
- Documentation Agent: Statussuche → Dokumentationsentwurf → Capture

## Sicherheitsgrenze

Keine automatischen E-Mails, keine Kalendereinträge, keine Systembefehle. v11.2 arbeitet read/compose-orientiert. Schreibende Aktionen bleiben Quick-Capture im lokalen Vault.
