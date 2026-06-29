---
title: "Entwicklungsstand und Architektur"
type: chatgpt_conversation
source: chatgpt
source_id: "69b3dd71-8158-8397-bc4d-b3916c0f768b"
created: 2026-03-13
tags:
  - chatgpt
  - code
  - gesundheit
  - import
  - ki
  - projekt
  - sap
  - tischtennis
  - verein
---


# Entwicklungsstand und Architektur

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69b3dd71-8158-8397-bc4d-b3916c0f768b`
- Nachrichten: 10

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

in der datei ist der aktuelle stand der entwicklung und dieser dient als grundlage für die weitere entwicklung

### 2. Assistent

Datei extrahiert und Struktur analysiert. Aktueller Entwicklungsstand lässt sich wie folgt modellieren.

## Systemarchitektur

**Architekturtyp:** Lokales Analyse- und Import-System für Dokumente und PST-Mailarchive.  
**Paradigma:** Service-orientierte Backend-Schicht + UI-Frontend + externe Wissenspersistenz (Neo4j).

**Technologiestack**

| Layer | Technologie | Funktion |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | UI, Workflowsteuerung |
| Backend | FastAPI | API, Orchestrierung |
| Analyse | Ollama / DNAbot | LLM-Analyse |
| Graph Storage | Neo4j | Wissensgraph |
| Storage | lokale JSON / Files | Zwischenspeicher |

---

## Projektstruktur

### 1. Backend

Domänenorientierte Struktur.

```
backend/app
├─ adapters
│  ├─ neo4j_adapter
│  ├─ ollama_adapter
│  └─ dnabot_adapter
│
├─ api
│  ├─ router
│  └─ routes
│     ├─ health
│     ├─ sources
│     ├─ filesystem
│     ├─ import_jobs
│     ├─ import_runs
│     ├─ persist
│     └─ settings
│
├─ core
│  └─ config
│
├─ models
│  ├─ source
│  ├─ document
│  ├─ import
│  ├─ analysis
│  ├─ settings
│  └─ tree
│
└─ services
   ├─ scanning
   ├─ pst
   ├─ import
   ├─ analysis
   └─ persistence
```

**Architekturpattern**

```
API Layer
   ↓
Service Layer
   ↓
Adapter Layer
   ↓
External Systems
```

Eigenschaften:

- klare Trennung Infrastruktur / Domäne
- Adapter kapseln externe Systeme
- Services enthalten Business-Logik
- Modelle definieren Datenstruktur

---

### 2. Frontend

React-Struktur nach Funktionsdomänen.

```
frontend/src
├─ api
│  ├─ client
│  ├─ sources
│  ├─ persist
│  ├─ import
│  ├─ analysis
│  ├─ filesystem
│  └─ settings
│
├─ components
│  ├─ layout
│  ├─ status
│  ├─ documents
│  └─ sources
│
├─ pages
│  ├─ system
│  ├─ quellen
│  ├─ datenimport
│  ├─ pst-scan
│  ├─ pst-import
│  └─ analyse
│
├─ styles
└─ types
```

Frontend erfüllt drei Rollen:

1. **Systemstatus / Konfiguration**
2. **Datenquellenverwaltung**
3. **Import- und Analysepipeline**

---

## Datenfluss (Pipeline)

Aktuelles System implementiert implizit folgende Verarbeitungskette:

```
Filesystem / PST
        │
        ▼
Scanning Service
        │
        ▼
Import Service
        │
        ▼
Document Model
        │
        ▼
Analysis Service (LLM)
        │
        ▼
Persistence Service
        │
        ▼
