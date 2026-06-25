# v30.18 — P1 Vector Index Repair

## Ziel

Provider-, Modell- oder Dimensionswechsel dürfen keinen still teilkaputten Vektorindex erzeugen. Der Index muss messbar driftfrei sein oder deterministisch repariert werden.

## Änderungen

- Vector Provider Audit vergleicht jetzt gegen die volle Index-Identität `provider:model:dimension`.
- Neuer Befehl `p1-vector-index-repair`.
- Repair führt bei `stale_vector_provider`, `missing_vectors` oder `dimension_mismatch_vectors` einen Reindex mit dem aktuellen Provider aus.
- Orphan-/Strukturfehler bleiben harte Blocker und werden nicht verdeckt.
- Launcher und ModuleRegistry kennen den neuen Befehl.

## Befehle

```bash
python launcher.py p1-vector-provider-audit --write-report
python launcher.py p1-vector-index-repair --write-report
python launcher.py p1-rag-vector-search "Jarvis memory" --limit 5
```

## Akzeptanz

- Modell-/Dimensionswechsel erzeugt Audit-Blocker.
- `p1-vector-index-repair` repariert den Index per Reindex.
- Nach Repair ist `stale_vectors = 0` und `dimension_mismatch_vectors = 0`.
- Orphan-Vectors bleiben blockierend.
