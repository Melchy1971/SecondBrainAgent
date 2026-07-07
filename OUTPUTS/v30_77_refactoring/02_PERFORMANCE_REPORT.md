# Performance Report — SecondBrain-Agent v30.77
Stand: 2026-07-07 | Hinweis: In der Linux-Sandbox ohne Projekt-`.venv` und ohne `runtime/`-Daten ist **kein belastbares Laufzeit-Profiling** möglich. Folgende Punkte sind statisch/strukturell hergeleitet und auf der Windows-Maschine zu messen.

## 1. Import-/Startkosten
- **17-gliedrige Import-Kette** `launcher_runtime_v108 → … → v126`. Jeder Start zieht potenziell die gesamte Kette inkl. `legacy_main`-Delegationen. Anforderung: Startzeit mit `python -X importtime launcher.py` messen; Kette ist der erste Verdächtige.
- `launcher.py` importiert beim Start direkt ≥12 `p0_/p1_/p3_`-Runtime-Module (Gates, RAG-Runtime, Store-Bridges). Kandidat für Lazy-Import (Import erst bei Bedarf).
- 1095 Module im Paket; `__init__.py`-Re-Exports ziehen bei Paket-Import Transitivlasten. Anforderung: schwergewichtige Re-Exports in `__init__` prüfen.

## 2. Mess-Auftrag (auf Windows auszuführen)
1. `python -X importtime -c "import secondbrain" 2> importtime.log` → Top-20 teuerste Module.
2. `python -X importtime launcher.py --help 2> launcher_importtime.log`.
3. RAG-Pfad (`p1_rag_runtime`, `advanced_rag_v109`, `rag/*`) unter Last messen — hier liegen die rechenintensiven Pfade (Embedding-Pipelines, `async_batch_embedding_pipeline`, `vector_store_pgvector`).

## 3. Strukturelle Optimierungshebel
- Kette v108–v126 zusammenführen: reduziert Importtiefe und Objektaufbau beim Start.
- Lazy-Import für Gate-/RAG-Module in `launcher.py`.
- Dynamische Registry-Scans (`module_registry`, Connector-Discovery) cachen statt bei jedem Start neu zu scannen.
- `benchmark_suite`-Module (7 Stück, u.a. `rag`, `agent`, `mobile`, `voice`) existieren bereits — als Grundlage für reproduzierbare Messläufe nutzen, nicht wegwerfen.

## 4. Nicht belegbar in dieser Umgebung
Laufzeit-CPU/RAM, DB-Query-Latenzen (pgvector), GUI-Rendering. Diese Zahlen sind ausschließlich am Live-System valide und hier bewusst **nicht geschätzt**.
