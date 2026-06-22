# Release-Historie

## v14.0 – Persistent Personal AGI
- Persistent Personal AGI Runtime
- Governance Policy
- Observe → Think → Plan → Act → Verify → Learn
- Proactive Assistant
- Self Optimizer

## v15.0 – Production Core
- Service Foundation
- Watchdog
- Secrets Vault Scaffold
- Audit Trail
- Approval Workflow
- Backup / Restore Plan

## v15.1 – Service Runtime
- Service Runner
- JSON Logs
- Health / Ready / Metrics
- HTTP Health Server
- pywin32 / NSSM Scaffold

## v15.2 – Installer & Update
- Release Manifest
- Config Validator
- Portable Installer Plan
- Backup before Update
- Rollback Plan

## v16.0 – PySide6 Desktop App
- Main Window
- Dashboard
- Chat UI
- Knowledge Explorer
- Task Board
- Notifications
- Settings

## v16.1 – Database Architecture
- SQLite Persistence
- PostgreSQL-ready Schema
- Memories, Tasks, Documents, Events, Automations, Embeddings
- Migration Runner

## v16.2 – Connector Framework
- Gmail, Google Calendar, Google Drive, GitHub, Obsidian, Paperless Registry
- Delta Cursor
- Sync Runs
- Connector Items
- Dead Letter Queue

## v16.3 – Document Understanding
- TXT/Markdown/EML Ingestion
- DOCX XML Reader
- XLSX/PPTX Scaffold
- PDF Stub
- Chunking
- Citations
- Entity Extraction

## v16.4 – Multi-Agent Runtime
- Supervisor
- Planner
- Research
- Execution
- Review
- Memory
- Improvement Agent

## v16.5 – Knowledge Graph
- Nodes / Edges
- Neighbors
- Shortest Path
- Communities
- Timeline
- Neo4j Cypher Export

## v16.6 – Long-Term Memory
- Episodic Memory
- Semantic Memory
- Procedural Memory
- Memory Links
- Consolidation
- Recall

## v16.7 – Hybrid RAG
- BM25-like Search
- Pseudo Embeddings
- Hybrid Ranking
- Reranking
- Citation Engine
- Context Compression

## v16.8 – Realtime Voice
- Voice Sessions
- Wake Word Stub
- STT/TTS Adapter
- Intent Parser
- Approval Boundary
- Interrupts

## v16.9 – Mobile Companion
- Device Pairing
- Offline Capture
- Voice Notes
- Camera OCR Scaffold
- Push Outbox
- Mobile Widgets
- Sync Runs
- Remote Sessions

## v17.2 – P0 Runtime Doctor
- P0 Doctor Command (`p0-doctor`) ergänzt.
- Runtime-Konfigurationssnapshot eingeführt.
- Event-Bus-Probe in den P0 Doctor integriert.
- `command-index` als dedizierter Launcher-Befehl ergänzt.
- Unbekannte Module liefern jetzt einen klaren Fehler statt `KeyError`.
- P0 Integrationstests auf 234 Tests erweitert.
## v17.6 P0
- `p0-contract` ergänzt.
- Launcher-Vertrag in `p0-gate` und `p0-smoke` integriert.
- Validierung: 243 passed.

## v17.8 P0 – Readiness & Bootstrap

- `p0-readiness` ergänzt.
- `p0-bootstrap` ergänzt.
- P0-Gate um Runtime-Readiness erweitert.
- Secrets-, Database-, Event-Bus- und Runtime-State-Prüfungen ergänzt.
- Reports `p0_readiness_latest.json` und `p0_bootstrap_latest.json` ergänzt.
- Tests erweitert: 246 passed.


## v17.9 P0 – Production Gate & Artifact Audit

- `p0-production` ergänzt.
- `p0-audit` ergänzt.
- Vollständige P0-Sequenz mit persistenter Evidenzkette ergänzt.
- Report `runtime/reports/p0_production_gate_latest.json` ergänzt.
- Report `runtime/reports/p0_artifact_audit_latest.json` ergänzt.
- Launcher-Vertrag um `p0-production` und `p0-audit` erweitert.
- Tests erweitert.

Validierung:

- `python launcher.py p0-production --write-report`: PASS
- `python launcher.py p0-audit --write-report`: PASS
- `pytest -q`: 249 passed
