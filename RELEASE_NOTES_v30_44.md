# v30.44 – Native Job & Queue Center

## Neu
- Persistente native Job Queue unter `runtime/native/job_queue/jobs.jsonl`
- Job History unter `runtime/native/job_queue/job_history.jsonl`
- Approval-gated Jobs starten blockiert und müssen freigegeben werden
- Native Tkinter-GUI für Queue-Überwachung
- CLI für Status, Liste, Freigabe, Start, Abbruch und Cleanup

## Nutzen
- Imports, Reindex, Agent Tasks, Voice Actions und Updates werden in einer zentralen Oberfläche sichtbar.
- Schreibende Aktionen bleiben kontrolliert.
- GUI und Sprachsteuerung erhalten eine gemeinsame Queue-Wahrheit.
