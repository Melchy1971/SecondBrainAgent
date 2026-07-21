# Jarvis — Rest-Roadmap bis 1.0

Stand: 2026-07-21
Basis: `origin/main` = `f0a9dd9`
Grundlage: `docs/status/current_capability_inventory.md`

## Leitsatz

Der Codebestand reicht bis Feature-Stufe v31.88. Für keinen der zertifizierungspflichtigen Bereiche existiert ein produktionsnaher Live-Nachweis. Die verbleibende Arbeit besteht überwiegend aus **Zertifizierung, nicht aus Implementierung**.

Konsequenz für die Reihenfolge: Zuerst fällt, was andere Nachweise blockiert.

---

## Stufe 0 — Vorbedingung — ERLEDIGT (2026-07-21)

**PySide6 als Laufzeitabhängigkeit deklarieren**

`SecondBrain/desktop_native/qt_shell.py` importierte PySide6, ohne dass das Paket deklariert war.

Präzisierung gegenüber der Erstfassung dieser Roadmap: die Anwendung stürzte dadurch **nicht** ab. `capabilities()` prüft PySide6 per `find_spec` und fällt sauber in `degraded_mode`. Der Fehler war stiller Funktionsverlust — die Qt-Oberfläche fehlte auf jeder frischen Installation und im Windows-Paket, ohne dass es auffiel.

Umgesetzt:

- `PySide6>=6.8.0` im `desktop`- und `all`-Extra von `pyproject.toml`
- `requirements-desktop.txt` neu, deckungsgleich mit dem Extra
- `PySide6==6.11.1` in `packaging/windows/constraints.txt` gepinnt
- `tests/test_desktop_runtime_dependencies.py` als Regressionsschutz für PySide6, PySide2, PyQt5 und PyQt6

Offen bleibt der Live-Start auf der Zielmaschine — das gehört zu Stufe 8.

---

## Stufe 1 — PostgreSQL- und pgvector-Live-Gate

Entspricht Prompt 68. Kommando `postgres-live-gate` fehlt vollständig; vorhanden ist nur `p3-pgvector-readiness`.

Umfang: Preflight, isoliertes Testschema pro Lauf, Repository-Tests gegen echtes PostgreSQL, Workspace-Isolation, Concurrency inklusive `FOR UPDATE SKIP LOCKED`, pgvector-Operationen mit Golden Dataset und Mindest-Recall.

Voraussetzung: erreichbare `TEST_DATABASE_URL` mit pgvector-Extension. Produktive `DATABASE_URL` bleibt unangetastet.

Abschlusskriterium: `python launcher.py postgres-live-gate` liefert `PASS`, Report ohne Secrets, Cleanup auch im Fehlerfall nachgewiesen.

---

## Stufe 2 — Approval-Live-Zertifizierung

Der Approval-Layer und `approval_postgres_live_gate.py` sind implementiert. Der Nachweis gegen PostgreSQL fehlt.

Nachzuweisen: Persistenz über Neustart, Payload-Hash, Replay-Schutz, parallele Leases, Workspace-Isolation, Audit-Vollständigkeit, Expiration, `recovery_required`, Exactly-Once gegen synthetische Connectoren.

Keine echten externen Writes auf dieser Stufe.

Abhängig von Stufe 1.

---

## Stufe 3 — Provider-Live-Zertifizierung

`provider-live-gate` ist implementiert, aber nie mit konfiguriertem Provider gelaufen.

Nachzuweisen je Provider: Health, Chat, strukturiertes JSON, Embedding, Timeout, Cancel, Kostenlimit, fehlendes Modell, Auth-Fehler, Offline-Verhalten, Privacy Mode.

Nicht konfigurierte optionale Provider dürfen keinen harten Blocker erzeugen. Pflichtprovider müssen als solche markierbar sein.

Unabhängig von Stufe 1 und 2, kann parallel laufen.

---

## Stufe 4 — Connector-E2E-Zertifizierung

`connector-e2e-gate` ist implementiert. Es fehlen Testkonten und jeder Write-Nachweis.

