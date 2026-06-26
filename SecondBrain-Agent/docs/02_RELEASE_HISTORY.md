# Release-Historie

Diese Datei fasst die Hauptlinie zusammen. Vollstaendige Release-Artefakte liegen unter `docs/releases/`.

## v14.x bis v16.x Foundation

- Persistent Personal AGI, Production Core, Service Runtime und Installer/Update Layer aufgebaut.
- Desktop App, Database Architecture, Connector Framework, Document Understanding, Multi-Agent Runtime, Knowledge Graph, Long-Term Memory, Hybrid RAG, Realtime Voice und Mobile Companion als modulare Foundations ergaenzt.

## v17.x P0 Integration

- Gemeinsamer Launcher, Module Registry, Command Index und Runtime Healthchecks etabliert.
- P0 Doctor, Smoke, Contract, Readiness, Bootstrap, Production und Audit Gate ergaenzt.
- Repository-Hygiene, Runtime-Konfigurationssnapshots und Event-Bus-Proben eingefuehrt.

## v18.x Reproducibility und P1 Start

- Packaging, Repo Doctor, Dependency Inventory und Release Workflow gehaertet.
- P1 Parser/Ingest, Embedding Health, Golden Retrieval, Provider Guards und Production Golden Gate aufgebaut.
- OpenAI/Ollama-Providergrenzen und striktes Fallback-Verhalten vorbereitet.

## v19.x P1 Store und Retrieval

- PostgreSQL/pgvector Foundation, Live Readiness, Store Interface und Store-backed Ingest ergaenzt.
- P1 Retrieval, Hybrid Gate, Maturity Candidate und Completion dokumentiert.

## v20.x bis v28.x Produktbereiche und GA-Hardening

- Memory, Agent Runtime, Connector Runtime, GUI, Voice, Mobile und weitere Produktbereiche iterativ erweitert.
- GA-Hardening und GA 1.0 Artefakte dokumentiert.

## v30.0 bis v30.5 Production Layer

- Provider Layer, PostgreSQL Production, pgvector Production, Agent Workflow Engine und Production Connectors dokumentiert.
- Export- und Test-Collection-Hardening ergaenzt.

## v30.11 bis v30.18 P1 Embedding und Vector Index

- Vector Dimension Drift Guard, Provider Health Gate und Golden Quality Gate ergaenzt.
- Embedding-Konfigurationsvertrag, Dimension Contract, HTTP Provider Boundary und Index Identity Guard eingefuehrt.
- `p1-vector-index-repair` fuer provider/model/dimension Drift ergaenzt.

## v30.19 P1 GUI Surface Update

- P1 Runtime Surface fuer Desktop Views, Settings Center, RAG Import, Vector Index und Production Gate aktualisiert.

## v30.20 GUI Startup Surface

- GUI-Startbefehle vereinheitlicht.
- `Jarvis.bat`, Shortcut-Installer und kompatible GUI-Aliase auf Launcher-Pfad ausgerichtet.

## v30.21 Unified Application Bootstrap

- `python launcher.py` startet Jarvis direkt.
- `python launcher.py jarvis` und `python launcher.py gui-bootstrap` ergaenzt.
- Bootstrap erzeugt lokale Defaults, Runtime-/Datenordner und `runtime/reports/bootstrap_v30_21.json`.
