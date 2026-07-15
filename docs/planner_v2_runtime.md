# Planner-v2-Laufzeit v31.16

Planner v2 modelliert Plaene als validierte DAGs. Vor der Ausfuehrung prueft der Service Abhaengigkeiten, Zyklen, Tools, Scopes, Workspace-Grenzen, Risiken, Approvals, Retry-Sicherheit und Budgets. Simulationen fuehren keine Tools aus.

## Ausfuehrungsregeln

- Topologische Ebenen bestimmen, welche Knoten unabhaengig sind.
- Sichere Knoten derselben Ebene laufen bis `max_parallelism` parallel.
- Approval-pflichtige und in `unsafe_tools` konfigurierte Knoten laufen seriell.
- `resource_locks` serialisieren Knoten, die dieselbe Datei, denselben Workspace oder denselben Connector veraendern.
- Ressourcen-Locks werden sortiert erworben, um Lock-Order-Deadlocks zu vermeiden.
- Audit-Schreibvorgaenge sind threadsicher; Ergebnislisten und Checkpoints bleiben in Planreihenfolge deterministisch.

## Fehler und Recovery

Alle bereits gestarteten Geschwister einer parallelen Ebene werden ausgewertet. Erfolgreiche Knoten gelangen auch dann in den Checkpoint, wenn ein Geschwister fehlschlaegt. Danach wechselt der Plan zu `recovery_required`. Resume und Recovery ueberspringen abgeschlossene Checkpoints. Nicht idempotente sowie Send-/Delete-/Forward-/Publish-Schritte werden nicht unsicher wiederholt.

## Integrationsgrenzen

Tool-Adapter muessen fuer Parallelbetrieb threadsicher sein und alle gemeinsam veraenderten Ressourcen deklarieren. Die Runtime erzwingt keine automatische Ableitung von Ressourcen aus beliebigen Tool-Inputs. Prozessuebergreifende Sperren und ein laufender Abbruch-Token sind nicht Bestandteil dieses lokalen Thread-Executors.
