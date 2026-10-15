# Offene Punkte und Roadmap

Stand: 2026-07-15. Die Liste enthaelt nur aktuell relevante, belegte Grenzen.

## Prioritaet 1: Produktionsdatenpfad

- PostgreSQL/pgvector aktiv konfigurieren und gegen die Zielinstanz live validieren.
- Task-/Projekt-Repository v31.15 in `main` integrieren und gegen echtes PostgreSQL testen.
- Migration, Backup und Restore-Probe vor produktivem `--apply` ausfuehren und dokumentieren. Der DR-Pfad (pg_dump/pg_restore, Restore in leere Datenbank, atomarer Rollback) ist seit 2026-10-13 gegen eine lokale Testinstanz live belegt; offen sind die Zielinstanz und das Restore-Template dort (siehe Runbook).
- Produktiven Embedding-Provider mit echten Credentials/Endpoints pruefen.
- Vollstaendigen Reindex- und Dimensionsdrift-Pfad abnehmen.
- Jarvis-1.0-Zertifizierung: alle Nachweise sind commit-gebunden versiegelt; Produktions-, Clean-Windows- und CI-Nachweise fuer einen gemeinsamen Commit stehen aus (siehe Runbook, Abschnitt jarvis-1.0-gate).

Die Repository-Tests decken den SQL-Pfad ueber den vorhandenen Test-Executor ab. Das PostgreSQL-/pgvector-Live-Gate hat am 2026-10-12 gegen eine lokale Testinstanz (PostgreSQL 18.4, pgvector 0.8.6, TLS `verify-full`, Rolle ohne RLS-Umgehung) mit `PASS` bestanden, siehe `docs/certification/live_certification_runbook.md`. Offen bleibt der Lauf gegen die Zielinstanz.

## Prioritaet 2: Planner Runtime integrieren

- v31.16 in `main` integrieren.
- Parallelbetrieb mit realen, threadsicheren Tool-Adaptern und Abbruchsignalen end-to-end pruefen.
- Ressourcen-Keys fuer datei-, workspace- und connectorbezogene Schreiboperationen verbindlich deklarieren.

## Prioritaet 3: Sicherheit und Betrieb

- Secret Store mit echter Verschluesselung statt Platzhalter-/Dateiloesung.
- Rollenmodell und Approval-Inbox fuer schreibende Aktionen.
- Kontrollierter Start/Stop/Restart inklusive PID-, Port- und Recovery-Logik.
- Einheitliches strukturiertes Logging sowie belastbare Backup-/Restore-Proben.

## Prioritaet 4: Connectoren

- Echten OAuth-Browserflow, Token Refresh und verschluesselte Token-Ablage implementieren.
- Gmail, Calendar, Drive und GitHub gegen reale Konten read-only validieren.
- Retry/Backoff, Delta-Sync und Dead-Letter-Verhalten end-to-end pruefen.
- Schreiboperationen ausschliesslich ueber Approval-Gates freigeben.

## Prioritaet 5: Oberflaechen

- Native Desktop-App mit realen Cross-Module-Workflows und Fehlerzustaenden abnehmen.
- RAG-Quellenanzeige, Approval-Inbox und Service-Control vervollstaendigen.
- Voice mit Mikrofon, STT, TTS und Wake Word auf Zielhardware testen.
- Mobile Backend durch PWA oder native App, echte Push-Zustellung und Konfliktloesung ergaenzen.

## Security Cameras

- MediaMTX mit mindestens einer realen Kamera validieren.
- WebRTC/HLS-Wiedergabe und ONVIF-/WS-Discovery im Zielnetz pruefen.
- Aufzeichnung, Bewegungserkennung und Remote-Authentifizierung sind bewusst nicht Teil der aktuellen lokalen Integration.

## Release-Nachweis

Vor Freigabe muessen das GA-Readiness-Gate und seine integrierten Security-, Backup-, Installer-, Update-, RAG-, Performance- und Approval-Gates dokumentiert sein. Aktuell ist kein neuer Production PASS mit echter PostgreSQL-/Provider-/Installer-Umgebung belegt.
