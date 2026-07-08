# Architekturuebersicht

## Systemgrenzen

```text
Native Desktop / Voice / Web-HUD / CLI / Mobile Backend
                         |
                         v
              Launcher und Runtime-Gates
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
     P1 RAG        Agent Runtime      Connectoren
        |                |                |
        +----------------+----------------+
                         |
                         v
     SQLite / PostgreSQL-pgvector / JSON Runtime State
                         |
                         v
            Audit, Reports und Approval-Grenzen
```

Die native Desktop-App ist seit v30.25 die primaere Oberflaeche. Das Web-HUD auf Port 8851 bleibt ein optionaler Kompatibilitaetsmodus.

## Kontrollfluss

```text
python launcher.py
  -> Umgebungs- und GUI-Bootstrap
  -> Runtime-Diagnose
  -> native Desktop-App
```

Schreibende oder systemnahe Aktionen werden nicht direkt aus der UI ausgefuehrt. Sie laufen ueber registrierte Launcher-/Tool-Grenzen und benoetigen je nach Risiko eine Bestaetigung.

## Datenfluss

```text
Dateien / Inbox / Connectoren / Voice / Mobile
  -> Parser und Normalisierung
  -> Source Records und Chunks
  -> Embeddings / RAG Store / Memory / Graph
  -> Suche, Antworten, Agenten und Workflows
  -> UI, Reports, Benachrichtigungen und Review
```

## Persistenz

- SQLite und JSON dienen als lokale, deterministische Basis.
- PostgreSQL/pgvector ist vorbereitet, aber nur bei aktivierter Konfiguration und erfolgreichem Live-Gate produktiv.
- Laufzeitdaten liegen unter `runtime/` und `data/` und gehoeren nicht in Git.
- Secrets gehoeren in lokale Umgebungsvariablen oder ignorierte Konfigurationsdateien und nie in Dokumentation, Reports oder Kamera-Metadaten.

## Kompatibilitaet

Viele historische Module bleiben im Repository, sind aber nicht Teil der aktuellen Hauptoberflaeche. Der verbindliche Befehlskatalog ist die Ausgabe von:

```powershell
python launcher.py command-index
```