Neo4j Graph
```

---

## Funktionale Module

### Quellenverwaltung

- lokale Verzeichnisse
- PST-Archive

API: `sources`, `filesystem`

---

### Import

- Scan
- Import Jobs
- Import Runs
- Dokumentpersistenz

API:  
`import_jobs`  
`import_runs`

---

### Analyse

- Dokumentanalyse über LLM
- vermutlich:
  - Entity Extraction
  - Strukturierung
  - Wissensgraph Aufbau

API: `analysis`

---

### Persistenz

Speicherung in:

- Neo4j
- lokale JSON-Daten

API: `persist`

---

## Stärken der aktuellen Architektur

1. **Saubere Layer-Trennung**

Adapters isolieren externe Systeme.

2. **LLM austauschbar**

Ollama / DNAbot über Adapter abstrahiert.

3. **Graph-First Architektur**

Neo4j ermöglicht:

- Relationship Mining
- E-Mail Netzwerke
- Wissensgraphen

4. **Import-Pipeline vorhanden**

- Jobs
- Runs
- Status

Skalierbar für große Mailarchive.

---

## Architektonische Risiken

### 1. Pipeline-Orchestrierung

Unklar:

- Job-Queue
- Parallelisierung
- Retry-Mechanismen

Risiko:

```
Große PST → blockierende Analyse
```

---

### 2. Persistenzmodell

Lokale JSON + Neo4j.

Potenzielle Probleme:

- Inkonsistenz
- fehlende Versionierung
- fehlende Transaktionslogik

---

### 3. LLM-Kosten / Performance

Analyse vermutlich:

```
Dokument → Prompt → LLM → Graph
```

Risiken:

- Tokenkosten
- lange Laufzeiten
- fehlendes Chunking

---

### 4. Datenmodell Graph

Ohne strikte Ontologie entstehen:

- inkonsistente Nodes
- Duplikate
- schlechte Query-Performance

---

## Implizites Zielsystem

Die Struktur deutet auf eine **Knowledge Extraction Plattform**.

Zielbild:

```
Mail + Dokumente
      ↓
Semantische Analyse
      ↓
Entity + Relationship Extraction
      ↓
Neo4j Knowledge Graph
      ↓
Abfragen / Exploration
```

---

## Reifegrad (geschätzt)

| Bereich | Status |
|---|---|
Frontend | mittlere Reife |
Backend API | stabil strukturiert |
Import Pipeline | vorhanden |
Analyse | integriert |
Graph Persistenz | vorhanden |
Orchestrierung | unklar |

Gesamt: **MVP / frühe Produktionsphase**

---

## Strategisch nächste Entwicklungsstufen

1. **Graph Ontology Layer**
2. **Import Queue System**
3. **Chunking + Embeddings**
4. **Deduplication Pipeline**
5. **Graph Query Interface**
6. **Incremental Re-Analysis**

---

Wenn gewünscht, kann ich als nächsten Schritt:

- die **gesamte Codebasis architektonisch auditieren**
- die **Neo4j-Datenstruktur rekonstruieren**
- eine **optimale LLM-Analysepipeline für das Projekt entwerfen**.

### 3. Benutzer

ich möchte nun einen pst import implementieren. die pst dateien liegen entweder lokal auf einer hdd oder auf einem netzwerklaufwerk. binde immer per auswahl die pst ein und zeige die ordnerstruktur in der pst datei an. damit beginnen wir

### 4. Assistent

Schritt 1 implementiert: PST-Datei per Auswahl einbinden und Ordnerstruktur anzeigen.

Ergebnis:
- Backend: PST-Tree-Modell ergänzt
- Backend: PST-Parser-Service implementiert
- Backend: Selektion persistierbar gemacht
- Backend: Import-Preview-Basis ergänzt
- Frontend: PST-Import-Seite auf Auswahlworkflow umgestellt
- Frontend: manuelle Navigation zu Netzpfaden im Browser ergänzt
- Frontend: PST-Ordnerstruktur-Seite implementiert
- Frontend: Sidebar um PST-Navigation ergänzt

Wesentliche Logik:
1. PST wird nicht frei eingetippt, sondern über Dateibrowser ausgewählt.
2. Browser kann lokale Laufwerke und manuell eingegebene Netzwerkpfade öffnen.
3. Nach Einbindung wird die PST als Quelle registriert und direkt die Ordnerstruktur geladen.
4. Die Ordnerstruktur wird rekursiv als Folder-Tree aufgebaut.
5. Ordnerauswahl wird gespeichert; Toggle auf einem Ordner wirkt auf den gesamten Teilbaum.

Geänderte Dateien:
- `backend/app/models/tree_models.py`
- `backend/app/services/pst_parser_service.py`
- `backend/app/services/source_selection_service.py`
- `backend/app/services/import_preview_service.py`
- `frontend/src/types/source.ts`
- `frontend/src/pages/PstTreePage.tsx`
- `frontend/src/pages/PstImportPage.tsx`
- `frontend/src/components/sources/SourceTreeView.tsx`
- `frontend/src/components/layout/SidebarNav.tsx`

Artefakt:
[Projektstand mit PST-Tree Schritt 1](sandbox:/mnt/data/wdb20/WDB_20-main-pst-tree-step1.zip)

Validierung:
- Backend Python-Syntax geprüft: erfolgreich
- Frontend-Build im Container nicht belastbar validierbar, da im Projektcontainer bereits Grundabhängigkeiten/Typauflösung fehlen (`react`, `vite` etc.). Das ist kein regressionsspezifischer Fehler dieser Änderung, sondern ein lokales Build-Setup-Problem der bereitgestellten Umgebung.

Offene technische Risiken:
- `filesystem.py` ist auf Windows-Laufwerkslogik ausgelegt. Das passt zur PST-/Netzlaufwerk-Anforderung, ist aber nicht plattformneutral.
- `libratom/pypff` muss im Zielsystem sauber installiert sein. Ohne diese Abhängigkeit liefert der Tree-Endpunkt erwartbar `503`.
- UNC-Browsing funktioniert über manuelle Eingabe eines Netzwerkpfads in den Browserdialog. Eine automatische Share-Discovery ist noch nicht implementiert.
- Tree zeigt aktuell Ordnerstruktur mit Message-Counts, keine Nachrichtenvorschau. Das ist für Schritt 1 korrekt.

Nächste sinnvolle Ausbaustufe:
- Auswahlverhalten fachlich härten: nur Folder-Knoten selektierbar, Parent/Child-Status konsistent, “Alle auswählen / Auswahl zurücksetzen”, danach Preview und echter PST-Importlauf.

### 5. Benutzer

erstelle mir immer zum schluss die benötigten Prompts für vsc

### 6. Assistent

Verstanden. Ab jetzt liefere ich am Ende jeder inhaltlichen Antwort die benötigten **VSC-Prompts** für den jeweiligen Umsetzungsschritt.

Für den aktuellen Schritt **„PST-Datei auswählen und Ordnerstruktur anzeigen“** sind diese Prompts zweckmäßig:

### VSC-Prompt 1 — Backend: PST-Datei laden und Ordnerstruktur extrahieren
```text
Implementiere im FastAPI-Backend einen PST-Tree-Endpunkt.

