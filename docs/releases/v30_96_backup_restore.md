# v30.96 Backup & Restore

## Ergebnis

SecondBrain verwendet den bestehenden `OperationsEngine` jetzt als zentralen Backup- und
Restore-Service. Backups sind versioniert, werden vor der Aufnahme in die Historie validiert
und können mit AES-256-GCM authentifiziert verschlüsselt werden. Im Production-Modus sind
unverschlüsselte Backups blockiert.

Gesichert werden – sofern vorhanden – Konfiguration einschließlich `.env`, Memory,
Secret Vault, Review-/Approval-Queues, Connector-Checkpoints, Runtime, Audit und Logs.
Ist PostgreSQL konfiguriert, wird ein Custom-Format-Dump über `pg_dump` aufgenommen;
pgvector-Daten sind Bestandteil desselben Datenbank-Dumps. Passwörter werden nur über die
Kindprozess-Umgebung und nie als Kommandozeilenargument oder Reportfeld übergeben.

## Konfiguration

- `SECONDBRAIN_BACKUP_KEY`: Base64-kodierter Schlüssel mit exakt 32 Byte.
- `SECONDBRAIN_BACKUP_PASSPHRASE`: Alternative; der Schlüssel wird mit Salt abgeleitet.
- `SECOND_BRAIN_DATABASE_URL` oder `DATABASE_URL`: PostgreSQL-Verbindung.
- `SECONDBRAIN_PG_DUMP` und `SECONDBRAIN_PG_RESTORE`: optionale Tool-Pfade.
- `SECONDBRAIN_ENV=production`: erzwingt verschlüsselte Backups.

Der Schlüssel beziehungsweise die Passphrase muss außerhalb des Backup-Inhalts verwahrt
werden. Ohne den passenden Schlüssel ist ein verschlüsseltes Backup absichtlich nicht
wiederherstellbar.

## Bedienung

```text
python launcher.py ops-backup --label nightly
python launcher.py ops-backups
python launcher.py ops-backup-verify <backup-id>
python launcher.py ops-backup-health
python launcher.py ops-backup-report
python launcher.py ops-backup-schedule-configure --interval daily
python launcher.py ops-backup-schedule-run
python launcher.py ops-restore-plan <backup-id>
python launcher.py ops-restore <backup-id>
python launcher.py ops-restore-rollback
```

Der Scheduler speichert Intervall und letzten erfolgreichen Lauf persistent. Ein Windows Task
Scheduler, systemd timer oder der bestehende SecondBrain-Tick ruft `ops-backup-schedule-run`
regelmäßig auf; der Service verhindert innerhalb des Intervalls einen zweiten Lauf.

## Restore- und Verlustschutz

Restore überschreibt keine aktiven Daten. Das Archiv wird authentifiziert, in ein temporäres
Staging-Verzeichnis unter `backups/restores/` entpackt, gegen die Dateihashes validiert und erst
danach als separates Restore-Verzeichnis veröffentlicht. Pfad-Traversal und Symlinks werden
abgelehnt. Rollback entfernt ausschließlich das zuletzt vom Wizard veröffentlichte
`restore_*`-Verzeichnis; Quelldaten und Backup bleiben erhalten.

Ein enthaltener PostgreSQL-Dump wird im Restore-Verzeichnis bereitgestellt und im Dry Run als
expliziter manueller Datenbank-Restore ausgewiesen. Ein automatisches Überschreiben einer
aktiven Produktionsdatenbank findet nicht statt.

## GUI

Die bestehende native Desktop-Anwendung enthält den Navigationspunkt **Backups**. Das
Backup-Center-ViewModel liefert Health, Historie, Scheduler, Restore-Center und die Aktionen
Backup, Validierung, Dry Run, Restore und Rollback. Es wird keine zweite Desktop-Anwendung
gestartet.

## Validierung

- Backup-/Restore-/Operations-Tests: 14 bestanden.
- Launcher- und Secret-Vault-Kompatibilität: 27 bestanden.
- Root-Launcher-Smoke-Test: verschlüsseltes Backup, Health, Dry Run, Restore und Rollback
  bestanden.
- Ruff (neue/geänderte Logik) und Python-Kompilierung: bestanden.

## Bekannte Grenze

Der Datenbank-Dump wird sicher extrahiert, aber nicht automatisch in eine aktive Datenbank
eingespielt. Diese bewusste Schutzgrenze verhindert versehentliches Überschreiben; ein
produktiver Datenbank-Restore benötigt ein separat freigegebenes Ziel und den kontrollierten
Aufruf von `pg_restore`.