Nachzuweisen: Gmail und Outlook Read, Draft, Send mit Approval; Kalender Read, Create, Update mit Approval; Cursor-Persistenz; Exactly-Once; Cleanup der Testdaten.

Harte Regel: Bei Timeout nach möglichem Write gilt `recovery_required`. Keine automatische Wiederholung für Mail Send, Forward, Delete, Calendar Write und Publish.

Abhängig von Stufe 2.

---

## Stufe 5 — Live-Zertifizierungs-Orchestrator

Entspricht Prompt 69. Fasst Stufe 1 bis 4 unter `python launcher.py live-certification --scope <bereich>` zusammen.

Vorhandene Gates werden nicht neu geschrieben, sondern aufgerufen und ausgewertet. Konfiguration über `config/live-certification.example.toml` ohne reale Secrets.

Erst sinnvoll, wenn mindestens zwei der Stufen 1 bis 4 grün sind — sonst zertifiziert der Orchestrator Leerlauf.

---

## Stufe 6 — Restliche Jobtyp-Migrationen

Entspricht Prompt 70. Die Job-Runtime unter `SecondBrain/jobs/` existiert. Unbekannt ist, welche Langläufer noch an ihr vorbei laufen.

Erster Schritt ist reine Analyse: Inventar aller `threading.Thread`, `ThreadPoolExecutor`, eigenen Queues, Retry-Loops, lokalen Statusdateien und Subprocess-Jobs ohne Tracking nach `docs/jobs/job_runtime_migration_inventory.md`.

Priorität danach: Reindex, Embedding Rebuild, Graph Extraction, ChatGPT-Großimport, weitere Importe, Connector Sync, Backup, Restore, Diagnostics, OCR, Repository Analysis. Maximal zwei Jobtypen pro Phase.

Besonderer Fokus ChatGPT-Großimport: 2,5-GB-Export streamend verarbeiten, Checkpoints, Resume, Deduplizierung. Keine vollständige Datei in den RAM.

Nicht-idempotente Jobs dürfen nicht automatisch wiederholt werden.

---

## Stufe 7 — Disaster Recovery und Secret Vault

Entspricht Prompt 71. `SecondBrain/secret_manager/` mit Crypto, Audit, Redaction und Health ist implementiert. `SecondBrain/backup*.py` ebenfalls.

Offen: Windows-Credential-Manager- beziehungsweise OS-Keyring-Backend, Schlüsselrotation im Live-Lauf, Restore-Atomarität mit Rollback, Verhalten bei beschädigtem Backup, manipuliertem Manifest, falschem Schlüssel und Crash während Restore.

Abschlusskriterium: `python launcher.py disaster-recovery-gate` liefert `PASS`. `BLOCKED` bei Datenverlust, Secret Leak, fehlendem Rollback, verlorenem Audit oder Approval, defekter Vector Search nach Restore, Klartext-Vault.

Abhängig von Stufe 1, da Restore die Datenbank einschließt.

---

## Stufe 8 — Native Jarvis Desktop

Entspricht Prompt 72, ist aber weitgehend erledigt. Auf `main` liegen Qt-Shell, Action Bus, Navigation, Lifecycle, System Tray, Autostart und Statusflächen für Health, Metrics, Vault, Alerts, Storage, Jobs, Approvals und Tasks.

Verbleibend:

- Entscheidung über die zwei parallelen Qt-Implementierungen (`desktop_app/app.py` und `desktop_native/qt_shell.py`)
- Entscheidung über die fünf parallelen Planner-Implementierungen
- Degraded Mode nachweisen: Start bei offline PostgreSQL, offline Provider, fehlendem Mikrofon, gesperrtem Vault, fehlendem pgvector
- Headless-Tests, soweit möglich
- Live-Start auf der Zielmaschine

Prompt 72 als vollständiges Neubau-Paket zu fahren wäre Doppelarbeit. Der Umfang reduziert sich auf Nachweis und Aufräumen.

---