Ziel:
- Eine ausgewählte PST-Datei einlesen
- Die Ordnerstruktur rekursiv extrahieren
- Das Ergebnis als JSON-Tree für das Frontend bereitstellen

Rahmenbedingungen:
- PST-Dateien liegen lokal auf HDD oder auf Netzwerklaufwerken
- Die PST wird nicht hartcodiert, sondern über einen zuvor ausgewählten Dateipfad übergeben
- Verwende einen separaten Service für PST-Parsing
- Kapsle externe PST-Abhängigkeiten in einem klaren Adapter/Service
- Liefere pro Knoten mindestens:
  - id
  - name
  - path
  - parent_path
  - has_children
  - message_count
  - children[]

Aufgaben:
1. Erstelle ein Tree-Modell für PST-Ordner
2. Implementiere einen pst_parser_service
3. Ergänze einen API-Endpunkt:
   - POST /sources/pst/tree oder GET /sources/pst/tree?path=...
4. Fehlerbehandlung:
   - Datei nicht gefunden
   - ungültige Dateiendung
   - Parser-Abhängigkeit fehlt
   - PST beschädigt
5. Rückgabeformat stabil und frontendtauglich halten
6. Rekursive Verarbeitung mit sauberer Trennung zwischen Modell, Service und Route

Lieferumfang:
- vollständiger Python-Code
- Änderungen nach Datei getrennt
- kurze Begründung der Architekturentscheidungen
```

### VSC-Prompt 2 — Frontend: PST-Auswahl und Tree-Anzeige
```text
Implementiere im React-Frontend einen Workflow für PST-Auswahl und Anzeige der Ordnerstruktur.

Ziel:
- Benutzer wählt eine PST-Datei über den vorhandenen Datei-/Pfadbrowser aus
- Nach Auswahl wird die PST als Quelle eingebunden
- Danach wird die Ordnerstruktur geladen und als Tree angezeigt

Rahmenbedingungen:
- React + TypeScript
- Bestehende API-Client-Struktur weiterverwenden
- PST kann lokal oder auf Netzwerklaufwerk liegen
- Netzpfade sollen über manuelle Pfadeingabe unterstützt werden
- Tree rekursiv rendern

Aufgaben:
1. Ergänze den API-Client um eine Methode zum Laden der PST-Ordnerstruktur
2. Passe die PST-Import-Seite auf Auswahlworkflow an
3. Erstelle eine Tree-Komponente für PST-Ordner
4. Zeige pro Knoten:
   - Ordnername
   - Message Count
   - Expand/Collapse
5. Lade Tree direkt nach erfolgreicher PST-Auswahl
6. Fehlerzustände visualisieren:
   - keine Datei gewählt
   - PST kann nicht gelesen werden
   - API nicht erreichbar
