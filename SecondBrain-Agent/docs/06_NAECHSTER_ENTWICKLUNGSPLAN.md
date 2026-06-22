# Nächster Entwicklungsplan

## v17.0 – Integration Core
Ziel: Alle v16.x Module in einen gemeinsamen Projektstand integrieren.

Lieferumfang:
- Unified Launcher
- Module Registry
- Shared Config
- Shared SQLite/PostgreSQL Adapter
- Event Bus
- Unified Health
- Cross-module Smoke Tests

## v17.1 – PostgreSQL + pgvector
Ziel: produktive Datenhaltung.

Lieferumfang:
- PostgreSQL Adapter
- pgvector Schema
- Alembic Migrations
- Connection Pool
- Repository Layer
- Migration von SQLite zu PostgreSQL

## v17.2 – Provider Layer
Ziel: echte LLM-/Embedding-Anbindung.

Lieferumfang:
- OpenAI Provider
- Ollama Provider
- Gemini Provider Scaffold
- Embedding Service
- RAG Answer Generator
- Token/Cost Tracking

## v17.3 – Real Gmail/Calendar Connector
Ziel: erster echter Produkt-Connector.

Lieferumfang:
- OAuth Browser Flow
- Token Refresh
- Gmail Read Sync
- Calendar Read Sync
- Delta Cursor
- Approval für Write Operations

## v17.4 – Desktop Control Center
Ziel: GUI wird Steuerzentrale.

Lieferumfang:
- Module Dashboard
- Agent Runs
- RAG Chat
- Connector Status
- Approval Inbox
- Memory Explorer
- Graph Explorer

## v17.5 – Automation Engine
Ziel: Trigger → Condition → Action → Approval → Execution.

Lieferumfang:
- Trigger Registry
- Rules
- Action Runner
- Approval Gate
- Feedback Loop
