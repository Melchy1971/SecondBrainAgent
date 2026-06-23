# PATCH P3.1.5 — Background Agent Jobs

## Inhalt
- AgentJob-Datenmodell mit Status, Fortschritt, Attempts, Ergebnis und Fehlerpfad
- AgentJobQueue für deterministische FIFO-Ausführung
- AgentJobRunner mit Retry-Policy und Event-Auslösung
- AgentJobManager als Fassade für Submit, Run, Cancel und Snapshot
- AgentJobHistory mit optionaler JSON-Persistenz
- AgentJobEventBus mit Lifecycle-Events

## Validierung
- `6 passed in 0.23s`

## Risiko reduziert
- Agent-Pläne laufen nicht mehr nur synchron/ad hoc.
- Hintergrundausführung erhält Status, Historie, Retry und Cancel-Pfade.
- Desktop-/Job-Center kann Agent-Jobs über Snapshots integrieren.
