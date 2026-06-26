# Implementierungsregeln

## Architekturregeln

1. Oeffentliche CLI-Kommandos bleiben abwaertskompatibel, sofern keine Migration dokumentiert ist.
2. GUI, Launcher und Runtime-Gates duerfen keine widerspruechlichen Startpfade dokumentieren.
3. Kein Modul darf direkt fremde Persistenzbereiche mutieren.
4. Gemeinsame Kommunikation laeuft ueber definierte Runtime-, Event- oder Service-Grenzen.
5. Jede riskante Aktion laeuft ueber ein Approval- oder Gate-Modell.
6. Secrets werden nie geloggt, gedruckt oder in Reports persistiert.
7. Jede neue Runtime erhaelt Health/Status und mindestens einen fokussierten Test.
8. Jede Persistenzaenderung erhaelt Migration, Reparaturpfad oder explizite Kompatibilitaetsentscheidung.
9. Jede Ingestion erzeugt nachvollziehbare Source Records oder Citations.
10. Desktop-/GUI-Code enthaelt keine versteckte Geschaeftslogik, die CLI/Gates umgeht.

## Definition of Done

- Code vorhanden und lokal lauffaehig.
- CLI- oder GUI-Einstieg dokumentiert.
- Fehlerfaelle explizit behandelt.
- Tests fuer neue Logik oder Bugfix vorhanden.
- Relevante Gates ausgefuehrt oder begruendet ausgelassen.
- Dokumentation und `docs/09_MASTERPLAN_STATUS.json` aktualisiert.
- Bekannte Grenzen und Restrisiken dokumentiert.

## Release-Regeln

- Historische Dateien unter `docs/releases/` bleiben auditierbare Artefakte.
- Aktuelle Bedienung steht in `README.md`, `INSTALLATION_BEGINNER.md`, `docs/README.md`, `docs/04_STARTBEFEHLE.md` und `docs/START_GUI.md`.
- Root-Dokumente duerfen nur auf den aktuellen Unterordnerstand verweisen, nicht eigene veraltete Bedienlogik enthalten.
