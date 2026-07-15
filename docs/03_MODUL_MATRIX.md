# Modulstatus v31.16

Die Einstufung trennt vorhandene Foundation von belegter Produktreife.

| Bereich | Aktiver Einstieg | Reifegrad | Hauptgrenze |
|---|---|---|---|
| Launcher / Bootstrap | `python launcher.py` | betriebsfaehig lokal | kein vollstaendiger Service-Lifecycle |
| Native Desktop | `native-gui`, `native-status` | primaere UI | Hardware-/End-to-End-Abnahme offen |
| Web-HUD | `hud`, `gui-web` | optionaler Kompatibilitaetsmodus | kein produktiver Remote-Betrieb |
| P0 Gates | `p0-*`, `repo-doctor` | stabil lokal | externe Produktionsumgebung separat pruefen |
| P1 RAG | `p1-rag-*`, `p1-gate` | fortgeschritten | echte Provider- und Qualitaetsabnahme offen |
| PostgreSQL/pgvector | `p3-*` | produktiver Pfad mit Live-Checks | Zielinstanz und pgvector muessen live validiert werden |
| Tasks / Projekte | Task Center / `SecondBrain/tasks` | integriert; PostgreSQL-Nacharbeit auf v31.15-Branch | echter PostgreSQL-Lauf benoetigt `TEST_DATABASE_URL` |
| Planner v2 | `SecondBrain/planner_v2` | DAG, Recovery und Parallel Runtime | v31.16-Branch noch in `main` integrieren |
| Long-running Jobs | `SecondBrain/jobs` | PostgreSQL Repository, Worker, Monitor, Metrics | Import/Planner integriert; Connector/Memory/Backup/Reindex folgen schrittweise |
| Update Center | Update GUI / Update Runtime | signiert und rollbackfaehig | reale Signatur-/Rollout-Infrastruktur extern abnehmen |
| Windows Distribution | Packaging / Installer Smoke | Portable und Installer-Pipeline | Zielsystem-Smoke und Signierung extern abnehmen |
| GA Readiness | `python launcher.py ga-readiness-gate` | verbindliches aggregiertes Gate | PASS bleibt umgebungsabhaengig |
| Persoenliche Assistenz | Dashboard, Briefing, Calendar, Mail, Proactive | integrierte v31-Oberflaechen | externe Provider bleiben approval- und credential-abhaengig |
| Knowledge Graph | `graph-*` | lokale Foundation | kein produktiver Graph-Store |
| Desktop Backend | `desktop-*` | lokale Foundation | Approval-Inbox und Lifecycle fehlen |
| Voice | `voice-*`, `VOICE_CONTROL_v20.md` | Textpfad nutzbar | Mikrofon, STT und TTS nicht live abgenommen |
| Mobile | `mobile16-*` | Backend-Foundation | keine native App, Push/OCR teilweise simuliert |
| Connectoren | Runtime-Module / HUD | Foundation | echte OAuth/API-Synchronisation fehlt |
| Agenten / Automation | Runtime-Module | deterministische Foundation | keine vollstaendige LLM-/Tool-Produktionskette |
| Security Cameras | Web-HUD API | lokale Integration | Gateway und echte Kamera muessen live validiert werden |

Den aktuellen, maschinenlesbaren Befehlskatalog liefert `python launcher.py command-index`.
