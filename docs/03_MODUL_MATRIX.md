# Modulstatus v30.25

Die Einstufung trennt vorhandene Foundation von belegter Produktreife.

| Bereich | Aktiver Einstieg | Reifegrad | Hauptgrenze |
|---|---|---|---|
| Launcher / Bootstrap | `python launcher.py` | betriebsfaehig lokal | kein vollstaendiger Service-Lifecycle |
| Native Desktop | `native-gui`, `native-status` | primaere UI | Hardware-/End-to-End-Abnahme offen |
| Web-HUD | `hud`, `gui-web` | optionaler Kompatibilitaetsmodus | kein produktiver Remote-Betrieb |
| P0 Gates | `p0-*`, `repo-doctor` | stabil lokal | externe Produktionsumgebung separat pruefen |
| P1 RAG | `p1-rag-*`, `p1-gate` | fortgeschritten | echte Provider- und Qualitaetsabnahme offen |
| PostgreSQL/pgvector | `p3-*` | Foundation mit Live-Checks | deaktiviert ohne DSN; Migration nicht automatisch produktiv |
| Knowledge Graph | `graph-*` | lokale Foundation | kein produktiver Graph-Store |
| Desktop Backend | `desktop-*` | lokale Foundation | Approval-Inbox und Lifecycle fehlen |
| Voice | `voice-*`, `VOICE_CONTROL_v20.md` | Textpfad nutzbar | Mikrofon, STT und TTS nicht live abgenommen |
| Mobile | `mobile16-*` | Backend-Foundation | keine native App, Push/OCR teilweise simuliert |
| Connectoren | Runtime-Module / HUD | Foundation | echte OAuth/API-Synchronisation fehlt |
| Agenten / Automation | Runtime-Module | deterministische Foundation | keine vollstaendige LLM-/Tool-Produktionskette |
| Security Cameras | Web-HUD API | lokale Integration | Gateway und echte Kamera muessen live validiert werden |

Den aktuellen, maschinenlesbaren Befehlskatalog liefert `python launcher.py command-index`.