7. Types sauber definieren:
   - PstFolderNode
   - PstTreeResponse

Lieferumfang:
- vollständiger TypeScript/TSX-Code
- Änderungen nach Datei getrennt
- keine Platzhalter, sondern integrierbare Implementierung
```

### VSC-Prompt 3 — Auswahlstatus für spätere Imports vorbereiten
```text
Erweitere die bestehende Importlogik so, dass ausgewählte PST-Ordner für spätere Importläufe vorgemerkt werden können.

Ziel:
- Ordner im PST-Tree selektierbar machen
- Auswahlzustand persistieren
- Basis für spätere Preview- und Import-Schritte schaffen

Anforderungen:
- Checkbox pro Ordner
- Auswahl eines Parents wirkt auf den gesamten Teilbaum
- Auswahlstatus im Backend speicherbar
- API und Frontend-Typen konsistent halten
- Noch kein echter Mail-Import, nur Auswahlpersistenz

Aufgaben:
1. Datenmodell für Source-Selection erweitern
2. Service ergänzen, der selektierte PST-Pfade speichert
3. API-Endpunkt für Save/Load der Auswahl hinzufügen
4. Frontend um Checkbox-Tree erweitern
5. Parent-/Child-Selektion konsistent implementieren
6. Grundlage für nächste Ausbaustufe schaffen:
   - Preview
   - tatsächlicher PST-Import

Lieferumfang:
- vollständiger Code
- Änderungsliste pro Datei
- Beschreibung der Zustandslogik
```

### VSC-Prompt 4 — Technische Härtung für Windows und Netzlaufwerke
```text
Härte den PST-Auswahl- und Ladeprozess technisch für Windows-Dateisysteme und Netzlaufwerke.

Ziel:
- Robuste Unterstützung für lokale Laufwerke und UNC-Pfade
- Saubere Validierung und Fehlerrückgabe
- Keine impliziten Annahmen über nur lokale Dateien

Berücksichtige:
- Laufwerksbuchstaben wie D:\, E:\
- UNC-Pfade wie \\server\freigabe\archiv.pst
- Berechtigungsfehler
- nicht erreichbare Netzfreigaben
- große PST-Dateien

Aufgaben:
1. Pfadvalidierung zentralisieren
2. UNC-Pfade korrekt behandeln
3. Lesbarkeitsprüfung vor Parsing einbauen
4. Timeouts / kontrollierte Fehlerbehandlung vorsehen
5. Logging für Diagnosefälle ergänzen
6. Rückgabefehler für Frontend standardisieren

