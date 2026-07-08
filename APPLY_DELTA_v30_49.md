# v30.49 - Aufgaben im AI Workspace

- `AgentControlCenter` bleibt die einzige Aufgabenablage.
- Prioritaeten, Abhaengigkeiten, Erinnerungs- und Faelligkeitstermine erweitern
  das bestehende Task-Schema abwaertskompatibel.
- Agent Jobs verwenden den vorhandenen `JobQueueService`; Genehmigungen den
  vorhandenen `NativeApprovalQueue`.
- Aufgaben, Erinnerungen, Kalender, Jobs, Genehmigungen und Historie sind als
  eingebettetes Panel im AI Workspace sichtbar.
- Das bestehende Dashboard zeigt eine read-only Aufgabenkarte.

Validierung: `python -m compileall .` und `pytest`.
