# SecondBrain OS v13.4 – Knowledge Intelligence

## Ziel
v13.4 erweitert den Wissensgraphen zu einer Knowledge-Intelligence-Schicht.

## Komponenten
- Entity Extraction
- Entity Resolution
- Relationship Discovery
- Timeline Analytics
- Semantic Clustering
- Contradiction Detection
- JSON Graph Store
- Neo4j-ready Export

## Befehle
```powershell
python launcher.py ki13-status
python launcher.py ki13-ingest "Jarvis nutzt Gmail und GitHub für SecondBrain."
python launcher.py ki13-entities
python launcher.py ki13-relationships
python launcher.py ki13-neighbors Jarvis
python launcher.py ki13-timeline
python launcher.py ki13-clusters
python launcher.py ki13-claims "Jarvis ist aktiv"
python launcher.py ki13-claims "Jarvis ist nicht aktiv"
python launcher.py ki13-contradictions
python launcher.py ki13-export
```

## Grenzen
- Kein echter Neo4j-Treiber in diesem Paket.
- Entity Extraction ist regelbasiert.
- Semantik ist deterministisch und lokal.