Lieferumfang:
- konkrete Backend-Anpassungen
- Fokus auf Robustheit, Fehlermodell und Wartbarkeit
```

Ab jetzt folgt dieses Muster:
1. Fachliche Antwort  
2. Implementierungsfolgen / Risiken  
3. **VSC-Prompts** für den nächsten oder aktuellen Schritt

### 7. Benutzer

weiter

### 8. Assistent

Schritt 2 umgesetzt: Auswahlhärtung, Import-Vorschau und Importlauf fachlich stabilisiert.

Artefakt:
[WDB_20-main-pst-step2-preview-import.zip](sandbox:/mnt/data/WDB_20-main-pst-step2-preview-import.zip)

Umgesetzte Änderungen

Backend:
- `ImportPreviewResponse` erweitert:
  - `effective_selected_count`
  - `estimated_message_count`
  - `node_path`
  - `message_count`
- Preview-Logik entdoppelt verschachtelte Selektionen.
  - Fall vorher: Parent + Child selektiert → doppelte Preview-Einträge
  - Fall jetzt: nur effektive Importwurzeln werden angezeigt
- `POST /sources/{source_id}/import-jobs`
  - leerer Selektionsfall mit sauberer `400`-Fehlermeldung
- `ImportRunResponse` erweitert:
  - `selected_folder_paths`
  - `started_at`
  - `finished_at`

Frontend:
- Tree-Komponente auf fachlich korrekten Auswahlzustand erweitert:
  - Expand/Collapse
  - indeterminate/partial state
  - Knotenzähler im Teilbaum
- PST-Tree-Seite erweitert:
  - `Alle auswählen`
  - `Auswahl zurücksetzen`
  - Anzeige effektiver Importwurzeln vs. gespeicherter Knoten
- Import-Vorschau-Seite korrigiert und erweitert:
  - fehlerhafte Leerstelle/Textbruch entfernt
  - Anzeige von:
    - effektiven Importwurzeln
    - gespeicherten Knoten
    - geschätzter Mailanzahl
    - vollständigem Ordnerpfad
- ImportRun-Seite erweitert:
  - Start-/Endzeit
  - selektierte Ordnerpfade
  - Datumsausgabe formatiert

Wesentliche Systemlogik

## 1. Selektion

Vorher:
- Auswahl wurde als flache ID-Menge gespeichert
- Parent und Child konnten parallel selektiert werden
- UI zeigte das unstrukturiert

Jetzt:
- Persistenz bleibt kompatibel
- Anzeigeebene interpretiert die Selektion hierarchisch
- Effektive Importwurzel = selektierter Knoten ohne selektierten Parent

Konsequenz:
- keine doppelte Importvorschau für denselben Teilbaum
- UI zeigt echten fachlichen Zustand statt nur roher ID-Menge

## 2. Vorschau

Vorher:
- Vorschau zeigte nur selektierte Knoten
- keine Aussage über effektive Importscope
- keine grobe Mengenschätzung

Jetzt:
- Vorschau zeigt nur effektive Importwurzeln
- pro Eintrag:
  - Pfad
  - Typ
  - geschätzte Anzahl Mails im Teilbaum
- globale Metriken:
  - gespeicherte Knoten
  - effektive Wurzeln
  - geschätzte Mailanzahl

## 3. ImportRun-Transparenz

Vorher:
- Ergebnis zeigte Mails und Attachments
- Herkunftsordner des Runs nur indirekt sichtbar

Jetzt:
- ImportRun zeigt:
  - selektierte Folder-Pfade
  - Startzeit
  - Endzeit
  - Statusverlauf besser nachvollziehbar

Betroffene Dateien

Backend:
- `backend/app/models/import_models.py`
- `backend/app/services/import_preview_service.py`
- `backend/app/api/routes/import_jobs.py`
- `backend/app/api/routes/import_runs.py`
- `backend/app/models/pst_import_models.py`

Frontend:
- `frontend/src/types/importPreview.ts`
- `frontend/src/types/pstImport.ts`
- `frontend/src/components/sources/SourceTreeView.tsx`
- `frontend/src/pages/PstTreePage.tsx`
- `frontend/src/pages/PstImportPreviewPage.tsx`
- `frontend/src/pages/PstImportRunPage.tsx`
- `frontend/src/index.css`

Validierung

Erfolgreich:
- Python-Compilecheck im Backend

Nicht belastbar validiert:
- Frontend-Build
- Grund: `node_modules` in der bereitgestellten Umgebung nicht vorhanden

Verbleibende Risiken

- Importausführung bleibt synchron im Prozess.
  - Große PSTs blockieren API-Thread und UI-Wahrnehmung.
- ImportRun-Store bleibt In-Memory.
  - Neustart verliert Laufhistorie.
- Preview-Mengen basieren auf `item_count`/Teilbaumaggregation.
  - Das ist für PST-Ordner praktikabel, aber keine harte Importgarantie.
- Selektion wird weiterhin als vollständige Knotenmengen gespeichert.
  - Fachlich sauberer wäre später ein kompaktes Modell nur mit effektiven Wurzeln.

Nächster sinnvoller Schritt

Schritt 3:
- echten robusten PST-Importlauf absichern:
  - persistenter ImportRun-Store auf Datei-/DB-Basis
  - Fortschrittsmetriken
  - Abbruch-/Retry-Mechanik
  - Deduplikation nach `message_id`
  - Batchweises Neo4j-Ingest statt monolithischem Run

## VSC-Prompts

### VSC-Prompt 1 — Persistenten ImportRun-Store implementieren
```text
Implementiere für PST-Importe einen persistenten ImportRun-Store statt In-Memory.

Ziel:
- ImportRuns über Neustarts hinweg erhalten
- Status, Metriken und importierte E-Mails reproduzierbar speichern
- Grundlage für Retry, Verlauf und Diagnose schaffen

Rahmenbedingungen:
- FastAPI Backend
- Bestehende ImportRun-Modelle weiterverwenden
- JSON-Datei oder leichtgewichtige lokale Persistenz bevorzugen
- Keine Einführung schwerer Infrastruktur

Aufgaben:
1. Ersetze den In-Memory-Store für ImportRuns durch einen persistenten Store
2. Speichere pro ImportRun:
   - import_run_id
   - source_id
   - source_path
   - selected_node_ids
   - selected_folder_paths
   - status
   - started_at
   - finished_at
   - email_count
   - attachment_count
   - error_message
