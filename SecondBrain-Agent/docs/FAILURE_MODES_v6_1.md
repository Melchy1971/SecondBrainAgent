# Failure Modes v6.1

## Falsche Pfade
Auswirkung: Import läuft ins Leere.
Kontrolle: Runtime Diagnostics.

## Fehlende Schreibrechte
Auswirkung: Reports/Backups schlagen fehl.
Kontrolle: Backup Restore Test.

## Secrets im Vault
Auswirkung: Datenschutzrisiko.
Kontrolle: Secret Scan im Release Gate.

## Zu viele automatisch erzeugte Notizen
Auswirkung: Vault-Rauschen.
Kontrolle: Quality Gate und Review Queue.

## Sync-Konflikte
Auswirkung: doppelte/kaputte Notizen.
Kontrolle: Conflict Report und Sync Health.

## Regressionsfehler
Auswirkung: Skripte laufen nicht.
Kontrolle: Hardening Tests.
