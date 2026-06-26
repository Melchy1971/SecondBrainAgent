# Architekturuebersicht v30.21

```text
SecondBrain OS / Jarvis
|-- Launcher und GUI Bootstrap
|-- Jarvis HUD / lokale GUI
|-- P0 Runtime und Hygiene Gates
|-- P1 RAG Runtime
|-- Embedding Provider Boundary
|-- SQLite / PostgreSQL / pgvector Foundations
|-- Desktop Commands und Dashboard
|-- Connector Framework
|-- Document Understanding
|-- Multi-Agent Runtime
|-- Knowledge Graph
|-- Long-Term Memory
|-- Voice Runtime
|-- Mobile Companion
|-- Production Core
|-- Service Runtime
`-- Installer / Update Layer
```

## Start- und Kontrollfluss

```text
python launcher.py
  -> gui-bootstrap
  -> lokale Konfigurations- und Runtime-Pruefung
  -> GUI/HUD Start
  -> Browser: http://127.0.0.1:8851
```

Kompatible Aliase:

```text
jarvis
gui
gui-start
gui-open
desktop-gui
desktop16-gui
```

## Datenfluss

```text
Input
|-- GUI / Desktop
|-- Voice
|-- Mobile
|-- Connectoren
`-- Dokumente
      |
      v
Ingestion / Parser / Source Records
      |
      v
RAG Store / Memory / Graph / Runtime State
      |
      v
Agents / Commands / Gates
      |
      v
Review / Approval / Reports
      |
      v
Output
|-- GUI
|-- Notifications
|-- Voice
|-- Tasks
`-- Recommendations
```

## Hauptentscheidung

v30.21 macht Jarvis ueber den Launcher direkt startbar. Die Architektur bleibt modular; produktive Reife haengt weiter an echten Provider-Credentials, PostgreSQL/pgvector-Livebetrieb, Secret-Verschluesselung und Connector-OAuth.