3. Speichere importierte E-Mails strukturiert und getrennt vom Metadatensatz, falls sinnvoll
4. Implementiere sauberes Laden beim Service-Start
5. Achte auf Dateikorruption und Fallback-Verhalten
6. Halte API-Verträge unverändert oder nur minimal erweitert

Lieferumfang:
- vollständiger Python-Code
- Änderungen nach Datei getrennt
- Begründung der Persistenzentscheidung
```

### VSC-Prompt 2 — Fortschrittsmetriken für PST-Import einführen
```text
Erweitere den PST-Importlauf um echte Fortschrittsmetriken.

Ziel:
- Während des Imports soll sichtbar sein, wie weit der Lauf fortgeschritten ist
- UI soll nicht nur queued/running/finished/failed kennen, sondern auch Fortschrittswerte

Anforderungen:
- Backend und Frontend konsistent erweitern
- Fortschritt auf Ordner- und Nachrichtenebene modellieren
- Keine Fake-Prozente, sondern nachvollziehbare Metriken

Aufgaben:
1. Ergänze das ImportRun-Modell um:
   - total_folder_count
   - processed_folder_count
   - total_message_count_estimate
   - processed_message_count
   - progress_percent
2. Berechne Fortschritt während der PST-Verarbeitung fortlaufend
3. Aktualisiere den ImportRun-Store während des Laufs
4. Gib Fortschritt über GET /import-runs/{import_run_id} zurück
5. Zeige Fortschritt im Frontend als Kennzahl und Fortschrittsbalken
6. Definiere Verhalten bei unbekannten Gesamtmengen sauber

Lieferumfang:
- vollständiger Code
- Modelländerungen Backend + Frontend
- Beschreibung der Fortschrittslogik
```

### VSC-Prompt 3 — Deduplikation im PST-Import einbauen
```text
Implementiere Deduplikation für importierte E-Mails im PST-Import.

Ziel:
- Doppelte Nachrichten aus mehreren PST-Ordnern oder mehrfachen Läufen erkennen
- Grundlage für robuste Persistenz und Graph-Ingest schaffen

Priorität:
- Primär nach message_id
- Fallback für Fälle ohne brauchbare message_id

Aufgaben:
1. Definiere eine Deduplikationsstrategie:
   - primary key: message_id
   - fallback hash über subject + sender + sent_at + body_text-Auszug
2. Verhindere doppelte Aufnahme innerhalb eines ImportRuns
3. Bereite Hook vor, um später run-übergreifend zu deduplizieren
4. Ergänze Metriken:
   - imported_count
   - duplicate_count
5. Logge verworfene Dubletten nachvollziehbar
6. Halte Verhalten deterministisch

Lieferumfang:
- vollständiger Python-Code
- Änderungen nach Datei getrennt
- Beschreibung der Deduplikationslogik und ihrer Grenzen
```

### VSC-Prompt 4 — Batchweises Neo4j-Ingest robust machen
```text
Baue den PST-Import so um, dass Neo4j-Ingest batchweise und fehlertolerant erfolgt.

Ziel:
- Große PST-Dateien sollen nicht monolithisch in einem Schritt persistiert werden
- Fehler sollen eingegrenzt und diagnostizierbar sein
- Speicher- und Laufzeitverhalten verbessern

Anforderungen:
- Bestehende Neo4j-Adapterstruktur weiterverwenden
- Batch-Größe konfigurierbar machen
- Teilfehler transparent behandeln

Aufgaben:
1. Teile importierte E-Mails in Batches auf
2. Persistiere jeden Batch separat nach Neo4j
3. Ergänze Run-Metriken:
   - processed_batches
   - failed_batches
   - batch_size
4. Implementiere Fehlerbehandlung pro Batch
5. Definiere Abbruchstrategie:
   - harter Abbruch oder partielle Fortsetzung
6. Schreibe saubere Logs und Statusmeldungen

