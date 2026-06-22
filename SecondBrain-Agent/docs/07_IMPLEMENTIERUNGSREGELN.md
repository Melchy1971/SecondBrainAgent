# Implementierungsregeln

## Architekturregeln
1. Kein Modul darf direkt fremde Tabellen ändern.
2. Gemeinsame Kommunikation über Event Bus.
3. Jede Aktion schreibt Audit Events.
4. Riskante Aktionen laufen über Approval.
5. Secrets niemals im Klartext loggen.
6. Jede neue Runtime erhält Health/Status/Smoke-Test.
7. Jede Persistenzänderung erhält Migration.
8. Jede Ingestion erzeugt Citations oder Source Records.
9. Agenten dürfen nicht ohne Review-Gate finalisieren.
10. Desktop UI darf Geschäftslogik nicht direkt enthalten.

## Definition of Done
- Code vorhanden
- CLI-Befehle vorhanden
- Tests vorhanden
- Dokumentation aktualisiert
- Smoke-Test dokumentiert
- bekannte Grenzen dokumentiert
