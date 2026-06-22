# Architekturübersicht v16.9

```text
SecondBrain OS / Jarvis
├── Desktop App
├── Database Architecture
├── Connector Framework
├── Document Understanding
├── Multi-Agent Runtime
├── Knowledge Graph
├── Long-Term Memory
├── Hybrid RAG
├── Realtime Voice
├── Mobile Companion
├── Production Core
├── Service Runtime
└── Installer / Update Layer
```

## Datenfluss

```text
Input
├── Desktop
├── Mobile
├── Voice
├── Connectoren
└── Dokumente
      ↓
Ingestion
      ↓
Database / Memory / Graph / RAG
      ↓
Agents
      ↓
Review / Approval
      ↓
Output
├── GUI
├── Push
├── Voice
├── Tasks
└── Recommendations
```

## Hauptentscheidung
Die Architektur ist modular. Aktuell erzeugt jedes Release ein eigenständiges Paket. Nächster notwendiger Schritt ist eine Integrationsschicht, die alle Module in einem gemeinsamen Runtime-/Launcher-/Datenmodell zusammenführt.
