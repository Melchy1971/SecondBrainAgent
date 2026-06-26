# SecondBrain OS / Jarvis Dokumentation v30.21

Stand: v30.21 Unified Application Bootstrap

## Zielbild

SecondBrain OS ist ein lokaler Jarvis-/SecondBrain-Agent fuer Wissen, Dokumente, Aufgaben, RAG, Agenten, GUI, Voice, Mobile Companion und kontrollierte Automatisierung.

## Aktueller Reifegrad

- GUI/HUD: startfaehig ueber `python launcher.py`, `jarvis`, `gui` und Windows-Startskripte.
- Bootstrap: prueft lokale Defaults, Runtime-Ordner, Python, Datenbank-URL und Embedding-Provider.
- P1 RAG: lokale Entwicklung mit deterministischem Provider; produktive Provider bleiben Gate-relevant.
- PostgreSQL/pgvector: Foundation und Live-Checks vorhanden, produktive Live-Validierung umgebungsabhaengig.
- Connectoren: Produktionsnahe Strukturen vorhanden, echte OAuth/API-Laeufe bleiben offen.
- Desktop/Voice/Mobile/Graph/Memory: modulare Foundations vorhanden, Produktreife je Modul unterschiedlich.

## Aktueller Startpunkt

Alle lokalen Befehle aus dem Projektordner starten:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

Bootstrap und Diagnose:

```powershell
python launcher.py gui-bootstrap
python launcher.py gui-doctor
```

Jarvis starten:

```powershell
python launcher.py
```

Browser: `http://127.0.0.1:8851`

Weitere Startbefehle: `docs\04_STARTBEFEHLE.md` und `docs\START_GUI.md`.

## Dokumentationsstruktur

- `01_ARCHITEKTUR_UEBERSICHT.md`: System- und Datenfluss.
- `02_RELEASE_HISTORY.md`: komprimierte Release-Historie.
- `03_MODUL_MATRIX.md`: aktueller Modulstatus.
- `04_STARTBEFEHLE.md`: verifizierte Start- und Diagnosebefehle.
- `05_OFFENE_LUECKEN.md`: offene technische und produktive Luecken.
- `06_NAECHSTER_ENTWICKLUNGSPLAN.md`: naechste sinnvolle Arbeitspakete.
- `07_IMPLEMENTIERUNGSREGELN.md`: Regeln fuer Code, Persistenz und Gates.
- `08_RELEASE_GATE.md`: aktueller Gate-Status.
- `09_MASTERPLAN_STATUS.json`: maschinenlesbarer Status.
- `releases/`: historische, auditierbare Release-Artefakte.
