# APPLY DELTA v30.72

## Umfang

- Bestehenden `SemanticExplorerService` auf Version 30.72 erweitern.
- Entity-, Relationship-, Project-, People-, Timeline- und Evidence-Graph als read-only Projektionen bereitstellen.
- Gewichtete Graph Search und die bestehende Graph-Explorer-Integration im AI Workspace verwenden.
- Keine Tabelle, kein Index und keine zweite Graph-Datenhaltung anlegen.

## Datenfluss

`RAG documents/chunks + Memory entries -> SemanticExplorerService -> Graph Views/Search -> AI Workspace`

Timeline-Knoten werden aus vorhandenen Zeitstempeln abgeleitet. Evidence-Knoten referenzieren vorhandene RAG-Chunks und Memory-Eintraege.

## Pruefung

```powershell
python -m compileall .
pytest -q
```