## Stufe 9 — Vollständige Sprachsteuerung

Entspricht Prompt 73, ebenfalls weitgehend vorhanden: STT-Policy, TTS-Safety, lokales Wake Word, Hotkey, Mikrofonsteuerung, Command Router, `native-voice-app-gate`.

Verbleibend:

- Klärung der zwei parallelen `voice_de.py` unter `desktop_native/` und `native/`
- Confirmation Binding gegen Action, Payload-Hash, Workspace, Actor und Expiration
- Assistant-Fallback für Äußerungen ohne Tool-Intent
- Nachweis, dass TTS kein Wake Word auslöst
- Live-Lauf mit Audiohardware

Abhängig von Stufe 0 und Stufe 8.

---

## Stufe 10 — Windows Installer und Updater

Entspricht Prompt 74. PyInstaller-Spec, WiX, Inno Setup, Build-Skript, Smoke-Test, Bootstrap und Uninstall existieren.

Verbleibend:

- PySide6 und Voice-Abhängigkeiten in den Paketumfang aufnehmen
- Nachweis auf sauberer Windows-11-VM ohne Python und ohne Git
- Upgrade mit Datenerhalt, absichtlicher Fehlerfall, Rollback
- SHA-256, SBOM, Manifest
- Code Signing; ohne Zertifikat `CONDITIONAL_PASS` mit dokumentierter Begründung

Abhängig von Stufe 0, 7, 8, 9.

---

## Stufe 11 — Private Beta

Entspricht Prompt 75. Nichts davon existiert.

Lokale, datensparsame Beobachtung: App-Starts, Laufzeit, Crashes, GUI-Freezes, Voice-Sessions, Job-Ergebnisse, Approval-Zählungen, Connector- und Provider-Fehler, Backup-, Restore- und Update-Ergebnisse. Keine Inhalte, kein Audio, keine Empfänger, keine Keys.

`python launcher.py support-bundle` mit Redaction und Vorschau vor Export.

Beobachtungsdauer 14 bis 30 Tage.

Abhängig von Stufe 10 — ohne installierbares Paket gibt es keine Beta.

---

## Stufe 12 — Jarvis 1.0 Final Gate

Entspricht Prompt 76. Aggregiert alle Teilgates, keine neuen Features.

`PASS` nur wenn alle kritischen Gates real gelaufen sind. Simulierte Ergebnisse zählen nicht. Live-Gates sind im Report als solche zu kennzeichnen.

`CONDITIONAL_PASS` nur bei nichtkritischen UX-Problemen, nicht konfigurierten optionalen Connectoren, fehlendem Code-Signing-Zertifikat oder dokumentierten Performancewarnungen ohne Datenrisiko.

---

## Abweichung von der ursprünglichen Reihenfolge

Die Vorgabe aus Prompt 67 listet zwölf Punkte beginnend mit dem PostgreSQL-Gate. Zwei Korrekturen:

1. **Stufe 0 vorgezogen.** Die fehlende PySide6-Deklaration blockierte drei spätere Stufen. Erledigt am 2026-07-21.

2. **Stufe 8 und 9 stark reduziert.** Prompt 72 und 73 sind als Neubau-Pakete formuliert. Der Code existiert bereits auf `main`. Beide als vollständige Pakete zu fahren würde parallele Subsysteme erzeugen — genau das, was die Projektregeln untersagen. Der Umfang reduziert sich auf Nachweis, Aufräumen der Dubletten und die in Stufe 8 und 9 benannten Lücken.

---

## Nicht in dieser Roadmap

Diese Punkte sind offen, gehören aber nicht in die Release-Kette und sollten separat entschieden werden:

- Fünf parallele Planner-Implementierungen (`agent/planner.py`, `agent/planning/planner.py`, `agent/task_planner.py`, `autonomous_planner.py`, `planner_v2/service.py`)
- Zwei `voice_de.py`-Module
- Paketversion `30.77.0` gegenüber Feature-Stufe `v31.88`
- `_archive_starters/` — Archiv ohne Referenzen
