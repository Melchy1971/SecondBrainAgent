# SecondBrain OS v16.6 – Long-Term Memory

## Ziel
v16.6 ergänzt Langzeitgedächtnis als eigene Schicht.

## Memory-Typen
- Episodic Memory: Ereignisse mit Kontext, Ergebnis, Wichtigkeit
- Semantic Memory: Fakten über Entitäten
- Procedural Memory: Routinen, Schritte, Erfolgs-/Fehlerquoten

## Enthalten
- SQLite Persistence
- Memory Links
- Consolidation Runs
- Recall
- Importance Report
- Graph Export

## Befehle
```powershell
python launcher.py mem16-migrate
python launcher.py mem16-seed
python launcher.py mem16-status
python launcher.py mem16-episode-add "Turnier" "Markus spielt Tischtennis in Bietigheim" --importance 0.9
python launcher.py mem16-fact-add Jarvis status aktiv --confidence 0.8
python launcher.py mem16-procedure-add "Release entwickeln" "[\"Code\",\"Test\",\"ZIP\"]"
python launcher.py mem16-recall Jarvis
python launcher.py mem16-consolidate
python launcher.py mem16-importance
python launcher.py mem16-graph-export
```

## Grenzen
- Konsolidierung ist regelbasiert.
- Kein LLM-Memory-Compression.
- Kein automatischer Datenschutzklassifizierer.
