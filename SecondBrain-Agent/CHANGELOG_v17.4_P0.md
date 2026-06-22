# CHANGELOG v17.4 P0

## Ziel
P0-Betriebsfähigkeit weiter härten: Gate-Ergebnisse persistieren, maschinenlesbare Reports für CI/Release einführen und Diagnoseausgabe stabilisieren.

## Änderungen
- `p0-report` als neuer Launcher-Befehl ergänzt.
- `p0-gate --write-report` ergänzt.
- P0-Gate-Payload um Schema und UTC-Zeitstempel erweitert.
- Gate-Checks stabil sortiert: fehlerhafte/blockierende Checks erscheinen zuerst.
- Report-Datei `runtime/reports/p0_gate_latest.json` wird geschrieben.
- `p0-doctor` schreibt den aktuellen Gate-Report automatisch mit.
- Command-Index um `p0-report` erweitert.
- Tests für Report-Persistenz und Write-Report-Flag ergänzt.

## Ergebnis
P0 liefert jetzt nicht nur Konsolenausgabe, sondern einen wiederverwendbaren Gate-Artefakt für lokale Prüfung, CI und Release-Dokumentation.
