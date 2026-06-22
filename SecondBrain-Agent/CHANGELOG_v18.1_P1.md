# SecondBrain-Agent v18.1 P1

## Schwerpunkt
P1-RAG-Härtung: Quelleninventar, Explainability, Metadaten und Gate-Schema v2.

## Änderungen
- `p1-rag-sources` ergänzt.
- `p1-rag-explain` ergänzt.
- Chunk-Schema um `char_start` und `char_end` erweitert.
- Source-Validation ergänzt.
- Antwort-/Suchtreffer um deterministische Snippets ergänzt.
- `p1-gate` auf Schema `secondbrain.p1_gate.v2` gehoben.
- Gate prüft jetzt Datenbank, Schema, Quelleninventar und Explainability.
- Tests erweitert.

## Validierung
- `p1-rag-sources`: PASS
- `p1-rag-explain`: PASS
- `p1-gate --write-report`: PASS
- `pytest`: 258 passed
