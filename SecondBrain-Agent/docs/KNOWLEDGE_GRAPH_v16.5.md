# SecondBrain OS v16.5 – Knowledge Graph

## Ziel
v16.5 ergänzt eine echte Graph-Schicht als SQLite-Backend mit Neo4j-Export.

## Enthalten
- Nodes
- Edges
- Graph Events
- Neighbor Queries
- Shortest Path
- Community Detection
- Timeline
- Neo4j Cypher Export

## Befehle
```powershell
python launcher.py kg16-migrate
python launcher.py kg16-seed
python launcher.py kg16-status
python launcher.py kg16-node-add Jarvis --kind system
python launcher.py kg16-edge-add Jarvis SecondBrain --type powers
python launcher.py kg16-neighbors Jarvis
python launcher.py kg16-path Jarvis Gmail
python launcher.py kg16-communities
python launcher.py kg16-event-add "Release v16.5" --type release --node Jarvis
python launcher.py kg16-timeline --node Jarvis
python launcher.py kg16-export-neo4j
```

## Grenzen
- Kein echter Neo4j-Treiber.
- Community Detection ist connected-components-basiert.
- Keine Embeddings im Graph.
