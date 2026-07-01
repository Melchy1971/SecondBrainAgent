# Offene Punkte und Roadmap

Stand: 2026-06-30. Die Liste enthaelt nur aktuell relevante, belegte Grenzen.

## Prioritaet 1: Produktionsdatenpfad

- PostgreSQL/pgvector aktiv konfigurieren und gegen die Zielinstanz live validieren.
- Migration, Backup und Restore-Probe vor produktivem `--apply` dokumentieren.
- Produktiven Embedding-Provider mit echten Credentials/Endpoints pruefen.
- Vollstaendigen Reindex- und Dimensionsdrift-Pfad abnehmen.

Der lokale Lauf vom 2026-06-30 war blockiert, weil pgvector deaktiviert und keine DSN konfiguriert war. Es wurde kein Schema angewendet.

## Prioritaet 2: Sicherheit und Betrieb

- Secret Store mit echter Verschluesselung statt Platzhalter-/Dateiloesung.
- Rollenmodell und Approval-Inbox fuer schreibende Aktionen.
- Kontrollierter Start/Stop/Restart inklusive PID-, Port- und Recovery-Logik.
- Einheitliches strukturiertes Logging sowie belastbare Backup-/Restore-Proben.

## Prioritaet 3: Connectoren

- Echten OAuth-Browserflow, Token Refresh und verschluesselte Token-Ablage implementieren.
- Gmail, Calendar, Drive und GitHub gegen reale Konten read-only validieren.
- Retry/Backoff, Delta-Sync und Dead-Letter-Verhalten end-to-end pruefen.
- Schreiboperationen ausschliesslich ueber Approval-Gates freigeben.

## Prioritaet 4: Oberflaechen

- Native Desktop-App mit realen Cross-Module-Workflows und Fehlerzustaenden abnehmen.
- RAG-Quellenanzeige, Approval-Inbox und Service-Control vervollstaendigen.
- Voice mit Mikrofon, STT, TTS und Wake Word auf Zielhardware testen.
- Mobile Backend durch PWA oder native App, echte Push-Zustellung und Konfliktloesung ergaenzen.

## Security Cameras

- MediaMTX mit mindestens einer realen Kamera validieren.
- WebRTC/HLS-Wiedergabe und ONVIF-/WS-Discovery im Zielnetz pruefen.
- Aufzeichnung, Bewegungserkennung und Remote-Authentifizierung sind bewusst nicht Teil der aktuellen lokalen Integration.

## Release-Nachweis

Vor Freigabe muessen Repo Doctor, Dependency Inventory, P0/P1-Gates, fokussierte Tests und der vollstaendige Testlauf dokumentiert sein. Aktuell ist kein Production PASS belegt.
