# Implementierungsregeln

## Architektur

1. Oeffentliche CLI-Kommandos bleiben kompatibel, sofern eine Migration nicht explizit dokumentiert ist.
2. GUI, Launcher und Runtime-Gates verwenden dieselben Start- und Konfigurationspfade.
3. Module mutieren fremde Persistenzbereiche nur ueber definierte Runtime-, Repository- oder Service-Grenzen.
4. Riskante Aktionen laufen ueber Policy-, Approval- oder Gate-Mechanismen.
5. Secrets werden nie geloggt, in Reports persistiert oder in Beispieldateien mit realen Werten dokumentiert.
6. Neue Runtime-Funktionen erhalten Status/Health, explizite Fehlerfaelle und fokussierte Tests.
7. Persistenzaenderungen erhalten Migration, Reparaturpfad oder eine dokumentierte Kompatibilitaetsentscheidung.
8. Ingestion erzeugt nachvollziehbare Quellen- und Citation-Daten.
9. UI-Code enthaelt keine versteckte Geschaeftslogik, die CLI- oder Sicherheitsgrenzen umgeht.
10. Historische Implementierungsdetails gehoeren in Release-Notizen, nicht in aktuelle Bedienhandbuecher.

## Definition of Done

- Minimaler, reviewbarer Code-Diff.
- Neue Logik und relevante Edge Cases getestet.
- Fehlerfaelle und externe Abhaengigkeiten sichtbar behandelt.
- Bedienung oder Architektur aktualisiert, wenn sie sich geaendert hat.
- Relevante Gates ausgefuehrt oder mit Grund als nicht ausgefuehrt dokumentiert.
- Bekannte Grenzen und Restrisiken benannt.
- Keine Cache-, Log-, PID-, Secret- oder generierten Reportdateien im Commit.

## Dokumentationsregeln

- Aktuelle Bedienung steht in den im [`README.md`](README.md) verlinkten Handbuechern.
- Der Befehlskatalog wird nicht manuell dupliziert; `python launcher.py command-index` ist verbindlich.
- `docs/releases/` enthaelt unveraenderliche historische Evidenz.
- Neue Release-Snapshots duerfen aktuelle Handbuecher nicht ersetzen.
- `09_MASTERPLAN_STATUS.json` bleibt maschinenlesbar und darf keine Secrets enthalten.