Lieferumfang:
- vollständiger Python-Code
- Änderungsliste pro Datei
- klare Begründung der Batch-Strategie
```

### 9. Benutzer

erweitere die gui im Bereich PST-Datei

### 10. Assistent

GUI im Bereich **PST-Datei** erweitert.

Artefakt:
[WDB_20-main-pst-gui-extended.zip](sandbox:/mnt/data/WDB_20-main-pst-gui-extended.zip)

Umgesetzt

## 1. PST-Datei-Seite strukturell aufgewertet

Datei:
- `frontend/src/pages/PstImportPage.tsx`

Erweiterungen:
- KPI-Header für PST-Kontext:
  - aktive Quelle
  - ausgewählte Datei
  - Speichertyp
  - Browser-Einträge
- Statusbereich für aktive PST-Quelle
- fachliche Schrittlogik sichtbar gemacht:
  - „Schritt 1 von 3“
- Detailkarten für:
  - Dateiname
  - Quellenlabel
  - vollständiger Pfad
- Hilfeblöcke für:
  - lokale Laufwerke
  - Netzwerklaufwerke / UNC
  - Validierungslogik
- Browser-Toolbar erweitert:
  - Root
  - Ebene hoch
  - Schließen
- Browser-Zusammenfassung ergänzt
- aktuell ausgewählte PST-Datei im Browser visuell markiert
- Zweitaktion ergänzt:
  - direkter Sprung zur Ordnerstruktur

## 2. PST-Ordnerstruktur-Seite ausgebaut

Datei:
- `frontend/src/pages/PstTreePage.tsx`

Erweiterungen:
- KPI-Header für:
  - Ordneranzahl
  - geschätzte Mailanzahl
  - Importwurzeln
  - gespeicherte Knoten
- Suchfeld für Ordnerfilter
- Umschalter:
  - nur selektierte Teilbäume anzeigen
- Expand-Strategie steuerbar:
  - alles ausklappen
  - alles einklappen
  - Automatik
- Toolbar-Zusammenfassung:
  - Trefferanzahl
  - aktuelle Ansicht

## 3. Tree-Komponente funktional erweitert

Datei:
- `frontend/src/components/sources/SourceTreeView.tsx`

Erweiterungen:
- Suchfilter auf Knotenebene
- Sichtbarkeitslogik für gefilterte Teilbäume
- Highlighting gefundener Knoten
- Expand/Collapse-Modus steuerbar
- „Nur Auswahl“-Ansicht fachlich korrekt integriert
- Parent-Ketten für Filtertreffer automatisch geöffnet

## 4. Styling für PST-Bereich deutlich erweitert

Datei:
- `frontend/src/index.css`

Neu:
- KPI-Cards
- Detail-Cards
- Toolbar-Felder
- Hint-Boxen
- Schritt-Badge
- Browser-Zusammenfassung
- aktive Secondary-Buttons
- Highlight-Zustand im Tree
- responsive Grid-Anpassungen

## 5. Bestehenden Defekt im ImportRun-Frontend korrigiert

Datei:
- `frontend/src/pages/PstImportRunPage.tsx`

Korrektur:
- fehlerhafte String-Zusammensetzung bei `selected_folder_paths.join(...)` repariert

Architektonische Wirkung

- PST-Bereich ist jetzt als eigener Workflow lesbar.
- Nutzer sieht vor der Einbindung bereits Pfadtyp, Dateikontext und nächsten Schritt.
- Tree-Seite ist bei großen PSTs besser bedienbar.
- Selektionsprüfung wird schneller, weil Filter und Teilbaumansicht die visuelle Last reduzieren.
- UNC-/Netzpfad-Nutzung ist in der Oberfläche explizit unterstützt statt nur implizit möglich.

Validierung

Erfolgreich:
- Codeänderungen paketiert
- offensichtlicher JSX-Defekt in `PstImportRunPage.tsx` beseitigt

Nicht belastbar validierbar:
- vollständiger Frontend-Build in dieser Container-Umgebung
- Ursache: Grundabhängigkeiten/Type-Declarations fehlen im bereitgestellten Setup (`react`, `vite`, JSX runtime, Vite typings)
- Das ist kein exklusiver Fehler dieser Änderung, sondern ein Setup-Defizit der Umgebung

Geänderte Dateien

- `frontend/src/pages/PstImportPage.tsx`
- `frontend/src/pages/PstTreePage.tsx`
- `frontend/src/components/sources/SourceTreeView.tsx`
- `frontend/src/pages/PstImportRunPage.tsx`
- `frontend/src/index.css`

## VSC-Prompts

### VSC-Prompt 1 — PST-GUI um Quellenkopf und Workflow-Navigation erweitern
```text
Erweitere die React-Frontend-GUI im Bereich PST-Datei zu einem klaren 3-Schritt-Workflow.

Ziel:
- PST-Datei auswählen
- Ordnerstruktur prüfen und selektieren
- Importvorschau / Importlauf erreichen

Anforderungen:
- Bestehende Seitenstruktur weiterverwenden
- Auf der PST-Datei-Seite einen sichtbaren Workflow-Kopf einführen
- Aktive Quelle, Dateiname, Pfadtyp und nächster Schritt sollen sofort erkennbar sein

