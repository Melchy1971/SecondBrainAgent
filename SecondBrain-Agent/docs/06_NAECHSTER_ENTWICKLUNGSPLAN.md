# Naechster Entwicklungsplan nach v30.21

## 1. Vollstaendige lokale Release-Validierung

Ziel: v30.21 reproduzierbar absichern.

Lieferumfang:

- `repo-doctor --execute-runtime-checks`
- `dependency-inventory`
- `gui-bootstrap`
- `gui-doctor`
- `p0-gate`
- `p1-gate`
- vollstaendiger `pytest -q`

## 2. GUI Lifecycle und Service Control

Ziel: Jarvis nicht nur starten, sondern kontrolliert betreiben.

Lieferumfang:

- Start/Stop/Restart Status in der GUI.
- PID-/Port-Konsistenz pruefen und reparieren.
- Saubere Fehlerzustaende fuer belegte Ports und tote PID-Dateien.
- Windows-Tray oder Dienst-Integration vorbereiten.

## 3. P1 Production Provider Live Gate

Ziel: produktive Embeddings nachweisbar machen.

Lieferumfang:

- Live-Checks fuer OpenAI/Ollama gegen echte Zielkonfiguration.
- Klare Gate-Ausgaben fuer fehlende Keys, unerreichbare Endpoints und Dimensionsdrift.
- Dokumentierter Reindex-Pfad ueber `p1-vector-index-repair`.

## 4. PostgreSQL/pgvector Produktivpfad

Ziel: SQLite-Prototyp durch produktiven Store ergaenzen.

Lieferumfang:

- `DATABASE_URL`-basierter Startpfad.
- Migration und Audit gegen Live-PostgreSQL.
- Backup/Restore-Probe.
- Performance- und Qualitaetsmessung fuer Vector Search.

## 5. Connector Runtime Foundation live validieren

Ziel: echte Datenquellen kontrolliert anbinden.

Lieferumfang:

- OAuth Flow.
- Token Refresh.
- Gmail/Calendar/Drive/GitHub Read Sync.
- Approval Gate fuer Write Operations.
- Retry/Backoff und Dead Letter Reports.

## 6. Secret- und Approval-Schicht

Ziel: lokale Produktivnutzung absichern.

Lieferumfang:

- DPAPI/Keyring Secret Store.
- Rollen- und Berechtigungsmodell.
- Approval Inbox in der GUI.
- Audit Reports fuer agentische Aktionen.
