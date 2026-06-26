# Offene Luecken nach v30.21

## Geschlossen oder deutlich verbessert

- Gemeinsamer Launcher vorhanden.
- `python launcher.py` startet Jarvis direkt.
- GUI-Bootstrap mit lokalen Defaults und Runtime-Ordnern vorhanden.
- `gui-doctor` prueft Launcher, Startskripte, Shortcut-Installer, Python und Runtime-Status.
- P0 Gates, Repo Doctor und Dependency Inventory vorhanden.
- P1 RAG Runtime, Golden Eval, Provider Health Gate und Vector Index Repair vorhanden.
- Embedding-Index-Identitaet beruecksichtigt Provider, Modell und Dimension.
- Windows-Startskripte und Shortcut-Installer sind auf den Jarvis-Launcher ausgerichtet.

## P0 / Runtime

Offen:

- Gemeinsame Lifecycle-Steuerung fuer Start/Stop aller produktiven Services.
- Einheitliches Logging ueber alle Module hinweg.
- Cross-Module Smoke Tests fuer echte Workflows statt nur Statusbefehle.
- Stabiler Hintergrundbetrieb als Windows-Dienst mit Restart-Policy.

## Datenbank und RAG

Offen:

- PostgreSQL/pgvector als produktiver Default.
- Live-Migration von SQLite zu PostgreSQL/pgvector.
- Betrieblich abgesicherte Backups und Restore-Proben.
- Live-Provider-Validierung fuer OpenAI/Ollama in der Zielumgebung.
- Reranker und semantische Qualitaetsmessung mit echten Daten.

## Sicherheit

Offen:

- Echte Secret-Verschluesselung statt Placeholder-Konfiguration.
- DPAPI/Keyring-Integration.
- Rollenmodell fuer lokale und agentische Aktionen.
- Approval UI fuer Write Operations.
- DSGVO Export/Loeschung und Audit Reports.

## Connectoren

Offen:

- Echter OAuth Browser Flow.
- Gmail, Google Calendar, Google Drive und GitHub API Sync gegen echte Konten.
- Token Refresh und sichere Token-Ablage.
- Delta Sync mit Retry/Backoff und Dead Letter Handling.
- Write Operations nur ueber Approval Gate.

## GUI / Produkt

Offen:

- Vollstaendige Cross-Module Workflows in der GUI.
- Approval Inbox.
- RAG Chat mit Quellenanzeige und Fehlerzustaenden.
- Connector Control Center.
- Graph/Memory Explorer fuer Endnutzer.
- System Tray und kontrollierter Stop/Restart.

## Voice / Mobile

Offen:

- Produktives Mikrofonstreaming.
- STT/TTS-Integration.
- Wake Word Engine mit sicherer Aktivierungslogik.
- Native App oder PWA.
- Echte Push Notifications.

## Aktuelle Gate-Warnungen

- Ohne `DATABASE_URL` bleibt SQLite/RAG-Prototyp aktiv.
- Lokaler deterministischer Embedding-Provider erlaubt Entwicklung, blockiert aber Production Gates.
- Vollstaendiger `pytest -q` kann je nach Umgebung lange laufen und muss fuer Release-Freigaben separat abgeschlossen werden.