Aufgaben:
1. Ergänze auf der PST-Datei-Seite KPI-Karten für:
   - aktive Quelle
   - ausgewählte Datei
   - Speichertyp
   - Browser-Einträge
2. Füge einen sichtbaren Step-Indikator ein:
   - Schritt 1: PST auswählen
   - Schritt 2: Ordnerstruktur
   - Schritt 3: Vorschau / Import
3. Ergänze Quick-Actions:
   - Ordnerstruktur öffnen
   - Importvorschau öffnen
4. Zeige bei aktiver PST-Quelle einen klaren Statusblock
5. Halte die Komponente TypeScript-sauber und ohne Placeholder

Lieferumfang:
- vollständiger TSX-Code
- Dateiänderungen getrennt aufführen
- keine abstrakte Beschreibung, sondern direkt integrierbare Umsetzung
```

### VSC-Prompt 2 — PST-Tree um Suche, Filter und Expand-Steuerung erweitern
```text
Erweitere die PST-Ordnerstruktur-GUI im React-Frontend funktional.

Ziel:
- Große PST-Strukturen schneller navigierbar machen
- Auswahl und Prüfung großer Teilbäume vereinfachen

Anforderungen:
- Tree-Komponente rekursiv beibehalten
- Suchfilter und Expand-Strategien integrieren
- Auswahlzustände fachlich korrekt erhalten

Aufgaben:
1. Ergänze ein Suchfeld für Ordnernamen
2. Implementiere Filterlogik:
   - Treffer anzeigen
   - Parent-Kette für Treffer sichtbar halten
3. Implementiere Highlighting für Treffer
4. Ergänze Ansichtsschalter:
   - nur selektierte Teilbäume
   - gesamte Struktur
5. Ergänze Expand-Strategien:
   - alles ausklappen
   - alles einklappen
   - Automatik
6. Zeige KPI-Werte oberhalb des Trees:
   - Ordner
   - geschätzte Mails
   - Importwurzeln
   - gespeicherte Knoten

Lieferumfang:
- vollständiger TSX-Code
- notwendige CSS-Erweiterungen
- sauber typisierte Props und Hilfsfunktionen
```

### VSC-Prompt 3 — PST-Dateibrowser UX für Netzlaufwerke härten
```text
Verbessere die GUI des PST-Dateibrowsers für lokale Laufwerke und Netzlaufwerke.

Ziel:
- Navigation auf HDD, gemappten Laufwerken und UNC-Pfaden robust und verständlich machen
- Auswahlkontext in der Oberfläche klar darstellen

Anforderungen:
- React + TypeScript
- bestehende browseFilesystem-API weiterverwenden
- keine Backend-Änderungen notwendig, nur GUI/UX

Aufgaben:
1. Ergänze Toolbar-Aktionen:
   - Root
   - Ebene hoch
   - Schließen
2. Zeige Browser-Zusammenfassung:
   - aktueller Pfad
   - Anzahl Einträge
3. Markiere die aktuell gewählte PST-Datei in der Liste
4. Ergänze Hilfeboxen für:
   - lokale Laufwerke
   - UNC-Pfade
   - Validierungsregeln
5. Zeige Pfaddetails in einer separaten Detailkarte
6. Halte die Oberfläche ohne manuelle Dateieingabe der PST selbst

Lieferumfang:
- vollständiger TSX-Code
- notwendige CSS-Anpassungen
- integrierbare Lösung ohne Platzhalter
```

### VSC-Prompt 4 — PST-Bereich visuell konsistent designen
```text
Überarbeite das Styling des PST-Bereichs im Frontend, damit Auswahl, Strukturprüfung und Importvorbereitung visuell konsistent sind.

Ziel:
- Der PST-Bereich soll wie ein zusammenhängender Fachworkflow wirken
- Informationsdichte erhöhen, ohne die Bedienbarkeit zu verschlechtern

Anforderungen:
- vorhandenes CSS-System und Variablen weiterverwenden
- keine externe UI-Bibliothek
- responsive Layout beibehalten

Aufgaben:
1. Implementiere KPI-Cards für PST-Metriken
2. Implementiere Detail-Cards für Dateikontext
3. Ergänze Hint-Boxen und Step-Badges
4. Ergänze Toolbar-Stile für Filter- und Toggle-Bereiche
5. Ergänze Highlight-Stile für Tree-Treffer
6. Ergänze aktive Secondary-Button-Stile
7. Halte alle Klassen konsistent benannt

Lieferumfang:
- vollständige CSS-Erweiterung
- klare Zuordnung der neuen Klassen zu den PST-Komponenten
```
