# Offene Lücken nach v17.2

## P0 – Integration
Status: teilweise geschlossen.

Erledigt:
- gemeinsamer Launcher wiederhergestellt
- Command Index verfügbar
- Module Registry vorhanden
- Runtime Healthcheck vorhanden
- P0 Doctor vorhanden
- Event-Bus-Probe über `p0-doctor`
- Test-Collection repariert

Offen:
- gemeinsame Runtime-Lifecycle-Steuerung für Start/Stop aller Module
- einheitliches Logging über alle Module
- verbindliches Fehler-/Exit-Code-Modell
- Cross-Module Smoke Tests für echte Workflows statt nur Statusbefehle

## P0 – Produktive Datenbank
Offen:
- PostgreSQL als produktiver Default
- pgvector
- Alembic-Migrationen
- Connection Pooling
- Repository Layer
- Backup/Restore produktiv

## P0 – Sicherheit
Offen:
- echte Secret-Verschlüsselung statt Placeholder/Base64
- DPAPI/Keyring
- Rollenmodell
- Audit Reports
- DSGVO Export/Löschung
- Approval UI
- Write-Action-Gate für Agenten und Connectoren

## P1 – echte Connectoren
Offen:
- echter OAuth Flow
- Gmail API
- Google Calendar API
- Google Drive API
- GitHub API
- Paperless API
- Obsidian Watcher
- Token Refresh
- Delta Sync mit Retry/Backoff

## P1 – echte Intelligenz
Offen:
- LLM Provider Layer produktiv
- Tool Calling mit Policy Enforcement
- echte Embeddings
- Reranker
- Agent Planning
- Result Validation
- Memory Compression

## P1 – Desktop produktiv
Offen:
- Docking Layout
- System Tray
- Settings vollständig
- Agent Control Center
- Graph View
- RAG Chat
- Connector UI
- Approval Inbox

## P2 – Mobile/Voice produktiv
Offen:
- native App oder PWA
- echte Push Notifications
- Faster Whisper
- Piper/ElevenLabs
- OpenWakeWord/Porcupine
- Mikrofonstreaming

## Update v17.5 P0

Geschlossen:
- Smoke-Gate für lokale P0-Fitness ergänzt.
- Command-Konflikte werden erkannt und blockieren `p0-gate`.
- Kritische Module sind maschinenlesbar über Registry verfügbar.

Offen:
- Echte Connectoren/OAuth.
- Produktive PostgreSQL/pgvector-Schicht.
- GUI-Control-Center.
- Write-Action Approval Flow.

## Stand v17.6 P0
Geschlossen: Launcher-Vertrag ist jetzt durch `p0-contract` maschinenlesbar abgesichert. Offen bleiben produktive Datenbankintegration, echte Secret-Verwaltung, Connector-OAuth, GUI-Control-Center und produktives RAG.
