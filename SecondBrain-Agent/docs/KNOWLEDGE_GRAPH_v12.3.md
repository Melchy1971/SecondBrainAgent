# Knowledge Graph v12.3

## Commands

```powershell
python launcher.py graph-status
python launcher.py graph-ingest-text "Jarvis nutzt Gmail am 2026-06-19" --source-id demo
python launcher.py graph-search Jarvis
python launcher.py graph-neighbors Jarvis
python launcher.py graph-timeline
python launcher.py graph-contradictions
```

## Data Flow

Text/File -> Entity Extraction -> Relationship Discovery -> Timeline -> Contradiction Detection -> Event Bus.

## Storage

`runtime/knowledge_graph_v123/` contains entities, relationships, timeline events and contradictions.
