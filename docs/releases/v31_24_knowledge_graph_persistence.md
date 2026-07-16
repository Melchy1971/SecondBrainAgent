# v31.24 – Persistent Knowledge Graph

## Ziel

Der bereits vorhandene evidenzbasierte Knowledge Graph wird neustartfest und als verbindlicher Bestandteil des Personal-Jarvis-Release-Gates zertifiziert.

## Änderungen

- atomare, workspace-spezifische Snapshots unter `runtime/knowledge_graph/`
- Erhalt von Entitäten, Beziehungen, Evidenz, Konflikten und Merge-Historie
- Schutz gegen Path Traversal über Workspace-IDs
- Ablehnung manipulierter Snapshots mit abweichendem Workspace
- stabile öffentliche Exporte `KnowledgeGraphService` und `GraphService`
- Knowledge Graph wird im Personal-Jarvis-Gate zum kritischen Bestandteil
- zusätzlicher Roundtrip-Probe im Release-Gate

## Datenintegrität

Snapshots werden zunächst als temporäre Datei geschrieben, mit `fsync` auf den Datenträger übertragen und anschließend atomar mit `os.replace` aktiviert. Ein Prozessabbruch während des Schreibens hinterlässt daher keinen teilweise geschriebenen aktiven Snapshot.

## Sicherheit

- keine vollständigen Dokumente außerhalb des bestehenden Evidenzmodells
- strikte Workspace-Isolation
- keine Pfade aus unvalidierten Workspace-IDs
- kein automatisches Löschen von Evidenz
- bestehendes Approval-Gate für Entity-Archivierung bleibt erhalten

## Tests

```bash
pytest -q tests/test_knowledge_graph_persistence.py
pytest -q SecondBrain/knowledge_graph/tests/test_knowledge_graph.py
python scripts/personal_jarvis_gate.py --project-root .
```

## Release-Kriterium

`knowledge_graph_available` und `knowledge_graph_persistence` müssen im Personal-Jarvis-Gate beide `PASS` melden.
