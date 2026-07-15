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
 PostgreSQL/pgvector / signierte Artefakte / Dev-JSONL
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

## Persistenz und Ausfuehrung

- PostgreSQL/pgvector ist der produktive Datenpfad; SQLite und JSONL sind explizite Entwicklungsmodi.
- Tasks und Projekte verwenden in Produktion ein transaktionales PostgreSQL-Repository. Die JSONL-Migration validiert vor dem Schreiben IDs, Versionen, Dubletten und Workspace-Zuordnungen.
- Planner v2 validiert DAGs, Budgets, Scopes, Risiken und Approvals. Unabhaengige sichere Knoten koennen parallel laufen; Approval-/Unsafe-Knoten und gemeinsam gesperrte Ressourcen bleiben serialisiert.
- Updates und Rollbacks erfordern signierte Manifeste und Pakete sowie Hash-, Kanal- und Kompatibilitaetspruefungen.
- Laufzeitdaten liegen unter `runtime/` und `data/` und gehoeren nicht in Git.
- Secrets gehoeren in lokale Umgebungsvariablen oder ignorierte Konfigurationsdateien und nie in Dokumentation, Reports oder Kamera-Metadaten.

## Kompatibilitaet

Viele historische Module bleiben im Repository, sind aber nicht Teil der aktuellen Hauptoberflaeche. Der verbindliche Befehlskatalog ist die Ausgabe von:

```powershell
python launcher.py command-index
```
