---
title: "Toolentwicklung mit KI-Prompts"
type: chatgpt_conversation
source: chatgpt
source_id: "69b7cdd8-9f58-8396-b976-f3ce2eb91d99"
created: 2026-03-16
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
---


# Toolentwicklung mit KI-Prompts

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69b7cdd8-9f58-8396-b976-f3ce2eb91d99`
- Nachrichten: 24

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

auf basis dieser masterplan.md möchte ich mit claude, codex, github copilot und chat gpt das tool bauen. erstelle mir hierfür die jeweiligen prompts nach und nach

### 2. Assistent

Basis für die Prompt-Strategie:

- Zielarchitektur: React/Vite/TypeScript-Frontend, FastAPI-Backend, Neo4j als externe Zielinfrastruktur, alle Integrationen ausschließlich über das Backend. Kein Frontend-Zugriff auf Neo4j oder Ollama. fileciteturn0file0
- Aktueller Stand: Quellenverwaltung existiert, lokales Dokumentenscanning existiert, Analyse-Grundgerüst existiert, aber Persistenz für Jobs/Status und Analyseergebnisse ist noch nicht belastbar umgesetzt. fileciteturn0file0
- Nächster belastbarer Stand: keine direkte Frontend-Kopplung zu Neo4j/Ollama, nachvollziehbarer Review-/Freigabe-Workflow, persistente Statusführung. fileciteturn0file0

Ich setze deshalb die Prompts in einer sinnvollen Reihenfolge auf. Runde 1 fokussiert auf Architekturhärtung und Persistenzfundament. Nicht auf Features, die später wegen falscher Basis neu gebaut werden müssten.

# Runde 1: Architektur- und Persistenzfundament

## 1) Claude Prompt
Einsatz: Architekturkritik, Umsetzungsplan, Zerlegung in belastbare Arbeitspakete.

```text
Du arbeitest als Senior Software Architect und Technical Product Owner.

Kontext:
Ich baue eine lokale Wissens- und Analyseplattform mit folgendem Zielbild:
- Frontend: React + Vite + TypeScript
- Backend: FastAPI
- Datenbank: externe Neo4j Aura oder Self-Managed Neo4j
- KI-Provider: Ollama lokal, optional DnaBot
- Parsing: PST später neu, lokal bereits PDF/DOCX/TXT/EML
- Architekturregel: kein Frontend-zu-Neo4j-Zugriff, kein Frontend-zu-Ollama-Zugriff, alle Integrationen nur über das Backend
- Rohdaten nie überschreiben
- Freigegebene Analyseergebnisse getrennt persistieren

Ist-Zustand:
- FastAPI-Backend vorhanden
- React-/Vite-Frontend vorhanden
- Quellenverwaltung vorhanden
- Dokumentenscanning lokal vorhanden
- Analyse-Grundgerüst vorhanden
- Persistenz für Jobs/Importstatus ist noch nicht belastbar
- Analyseergebnisse werden noch nicht in Neo4j persistiert
- PST-Pipeline ist zurückgesetzt und derzeit kein Umsetzungsschwerpunkt

Domänenobjekte:
- SourceSystem / Source
- ImportRun
- Folder
- Email
- Document
- Attachment
- Topic
- Entity
- AnalysisResult
- MergedCase

Roadmap-Prio jetzt:
Phase 1: Persistenz & Stabilität
- Job- und Import-Status von In-Memory auf dauerhafte Persistenz umstellen
- Analyse-Ergebnisse dauerhaft speichern
- robusteres Error Handling
- Encoding-Bereinigung

Deine Aufgabe:
1. Leite aus dem Kontext eine saubere Zielstruktur für Backend, Frontend und Persistenzschicht ab.
2. Definiere die minimal belastbare Architektur für Phase 1.
3. Schlage konkrete Module, Verantwortlichkeiten und Schnittstellen vor.
4. Benenne technische Risiken, versteckte Abhängigkeiten und typische Fehlentscheidungen.
5. Formuliere einen priorisierten Implementierungsplan in 8-12 Schritten.
6. Liefere Entscheidungstabellen für:
   - SQLite vs andere lokale Persistenzoptionen für Jobs/Status
   - synchrone vs asynchrone Job-Ausführung
   - Zwischenspeicherung von Analyseergebnissen lokal vs direkt nach Neo4j
7. Gib am Ende eine “Definition of Done” für Phase 1 aus.

Antwortformat:
- Annahmen
- Zielarchitektur Phase 1
- Modulzuschnitt
- API-/Datenmodell-Empfehlung
- Risiken / Failure Modes
- Priorisierte Implementierungsschritte
- Definition of Done

Wichtig:
- Keine generischen Best Practices ohne Bezug zum Kontext
- Beurteile Trade-offs explizit
- Denke in Änderbarkeit, Wiederanlauf, Fehlerisolierung und Reviewbarkeit
```

## 2) Codex Prompt
Einsatz: konkrete Backend-Umsetzung für Persistenz, Services, Modelle, APIs.

```text
Arbeite als erfahrener Python/FastAPI-Entwickler in einer bestehenden Codebasis.

Ziel:
Implementiere das Persistenzfundament für eine Wissens- und Analyseplattform.

Architekturregeln:
- Kein Frontend-Zugriff auf Neo4j
- Kein Frontend-Zugriff auf Ollama
- Alle Integrationen nur über FastAPI-Backend
- Rohdaten nie überschreiben
- Analyseergebnisse getrennt von Rohdaten persistieren

Bestehender Kontext:
- FastAPI-Backend existiert
- Analyse-Service existiert bereits als Grundgerüst
- Quellenverwaltung existiert
- Dokumentenscanning existiert
- Job-/Importstatus ist aktuell In-Memory
- Analyseergebnisse werden noch nicht dauerhaft gespeichert
- Ziel ist zuerst lokale belastbare Persistenz, Neo4j-Anbindung folgt danach für freigegebene Ergebnisse

Implementiere jetzt Phase 1 mit Fokus auf:
1. lokale dauerhafte Persistenz für Jobs, ImportRuns und Analysezustände
2. saubere Service-Schicht
3. belastbare Statusübergänge
4. Error Handling
5. Wiederanlauf-Fähigkeit nach Neustart

Erwartete Deliverables:
- Vorschlag für Verzeichnisstruktur
- Datenmodelle / Schemas
- Persistenzlayer
- Service-Layer
- API-Endpunkte
- Statusmodell als Enum / State Machine
- Beispielmigration oder Initialisierung
- Tests für Kernlogik

Anforderungen:
- Bevorzuge SQLite mit SQLAlchemy oder SQLModel, falls die bestehende Codebasis nichts Besseres vorgibt
- Trenne API-Modelle, Domainlogik und Persistenzmodelle
- Definiere ImportRun-Status und AnalysisRun-Status explizit
- Jeder Lauf braucht:
  - ID
  - Source-ID
  - Typ
  - Startzeit
  - Endzeit
  - Status
  - Fehlertext
  - Zähler für Dateien/Erfolge/Fehler
- Analyseergebnisse lokal persistent speichern, noch nicht nach Neo4j schreiben
- Implementiere Idempotenz und sichere Wiederaufnahme, wo sinnvoll
- Keine Schein-Asynchronität; wenn echte Hintergrundjobs fehlen, Statusmodell trotzdem vorbereiten
- Bestehende In-Memory-Logik nur ersetzen, wenn Migration konsistent möglich ist

Arbeitsmodus:
1. Analysiere zunächst die mutmaßlich nötigen Dateien und Komponenten.
2. Formuliere dann einen konkreten Änderungsplan.
3. Erzeuge danach den Code schrittweise mit Begründung pro Block.
4. Markiere Annahmen explizit.
5. Zeige am Ende offene Integrationspunkte.

Wichtig:
- Keine Platzhalterarchitektur
- Keine harte Kopplung an Neo4j im Frontend
- Keine unkontrollierte Vermischung von Rohimport und fachlicher Analysepersistenz
```

## 3) GitHub Copilot Prompt
Einsatz: direkt im Editor für konkrete Dateiänderungen und Refactorings.

```text
Kontext der Codebasis:

Ich entwickle eine Wissens- und Analyseplattform mit:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- externer Neo4j-Zielinfrastruktur
- KI-Zugriff nur über Backend
- lokaler Persistenz für Jobs/Status/Analyseergebnisse als nächster Umsetzungsschritt

Bitte hilf mir beim Refactoring und Ausbau des Backends.

Ziele dieses Tasks:
- In-Memory Job-/Importstatus durch dauerhafte Persistenz ersetzen
- Analyseergebnisse lokal persistent speichern
- Service-Layer klar trennen
- Statusmodell robust definieren
- Fehlerfälle und Wiederanlauf berücksichtigen

Erzeuge oder überarbeite Code so, dass folgende Struktur unterstützt wird:
- models/
- schemas/
- services/
- repositories/
- api/routes/
- db/

Konkrete Anforderungen:
- SQLite-basierte Persistenz
- SQLAlchemy oder SQLModel
- ImportRun und AnalysisRun mit klaren Status-Enums
- Felder für IDs, Status, Zeitstempel, Fehler, Zählerstände
- Repository-Methoden für create/get/list/update-status
- API-Endpunkte zum Starten, Abfragen und Auflisten von Runs
- saubere Pydantic-Schemas
- defensive Fehlerbehandlung
- möglichst kleine, reviewbare Commits/Änderungen

Beachte:
- keine direkte Neo4j- oder Ollama-Logik im Frontend
- Analyseergebnisse getrennt von Rohdaten behandeln
- noch keine Persistierung nach Neo4j in diesem Task
- vorhandene Services möglichst weiterverwenden statt blind neu schreiben

Arbeite bevorzugt dateibasiert:
1. zeige zuerst die wahrscheinlich betroffenen Dateien
2. schlage dann konkrete Änderungen pro Datei vor
3. generiere anschließend implementierbaren Code
4. markiere TODOs nur dort, wo echte Anschlussarbeiten außerhalb dieses Tasks liegen
```

## 4) ChatGPT Prompt
Einsatz: Spezifikation, Review, Akzeptanzkriterien, Teststrategie.

```text
Arbeite als Product Owner, Systems Analyst und Software Reviewer.

Ich baue eine Wissens- und Analyseplattform mit diesem Rahmen:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- Neo4j als externe Zielinfrastruktur
- lokale oder optionale externe KI-Provider nur über Backend
- Dokumentenscanning bereits vorhanden
- Analyse-Grundgerüst bereits vorhanden
- Persistenz und Betriebsstabilität sind der aktuelle Engpass

Fokus dieser Ausarbeitung:
Phase 1 – Persistenz & Stabilität

Erstelle eine umsetzbare Spezifikation für diese Phase.

Benötigt:
1. fachliche Ziele
2. Nicht-Ziele
3. Domänenmodell für ImportRun, AnalysisRun, Source und AnalysisResult
4. Statusmodell mit zulässigen Zustandsübergängen
5. API-Kontrakte
6. Akzeptanzkriterien
7. Testfälle
8. Betriebsrisiken
9. Messgrößen / Telemetrie
10. Definition of Done

Rahmenbedingungen:
- Frontend darf nie direkt auf Neo4j oder Ollama zugreifen
- Analyseergebnisse zunächst lokal persistent speichern
- Freigegebene Ergebnisse werden später getrennt nach Neo4j geschrieben
- Rohdaten und fachliche Ergebnisse müssen getrennt bleiben
- Lösung muss Neustarts, Teilfehler und defekte Dateien verkraften

Antwortformat:
- Zielbild
- Scope / Out of Scope
- Domänenmodell
- Zustandsautomat
- API-Spezifikation
- Akzeptanzkriterien
- Negativfälle / Edge Cases
- Teststrategie
- Betriebsmetriken
- Definition of Done

Zusatz:
Fokussiere auf konkrete Entscheidungsfähigkeit. Keine allgemeine Lehrbuchbeschreibung.
```

# Empfohlene Einsatzlogik

Nicht alle Modelle für denselben Job verwenden. Sonst entsteht Redundanz statt Fortschritt.

- Claude: Architekturprüfung, Zerlegung, Risikoanalyse
- Codex: Implementierung Backend Phase 1
- GitHub Copilot: dateinahe Codegenerierung und Refactoring im Editor
- ChatGPT: Spezifikation, Review, Akzeptanzkriterien, Testfälle

# Nächste sinnvolle Sequenz

Reihenfolge der Nutzung:

1. Claude: Zielstruktur und Umsetzungsplan festziehen
2. ChatGPT: daraus belastbare Spezifikation und Akzeptanzkriterien ableiten
3. Codex: Backend-Persistenz implementieren
4. GitHub Copilot: konkrete Dateiänderungen, Refactoring, Boilerplate und Tests im Projekt ausführen

# Warum diese Runde zuerst

Der Masterplan zeigt, dass nicht Features, sondern Persistenz, Stabilität und saubere Trennung der Verantwortlichkeiten der aktuelle Engpass sind. Analyse nach Neo4j ist ausdrücklich noch offen, ebenso belastbare Statuspersistenz. Genau diese Schicht entscheidet über Wiederanlauf, Nachvollziehbarkeit und spätere Erweiterbarkeit. fileciteturn0file0

Als Nächstes folgt Runde 2: Prompts für Quellenvalidierung, ImportRun-Workflow und lokale Analysepersistenz.

### 3. Benutzer

Arbeite als Product Owner, Systems Analyst und Software Reviewer.



Ich baue eine Wissens- und Analyseplattform mit diesem Rahmen:

- React/Vite/TypeScript Frontend

- FastAPI Backend

- Neo4j als externe Zielinfrastruktur

- lokale oder optionale externe KI-Provider nur über Backend

- Dokumentenscanning bereits vorhanden

- Analyse-Grundgerüst bereits vorhanden

- Persistenz und Betriebsstabilität sind der aktuelle Engpass



Fokus dieser Ausarbeitung:

Phase 1 – Persistenz & Stabilität



Erstelle eine umsetzbare Spezifikation für diese Phase.



Benötigt:

1. fachliche Ziele

2. Nicht-Ziele

3. Domänenmodell für ImportRun, AnalysisRun, Source und AnalysisResult

4. Statusmodell mit zulässigen Zustandsübergängen

5. API-Kontrakte

6. Akzeptanzkriterien

7. Testfälle

8. Betriebsrisiken

9. Messgrößen / Telemetrie

10. Definition of Done



Rahmenbedingungen:

- Frontend darf nie direkt auf Neo4j oder Ollama zugreifen

- Analyseergebnisse zunächst lokal persistent speichern

- Freigegebene Ergebnisse werden später getrennt nach Neo4j geschrieben

- Rohdaten und fachliche Ergebnisse müssen getrennt bleiben

- Lösung muss Neustarts, Teilfehler und defekte Dateien verkraften



Antwortformat:

- Zielbild

- Scope / Out of Scope

- Domänenmodell

- Zustandsautomat

- API-Spezifikation

- Akzeptanzkriterien

- Negativfälle / Edge Cases

- Teststrategie

- Betriebsmetriken

- Definition of Done



Zusatz:

Fokussiere auf konkrete Entscheidungsfähigkeit. Keine allgemeine Lehrbuchbeschreibung.

### 4. Assistent

## Zielbild

Phase 1 stabilisiert den operativen Kern zwischen Quelle, Import, Analyse und lokaler Nachvollziehbarkeit. Ziel ist nicht fachliche Vollausprägung des Wissensgraphen, sondern ein belastbarer Ausführungs- und Persistenzrahmen mit klarer Trennung zwischen Rohdaten, Analysezustand und späterer Freigabe in Richtung Neo4j. Der Masterplan priorisiert dafür explizit dauerhafte Persistenz für Jobs/Importstatus, lokale Speicherung von Analyseergebnissen, robusteres Fehlerhandling und Encoding-Bereinigung. fileciteturn1file2

Architekturziel für Phase 1:
- Frontend nur gegen FastAPI.
- FastAPI kapselt alle Integrationen.
- Neo4j bleibt externe Zielinfrastruktur und wird in Phase 1 nicht als operative Primärpersistenz für Analysezustände verwendet.
- Rohimport und fachliche Analyse bleiben persistenzseitig getrennt.
- Neustarts dürfen laufende oder abgebrochene Vorgänge nicht unkenntlich machen. fileciteturn1file0 fileciteturn1file2

Operativer Sollzustand nach Phase 1:
- jeder ImportRun und jeder AnalysisRun ist dauerhaft gespeichert,
- jeder Statuswechsel ist nachvollziehbar,
- Teilfehler und defekte Dateien führen nicht zum Totalverlust des Laufs,
- Analyseergebnisse liegen lokal persistent vor,
- Freigabe nach Neo4j ist noch bewusst nicht Bestandteil dieser Phase. fileciteturn1file2turn1file4

## Scope / Out of Scope

### Scope
- Persistente lokale Speicherung für ImportRuns, AnalysisRuns und AnalysisResults.
- Ersatz von In-Memory-Status durch dauerhafte Statusführung.
- Wiederanlauf- und Recovery-Logik nach Prozessneustart.
- Fehlerisolierung auf Datei-/Dokumentebene.
- Quelle bleibt als registriertes Objekt mit Validierungsstatus erhalten.
- API für Start, Statusabfrage, Auflistung und Ergebnisabfrage.
- Encoding-Bereinigung in Status-, Fehler- und UI-relevanten Texten als Betriebsqualitätsmaßnahme. fileciteturn1file2

### Out of Scope
- Persistierung freigegebener Analyseergebnisse nach Neo4j.
- Entity Linking, Clusterbildung, Wissensgraph-Anreicherung.
- semantische Suche, Embeddings, Chat/RAG.
- PST-Neuentwicklung als Pipeline-Schwerpunkt.
- Frontend-seitige Fachlogik für Analyse oder Provider-Steuerung.
- echte verteilte Job-Orchestrierung; vorbereitet wird nur ein belastbares Statusmodell. fileciteturn1file2turn1file3

### Architekturentscheidung
Für Phase 1 ist lokale relationale Persistenz die zweckmäßige Basis. Der Masterplan nennt SQLite oder ähnliche lokale Persistenz explizit als Folgeschritt für Jobs und Status. SQLite ist ausreichend, weil der Engpass nicht horizontale Skalierung, sondern Wiederanlauf, Nachvollziehbarkeit und Zustandskonsistenz ist. fileciteturn1file0

## Domänenmodell

### 1. Source
Repräsentiert eine registrierte Quelle, nicht den konkreten Ausführungslauf.

**Felder**
- `source_id` UUID
- `source_system` enum: `LOCAL_FOLDER`, `PST`, später erweiterbar
- `display_name`
- `location_uri` oder lokaler Pfad
- `is_active`
- `validation_status` enum: `UNKNOWN`, `VALID`, `INVALID`, `INACCESSIBLE`
- `last_validated_at`
- `validation_message`
- `created_at`
- `updated_at`

**Semantik**
- Source ist langlebig.
- Source-Änderungen erzeugen nicht automatisch einen neuen ImportRun.
- Source enthält keine Laufzeitmetriken.

### 2. ImportRun
Repräsentiert einen einzelnen Import-/Scanlauf gegen genau eine Source.

**Felder**
- `import_run_id` UUID
- `source_id` FK
- `run_type` enum: `SCAN_ONLY`, `SCAN_AND_PARSE`
- `status` enum
- `started_at`
- `finished_at`
- `triggered_by` optional
- `restart_of_run_id` optional FK
- `resume_token` optional
- `files_discovered_count`
- `files_processed_count`
- `files_succeeded_count`
- `files_failed_count`
- `folders_scanned_count`
- `warning_count`
- `error_count`
- `last_error_code`
- `last_error_message`
- `status_message`
- `created_at`
- `updated_at`

**Kinder / zugeordnete Datensätze**
- `ImportRunItem` für jede Datei/Dokumenteinheit
- optional `ImportRunEvent` für Audit/Timeline

**Semantik**
- ImportRun beschreibt Rohdatenverarbeitung.
- Keine fachlichen KI-Ergebnisse direkt im ImportRun speichern.
- Defekte Dateien werden auf Item-Ebene protokolliert, nicht nur aggregiert.

### 3. AnalysisRun
Repräsentiert einen Analyselauf auf Basis eines abgeschlossenen oder ausreichend fortgeschrittenen ImportRuns.

**Felder**
- `analysis_run_id` UUID
- `import_run_id` FK
- `source_id` FK redundanzarm ableitbar, aber für schnelle Filterung zulässig
- `provider` enum/string: `OLLAMA`, `DNABOT`, `OTHER`
- `provider_model`
- `status` enum
- `started_at`
- `finished_at`
- `restart_of_run_id` optional FK
- `documents_targeted_count`
- `documents_analyzed_count`
- `documents_succeeded_count`
- `documents_failed_count`
- `warning_count`
- `error_count`
- `last_error_code`
- `last_error_message`
- `status_message`
- `created_at`
- `updated_at`

**Semantik**
- AnalysisRun referenziert den Rohimport, überschreibt ihn aber nie.
- Provider-spezifische Laufdetails dürfen gespeichert werden, aber nicht die Zugangsdaten.

### 4. AnalysisResult
Repräsentiert das lokal gespeicherte fachliche Ergebnis pro analysierter Einheit.

**Felder**
- `analysis_result_id` UUID
- `analysis_run_id` FK
- `import_run_item_id` FK oder `raw_document_id`/`raw_email_id` FK
- `result_type` enum: `SUMMARY`, `ENTITY_EXTRACTION`, `TOPIC_ASSIGNMENT`, `CLASSIFICATION`, `RAW_PROVIDER_OUTPUT`
- `review_status` enum: `UNREVIEWED`, `APPROVED`, `REJECTED`, `SUPERSEDED`
- `schema_version`
- `input_hash`
- `output_payload` JSON
- `normalized_payload` JSON optional
- `confidence_score` optional
- `provider`
- `provider_model`
- `generated_at`
- `approved_at` optional
- `approved_by` optional
- `supersedes_result_id` optional FK
- `created_at`
- `updated_at`

**Semantik**
- AnalysisResult ist fachliche Persistenzstufe.
- Freigabezustand wird lokal vorgehalten.
- Export nach Neo4j erfolgt später nur aus freigegebenen Ergebnissen. Das folgt direkt aus der Trennung “Review im Frontend” vor “Freigegebene Ergebnisse nach Neo4j schreiben”. fileciteturn1file1

### Ergänzendes Modell: ImportRunItem
Nicht explizit angefordert, aber operativ notwendig. Ohne dieses Objekt bleiben Teilfehler, Wiederaufnahme und Dokumentstatus unpräzise.

**Felder**
- `import_run_item_id` UUID
- `import_run_id` FK
- `relative_path` / `resource_identifier`
- `content_type`
- `discovered_at`
- `parse_status` enum
- `normalization_status` enum
- `raw_metadata` JSON
- `raw_text_path` oder `raw_text_blob_ref`
- `content_hash`
- `error_code`
- `error_message`

**Begründung**
Ein ImportRun ohne Item-Ebene kann nur Gesamtzustände liefern. Für Recovery, Idempotenz und defekte Einzeldateien ist das unzureichend.

## Zustandsautomat

### 1. ImportRun Statusmodell
Empfohlenes Enum:
- `CREATED`
- `QUEUED`
- `RUNNING`
- `PARTIALLY_COMPLETED`
- `COMPLETED`
- `FAILED`
- `CANCELLED`
- `ABANDONED`

**Zulässige Übergänge**
- `CREATED -> QUEUED`
- `QUEUED -> RUNNING`
- `RUNNING -> COMPLETED`
- `RUNNING -> PARTIALLY_COMPLETED`
- `RUNNING -> FAILED`
- `RUNNING -> CANCELLED`
- `QUEUED -> CANCELLED`
- `RUNNING -> ABANDONED` bei Prozessabbruch/Crash-Erkennung nach Neustart
- `ABANDONED -> QUEUED` für expliziten Resume/Retry
- `FAILED -> QUEUED` für Retry als neuer oder referenzierter Restart-Lauf

**Regeln**
- `COMPLETED`, `FAILED`, `CANCELLED` sind terminal, außer durch neuen Restart-Lauf.
- `PARTIALLY_COMPLETED` ist fachlich terminal für diesen Lauf, aber analysierbar für erfolgreiche Teilmengen.
- Nach Neustart wird ein vormals `RUNNING` markierter Lauf nicht automatisch auf `FAILED`, sondern auf `ABANDONED` gesetzt. Das trennt fachlichen Fehler von Prozessabbruch.

### 2. AnalysisRun Statusmodell
Empfohlenes Enum:
- `CREATED`
- `QUEUED`
- `RUNNING`
- `PARTIALLY_COMPLETED`
- `COMPLETED`
- `FAILED`
- `CANCELLED`
- `ABANDONED`

**Zulässige Übergänge**
identisch zum ImportRun.

**Zusatzregel**
- Start nur zulässig, wenn zugehöriger ImportRun in `COMPLETED` oder `PARTIALLY_COMPLETED` ist.
- Analyse darf auf Teilmenge erfolgreicher ImportItems laufen.

### 3. AnalysisResult Review-Status
- `UNREVIEWED`
- `APPROVED`
- `REJECTED`
- `SUPERSEDED`

**Zulässige Übergänge**
- `UNREVIEWED -> APPROVED`
- `UNREVIEWED -> REJECTED`
- `APPROVED -> SUPERSEDED`
- `REJECTED -> SUPERSEDED`

**Nicht zulässig**
- direkte Rücksetzung von `APPROVED` auf `UNREVIEWED`
- Mehrfachfreigabe konkurrierender Ergebnisse ohne Supersession-Regel

### 4. ImportRunItem Parse-Status
- `DISCOVERED`
- `PARSED`
- `NORMALIZED`
- `FAILED`
- `SKIPPED`

Dieses zusätzliche Statusobjekt ist erforderlich, damit Teilfehler nicht auf Gesamtlauf-Ebene maskiert werden.

## API-Spezifikation

API bleibt ausschließlich Backend-zentriert. Keine Frontend-Direktkopplung an Neo4j oder Ollama. Das ist feste Architekturregel des Masterplans. fileciteturn1file0

### 1. Sources

**POST `/api/sources`**  
Anlegen/Registrieren einer Quelle.

Request:
```json
{
  "sourceSystem": "LOCAL_FOLDER",
  "displayName": "Mandant A Dokumente",
  "locationUri": "/data/mandant_a",
  "isActive": true
}
```

Response `201`:
```json
{
  "sourceId": "uuid",
  "validationStatus": "UNKNOWN",
  "createdAt": "timestamp"
}
```

**GET `/api/sources`**  
Liste registrierter Quellen.

**GET `/api/sources/{sourceId}`**  
Detailansicht.

**POST `/api/sources/{sourceId}/validate`**  
Prüft Existenz, Lesbarkeit, grundlegende Konsistenz.

Response:
```json
{
  "sourceId": "uuid",
  "validationStatus": "VALID",
  "validationMessage": "directory readable",
  "lastValidatedAt": "timestamp"
}
```

### 2. ImportRuns

**POST `/api/import-runs`**  
Startet einen neuen ImportRun.

Request:
```json
{
  "sourceId": "uuid",
  "runType": "SCAN_AND_PARSE"
}
```

Response `202`:
```json
{
  "importRunId": "uuid",
  "status": "QUEUED"
}
```

**GET `/api/import-runs/{importRunId}`**  
Status, Zählerstände, Zeitstempel, letzte Fehler.

Response:
```json
{
  "importRunId": "uuid",
  "sourceId": "uuid",
  "status": "RUNNING",
  "startedAt": "timestamp",
  "finishedAt": null,
  "counters": {
    "filesDiscovered": 1200,
    "filesProcessed": 430,
    "filesSucceeded": 420,
    "filesFailed": 10
  },
  "lastErrorCode": "PDF_PARSE_ERROR",
  "lastErrorMessage": "corrupt cross-reference table"
}
```

**GET `/api/import-runs`**  
Filterbar nach `sourceId`, `status`, `createdAfter`, `limit`.

**GET `/api/import-runs/{importRunId}/items`**  
Liefert Item-Status mit Pagination und Fehlerdetails.

**POST `/api/import-runs/{importRunId}/retry`**  
Startet neuen Lauf mit Bezug auf abgebrochenen/fehlgeschlagenen Lauf.

Response `202`:
```json
{
  "importRunId": "new-uuid",
  "restartOfRunId": "old-uuid",
  "status": "QUEUED"
}
```

**POST `/api/import-runs/{importRunId}/cancel`**  
Kooperativer Abbruch.

### 3. AnalysisRuns

**POST `/api/analysis-runs`**  
Startet einen Analyselauf auf Basis eines ImportRuns.

Request:
```json
{
  "importRunId": "uuid",
  "provider": "OLLAMA",
  "providerModel": "llama3",
  "scope": "SUCCESSFUL_ITEMS_ONLY"
}
```

Response `202`:
```json
{
  "analysisRunId": "uuid",
  "status": "QUEUED"
}
```

**GET `/api/analysis-runs/{analysisRunId}`**  
Status, Zähler, Provider, Fehler.

**GET `/api/analysis-runs`**  
Liste/Filter.

**POST `/api/analysis-runs/{analysisRunId}/retry`**  
Neuer Lauf auf Basis desselben ImportRuns oder nur fehlgeschlagener Items.

**POST `/api/analysis-runs/{analysisRunId}/cancel`**  
Kooperativer Abbruch.

### 4. AnalysisResults

**GET `/api/analysis-runs/{analysisRunId}/results`**  
Liste lokaler Analyseergebnisse.

**GET `/api/analysis-results/{analysisResultId}`**  
Detailansicht.

**POST `/api/analysis-results/{analysisResultId}/review`**  
Setzt Review-Status.

Request:
```json
{
  "reviewStatus": "APPROVED",
  "reviewComment": "fachlich plausibel"
}
```

Response:
```json
{
  "analysisResultId": "uuid",
  "reviewStatus": "APPROVED",
  "approvedAt": "timestamp"
}
```

### API-Regeln
- Alle Start-Endpunkte liefern `202 Accepted`, nicht `200`, da Lauf und Rückgabe zeitlich getrennt sind.
- Status-Endpunkte liefern terminale und nichtterminale Zustände konsistent.
- Fehlercodes standardisieren: `SOURCE_NOT_FOUND`, `SOURCE_INVALID`, `RUN_NOT_RETRYABLE`, `PROVIDER_UNAVAILABLE`, `ITEM_PARSE_FAILED`, `INVALID_STATE_TRANSITION`.
- Keine API für direkten Neo4j-Write in Phase 1.

## Akzeptanzkriterien

### A. Persistenz
1. Ein gestarteter ImportRun bleibt nach Backend-Neustart abrufbar, inklusive Status, Zählerständen und Fehlertext.  
2. Ein gestarteter AnalysisRun bleibt nach Backend-Neustart abrufbar.  
3. AnalysisResults sind lokal dauerhaft gespeichert und nach Neustart unverändert abrufbar.  
4. Source-Definitionen, Laufzustände und Analyseergebnisse sind persistenzseitig getrennt.  
5. Rohdaten werden durch Analyse nicht überschrieben. fileciteturn1file0turn1file2

### B. Zustandskonsistenz
6. Ungültige Statusübergänge werden serverseitig abgelehnt.  
7. Ein AnalysisRun kann nicht gestartet werden, wenn der referenzierte ImportRun weder `COMPLETED` noch `PARTIALLY_COMPLETED` ist.  
8. Ein abgestürzter `RUNNING`-Lauf wird nach Neustart deterministisch als `ABANDONED` markiert oder in einen definierten Recovery-Pfad überführt.  
9. `PARTIALLY_COMPLETED` wird gesetzt, wenn mindestens ein Item erfolgreich und mindestens ein Item fehlgeschlagen ist.

### C. Fehlerisolierung
10. Eine defekte Datei beendet nicht den gesamten ImportRun, sofern der Fehler auf Item-Ebene isolierbar ist.  
11. Fehlerhafte Analyse eines einzelnen Dokuments beendet nicht zwingend den gesamten AnalysisRun.  
12. Fehlercodes und Fehlertexte werden pro Lauf und pro Item persistent gespeichert.

### D. API-Verhalten
13. Alle Lauf-Endpunkte liefern stabile IDs und wiederholbare Antworten.  
14. Polling auf Status-Endpunkte zeigt monoton konsistente Fortschrittswerte.  
15. Review-Status eines AnalysisResult ist separat änderbar, ohne Rohdaten anzufassen.

### E. Architektur
16. Frontend enthält keine Neo4j-Credentials und keine direkte Provider-Kommunikation.  
17. Kein API-Endpunkt in Phase 1 schreibt freigegebene Ergebnisse nach Neo4j. fileciteturn1file0turn1file4

## Negativfälle / Edge Cases

1. **Quelle gelöscht oder Pfad nach Registrierung nicht mehr lesbar**  
   Source bleibt erhalten, Validierungsstatus wird `INACCESSIBLE`, neue Runs werden abgelehnt.

2. **Datei-Encoding defekt oder uneinheitlich**  
   Item auf `FAILED`, Fehlercode z. B. `ENCODING_ERROR`; Gesamtlauf bleibt fortsetzbar. Encoding-Bereinigung ist expliziter Teil von Phase 1. fileciteturn1file2

3. **Korruptes PDF / DOCX / EML**  
   Parsefehler auf Item-Ebene persistieren; Lauf nicht global abbrechen, außer Fehlerquote überschreitet definierte Schwelle.

4. **Provider nicht erreichbar**  
   AnalysisRun geht auf `FAILED` oder `PARTIALLY_COMPLETED`, nie stillschweigendes `COMPLETED`.

5. **Doppelter Start desselben Laufs durch UI-Doppelklick**  
   Idempotenz über Client-Request-ID oder serverseitige Entprellung.

6. **Backend-Crash während RUNNING**  
   Beim Neustart Recovery-Prozess: offene Läufe werden als `ABANDONED` markiert oder auf Resume-Fähigkeit geprüft.

7. **Retry auf terminalem, aber nicht retry-fähigem Lauf**  
   API gibt `409 Conflict` mit `RUN_NOT_RETRYABLE`.

8. **Analyseergebnis strukturell ungültig**  
   Raw Provider Output darf gespeichert werden, Normalisierung kann fehlschlagen. Trennung zwischen `output_payload` und `normalized_payload` verhindert Datenverlust.

9. **Sehr großer ImportRun**  
   Item-Listen nur paginiert; Zähler aggregiert im Run-Objekt.

10. **Source geändert während laufendem Import**  
    Lauf verwendet Snapshot der Source-Konfiguration zum Startzeitpunkt.

11. **Teilfreigaben**  
    Einzelne AnalysisResults dürfen `APPROVED` werden, auch wenn derselbe AnalysisRun insgesamt nur `PARTIALLY_COMPLETED` ist.

12. **Race Condition zwischen Cancel und Completion**  
    Terminalzustand wird transaktional entschieden; kein mehrfaches Finalisieren.

## Teststrategie

### 1. Unit-Tests
Fokus auf Zustandslogik, Repository-Verhalten, Fehlerabbildung.

Pflichtfälle:
- gültige/ungültige Statusübergänge ImportRun
- gültige/ungültige Statusübergänge AnalysisRun
- Review-Transitionen AnalysisResult
- Aggregation der Zählerstände
- Recovery-Regeln für `RUNNING -> ABANDONED`
- Idempotenz bei Retry/Start-Operationen

### 2. Repository-/Persistenztests
Mit echter SQLite-Testdatenbank, nicht nur Mocking.

Pflichtfälle:
- Persistenz und Reload von Source, ImportRun, AnalysisRun, AnalysisResult
- parallele Updates auf denselben Lauf
- atomare Finalisierung eines Laufs
- Pagination für ImportRunItems
- JSON-Felder für Output-Payload und Fehlerdetails

### 3. API-Integrationstests
Mit FastAPI TestClient.

Pflichtfälle:
- `POST /api/import-runs` erzeugt persistenten Run
- `GET /api/import-runs/{id}` zeigt denselben Zustand nach “Neustart-Simulation”
- `POST /api/analysis-runs` validiert Vorbedingung des ImportRuns
- `POST /api/analysis-results/{id}/review` ändert nur Review-Status
- ungültige Übergänge liefern 409/422 statt stiller Akzeptanz

### 4. Fehler- und Recovery-Tests
- defekte PDF/DOCX/EML-Datei im Batch
- unlesbare Quelle
- Provider-Timeout
- Prozessabbruch mitten im Run
- Resume/Retry nach `ABANDONED` und `FAILED`

### 5. End-to-End-Tests
Minimaler Happy Path:
1. Source anlegen
2. Source validieren
3. ImportRun starten
4. erfolgreiche und fehlgeschlagene Items erzeugen
5. AnalysisRun auf erfolgreichen Items starten
6. AnalysisResults abrufen
7. einzelnes Ergebnis freigeben

### Testabdeckung mit Priorität
- höchste Priorität: Zustandsautomat, Recovery, Persistenz
- mittlere Priorität: API-Formate, Pagination
- niedrigere Priorität: UI-Rendering

## Betriebsmetriken

Phase 1 braucht keine observability-plattform auf Enterprise-Niveau, aber klare Basiskennzahlen.

### Kernmetriken
- `import_run_started_total`
- `import_run_completed_total`
- `import_run_failed_total`
- `import_run_partially_completed_total`
- `analysis_run_started_total`
- `analysis_run_completed_total`
- `analysis_run_failed_total`
- `analysis_run_partially_completed_total`

### Qualitätsmetriken
- Erfolgsquote Import: `files_succeeded / files_processed`
- Fehlerquote Import: `files_failed / files_processed`
- Erfolgsquote Analyse: `documents_succeeded / documents_analyzed`
- Anteil unreviewter Ergebnisse
- Anteil freigegebener Ergebnisse
- Anzahl Encoding-Fehler pro 1000 Dateien

### Zeitmetriken
- Durchlaufzeit pro ImportRun
- Durchlaufzeit pro AnalysisRun
- mittlere Parsezeit pro Datei
- mittlere Analysezeit pro Dokument
- Zeit bis Review/Freigabe eines AnalysisResult

### Betriebsrisikoindikatoren
- Anzahl `ABANDONED` Runs
- Anzahl Recovery-Vorgänge nach Neustart
- Provider-Ausfallrate
- Anzahl Quellen mit `INVALID` oder `INACCESSIBLE`
- Anzahl Items mit wiederholtem Fehlercode

### Logging/Audit
Mindestens erforderlich:
- korrelierbare `run_id`
- `source_id`
- `item_id`
- `status_from`, `status_to`
- Fehlercode
- Provider/Model bei AnalysisRun

Ohne diese Daten ist die vom Masterplan geforderte Nachvollziehbarkeit von Review und Freigabe nicht belastbar erreichbar. fileciteturn1file4

## Definition of Done

Phase 1 ist fertig, wenn alle folgenden Bedingungen erfüllt sind:

1. ImportRun- und AnalysisRun-Status werden nicht mehr nur In-Memory gehalten, sondern lokal dauerhaft persistiert. Das ist explizite Roadmap-Anforderung. fileciteturn1file2  
2. Jeder Run besitzt definierte terminale und nichtterminale Zustände mit serverseitig erzwungenen Übergangsregeln.  
3. Nach Backend-Neustart sind alle zuvor bekannten Sources, Runs und AnalysisResults wieder abrufbar.  
4. `RUNNING`-Leichen werden nach Neustart deterministisch in einen Recovery-Zustand überführt.  
5. Analyseergebnisse werden lokal persistent gespeichert; kein Neo4j-Write für diese Phase. fileciteturn1file2turn1file4  
6. Rohdaten und fachliche Analyseergebnisse sind in getrennten Datenmodellen/Persistenzpfaden abgelegt. Das entspricht der im Masterplan geforderten Trennung von Rohimport und fachlicher Auswertung. fileciteturn1file2  
7. Defekte Einzeldateien führen zu nachvollziehbaren Item-Fehlern, ohne den Gesamtprozess unnötig abzubrechen.  
8. API-Endpunkte für Start, Status, Listen und Review sind implementiert und integrationstestbar.  
9. Review-Status für AnalysisResults ist lokal nachvollziehbar speicherbar.  
10. Frontend greift weiterhin ausschließlich auf FastAPI zu; keine direkte Kopplung an Neo4j oder Ollama. Das ist zugleich Bestandteil des nächsten belastbaren Projektstands. fileciteturn1file0turn1file4  
11. Basis-Metriken und strukturierte Logs erlauben Ursachenanalyse für Abbrüche, Teilfehler und Recovery.  
12. Encoding-Probleme in verbleibenden UI-/Backend-Texten sind systematisch bereinigt oder als klar abgegrenzte Restmängel dokumentiert. fileciteturn1file2

Kritischer Punkt: Die fachlich wichtigste Zusatzentscheidung gegenüber deinem Prompt ist die Einführung von `ImportRunItem` als persistente Untereinheit. Ohne dieses Objekt bleibt “Teilfehler verkraften” technisch unsauber, weil dann nur Run-Gesamtstatus existiert, aber keine präzise Fehler- und Wiederanlaufbasis pro Datei.

### 5. Benutzer

Runde 2: Prompts für Quellenvalidierung, ImportRun-Workflow und lokale Analysepersistenz. Prompts immer am schluss

### 6. Assistent

Runde 2 muss die Lücke zwischen bestehender Quellenverwaltung, vorhandenem lokalen Scanning und noch fehlender belastbarer Status-/Ergebnispersistenz schließen. Der Masterplan nennt dafür explizit drei relevante Baustellen: Source-Validierung erweitern, belastbare Statuspersistenz für Import-Jobs vorbereiten und Analyse-Ergebnisse dauerhaft speichern. Gleichzeitig bleibt die Architekturregel bestehen: Frontend nur gegen Backend, keine direkte Kopplung zu Neo4j oder Ollama, Rohimport und fachliche Auswertung getrennt. fileciteturn2file1 fileciteturn2file3turn2file4

Reihenfolge in Runde 2:
1. Quellenvalidierung
2. ImportRun-Workflow
3. lokale Analysepersistenz

Diese Reihenfolge ist zwingend, weil ein instabiler Source-Eingang jeden nachgelagerten Workflow kontaminiert. Danach folgt der ImportRun als operativer Taktgeber. Erst dann lohnt sich die Persistenz fachlicher Analyseergebnisse. Der Masterplan legt genau diese Pipeline nahe: Quelle registrieren, scannen, parsen, normalisieren, KI-Analyse, Review, später Freigabe nach Neo4j. fileciteturn2file2

## Einsatzlogik je Modell

- Claude: Architektur- und Workflowkritik, Validierungslogik, Failure Modes
- Codex: Backend-Implementierung, Modelle, Services, API, Zustandslogik
- GitHub Copilot: dateinahe Änderungen, Refactoring, Boilerplate, Tests
- ChatGPT: Spezifikation, API-Kontrakte, Akzeptanzkriterien, Testfälle

## Runde 2A: Quellenvalidierung

Ziel:
Source-Validierung von bloßer Registry-Verwaltung zu belastbarer Vorprüfung ausbauen. Der Backlog fordert ausdrücklich Existenzprüfungen und lesbaren Zugriff; im Frontend ist bessere Inline-Validierung vorgesehen. fileciteturn2file3turn2file4

### Erwartetes Ergebnis
- Validierungsstatus pro Source persistent gespeichert
- technische Prüfungen für Existenz, Lesbarkeit, Pfadtyp, unterstützte Dateitypen
- klare Trennung zwischen “Source registriert” und “Source lauffähig”
- UI zeigt präzise Validierungsfehler statt generischem Fail

## Runde 2B: ImportRun-Workflow

Ziel:
Den vorhandenen lokalen Scan-/Parse-Pfad in einen belastbaren Laufprozess mit Statusmodell, Item-Ebene, Resume/Retry und Recovery überführen. Der Masterplan nennt dafür dauerhafte Job-/Importstatus-Persistenz und Vorbereitung echter asynchroner Job-Ausführung. fileciteturn2file3turn2file4

### Erwartetes Ergebnis
- deterministische Statusübergänge
- persistierte Runs und Run-Items
- Teilfehler auf Datei-Ebene
- Restart-/Recovery-Verhalten nach Prozessabbruch
- API für Start, Status, Item-Liste, Retry, Cancel

## Runde 2C: Lokale Analysepersistenz

Ziel:
Analyseergebnisse lokal dauerhaft speichern, getrennt von Rohdaten und noch ohne Neo4j-Write. Genau diese Trennung ist im Masterplan als Persistenzstufe und als Phase-1-/Phase-2-Schnitt genannt. fileciteturn2file2turn2file3

### Erwartetes Ergebnis
- lokale AnalysisResult-Persistenz mit Review-Status
- Zuordnung zu ImportRun/RunItem/Dokument
- Speicherung von Raw Output plus normalisiertem Ergebnis
- spätere Freigabe nach Neo4j technisch vorbereiten, aber nicht implementieren

---

# Prompts

## 1) Claude Prompt — Quellenvalidierung

```text
Arbeite als Senior Software Architect und Systems Reviewer.

Kontext:
Ich baue eine Wissens- und Analyseplattform mit:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- Neo4j als externe Zielinfrastruktur
- KI-Provider nur über das Backend
- aktueller Source-Registry in JSON
- bestehender UI für Auflistung, Hinzufügen, Aktivieren und Bearbeiten von Quellen
- lokaler Dokumentenverarbeitung für PDF, DOCX, TXT, EML
- Architekturregel: kein Frontend-Zugriff auf Neo4j oder Ollama

Masterplan-relevante Punkte:
- Source-Validierung soll um Existenzprüfungen und lesbaren Zugriff erweitert werden
- Frontend soll bessere Inline-Validierung und UX für lokale Pfade erhalten
- Rohimport und fachliche Auswertung bleiben getrennt
- Persistenz & Stabilität haben aktuell Vorrang

Deine Aufgabe:
1. Entwirf eine belastbare Zielkonzeption für Quellenvalidierung.
2. Trenne klar zwischen:
   - Source registriert
   - Source technisch valide
   - Source operativ verwendbar
3. Definiere ein Validierungsmodell für lokale Quellenpfade mit:
   - Existenzprüfung
   - Pfadtypprüfung
   - Lesbarkeit
   - unterstützte Dateitypen
   - Erreichbarkeit
   - Fehlermeldungsmodell
4. Leite zulässige Source-Status und Statusübergänge ab.
5. Formuliere den minimalen Backend- und Frontend-Umfang für diese Ausbaustufe.
6. Benenne Failure Modes, Race Conditions und UX-Risiken.
7. Gib konkrete Empfehlungen für API-Verhalten, Validierungszeitpunkte und Persistenz der Prüfergebnisse.
8. Definiere eine Definition of Done.

Antwortformat:
- Annahmen
- Zielmodell Quellenvalidierung
- Statusmodell
- Backend-Verantwortlichkeiten
- Frontend-Verantwortlichkeiten
- Failure Modes / Risiken
- priorisierte Umsetzungsschritte
- Definition of Done

Wichtig:
- Keine generische Validierungsdiskussion
- Fokus auf lokale Pfade und stabile Betriebsfähigkeit
- Trade-offs explizit benennen
```

## 2) Codex Prompt — Quellenvalidierung implementieren

```text
Arbeite als erfahrener Python/FastAPI-Entwickler in einer bestehenden Codebasis.

Ziel:
Implementiere eine belastbare Quellenvalidierung für lokale Sources.

Kontext:
- Es gibt bereits eine Source-Registry, aktuell JSON-basiert
- Es gibt UI für Quellenverwaltung
- Lokales Dokumentenscanning existiert
- Source-Validierung soll um Existenzprüfung und lesbaren Zugriff erweitert werden
- Frontend darf nie direkt mit Neo4j oder Ollama sprechen
- Fokus ist Phase 1: Persistenz & Stabilität

Implementiere:
1. Source-Validierungslogik im Backend
2. persistente Felder für Validierungsstatus und Validierungsdetails
3. API-Endpunkte für:
   - Quelle anlegen
   - Quelle aktualisieren
   - Quelle validieren
   - Quellenliste / Quelle im Detail
4. standardisierte Fehlercodes und Fehlermeldungen
5. Tests für valide und invalide lokale Pfade

Validierungsdimensionen:
- Pfad vorhanden oder nicht
- lesbar oder nicht
- Datei vs Verzeichnis
- unterstützte Dateitypen vorhanden oder nicht
- Quelle aktiv/inaktiv
- Validierungsergebnis mit Zeitstempel

Erwartete Datenfelder:
- source_id
- display_name
- source_system
- location_uri
- is_active
- validation_status
- validation_message
- last_validated_at
- updated_at

Arbeitsmodus:
1. Analysiere zunächst die mutmaßlich betroffenen Dateien.
2. Schlage dann konkrete Änderungen vor.
3. Implementiere den Code schrittweise.
4. Füge Tests hinzu.
5. Markiere offene Integrationspunkte mit dem Frontend.

Wichtig:
- Keine direkte Dateisystemlogik im Frontend
- Keine neue komplexe Infrastruktur
- Bestehende Source-Registry nicht unkontrolliert brechen
- Defensive Fehlerbehandlung
```

## 3) GitHub Copilot Prompt — Quellenvalidierung im Editor

```text
Kontext der Codebasis:

Ich erweitere die bestehende Quellenverwaltung einer Wissens- und Analyseplattform.
Technischer Rahmen:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- bestehende Source-Registry
- lokales Dokumentenscanning vorhanden
- Validierung lokaler Pfade soll belastbar werden

Bitte hilf mir beim Ausbau der Quellenvalidierung.

Ziele:
- Source-Validierung serverseitig durchführen
- Validierungsstatus persistent speichern
- klare Fehlermeldungen für Existenz, Lesbarkeit, Pfadtyp und unterstützte Dateien
- Frontend nur gegen FastAPI, keine lokale Fachlogik für Dateisystemprüfung
- möglichst kleine, reviewbare Änderungen

Arbeite dateibasiert:
1. zeige zuerst die wahrscheinlich betroffenen Dateien
2. schlage Änderungen pro Datei vor
3. generiere danach implementierbaren Code
4. ergänze Tests für Validierungsfälle

Zu berücksichtigen:
- Source registriert ist nicht gleich Source lauffähig
- Validation API und UI-Feedback müssen konsistent sein
- keine Kopplung an Neo4j oder Ollama
```

## 4) ChatGPT Prompt — Spezifikation Quellenvalidierung

```text
Arbeite als Product Owner, Systems Analyst und Software Reviewer.

Ich baue eine Wissens- und Analyseplattform mit bestehender Quellenverwaltung.
Aktueller Bedarf:
Quellenvalidierung für lokale Pfade fachlich und technisch sauber spezifizieren.

Rahmen:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- Source-Registry existiert
- lokales Dokumentenscanning existiert
- Source-Validierung soll Existenzprüfung und lesbaren Zugriff abdecken
- Frontend darf keine Dateisystem-Fachlogik übernehmen
- Fokus liegt auf Stabilität, Nachvollziehbarkeit und klaren Fehlerbildern

Erstelle eine umsetzbare Spezifikation für Quellenvalidierung.

Benötigt:
1. fachliche Ziele
2. Nicht-Ziele
3. Domänenmodell für Source und SourceValidation
4. Statusmodell mit zulässigen Übergängen
5. API-Kontrakte
6. Akzeptanzkriterien
7. Testfälle
8. Betriebsrisiken
9. Messgrößen
10. Definition of Done

Antwortformat:
- Zielbild
- Scope / Out of Scope
- Domänenmodell
- Zustandsautomat
- API-Spezifikation
- Akzeptanzkriterien
- Negativfälle / Edge Cases
- Teststrategie
- Betriebsmetriken
- Definition of Done

Zusatz:
Fokussiere auf lokale Quellenpfade, Fehlertoleranz und klare Entscheidbarkeit.
```

---

## 5) Claude Prompt — ImportRun-Workflow

```text
Arbeite als Senior Software Architect und Workflow Reviewer.

Kontext:
Ich habe bereits:
- lokale Quellenverwaltung
- rekursives Scannen lokaler Ordner
- Extraktion von Text und Metadaten aus PDF, DOCX, TXT und EML
- ein FastAPI-Backend
- ein React/Vite-Frontend
- ein Analyse-Grundgerüst

Aktuelles Problem:
Der ImportRun-Workflow ist noch nicht belastbar genug für Persistenz, Recovery und Teilfehler.
Job- und Import-Status sollen von In-Memory auf dauerhafte Persistenz umgestellt werden.
Echte asynchrone Job-Ausführung ist später relevant, muss aber jetzt vorbereitbar werden.

Deine Aufgabe:
1. Entwirf einen belastbaren ImportRun-Workflow für lokale Dokumentquellen.
2. Definiere die benötigten Domänenobjekte:
   - ImportRun
   - ImportRunItem
   - optionale Event-/Audit-Struktur
3. Definiere das Statusmodell mit zulässigen Übergängen.
4. Beschreibe das Verhalten bei:
   - defekten Dateien
   - Encoding-Problemen
   - teilweisem Erfolg
   - Cancel
   - Retry
   - Prozessabbruch / Neustart
5. Leite API-Endpunkte und Minimalverhalten für das Frontend ab.
6. Benenne technische Risiken, Race Conditions und Recovery-Fallen.
7. Formuliere einen priorisierten Implementierungsplan.
8. Gib eine Definition of Done aus.

Antwortformat:
- Annahmen
- Zielworkflow
- Domänenobjekte
- Zustandsautomat
- Recovery-/Retry-Modell
- API-Empfehlung
- Risiken / Failure Modes
- priorisierte Umsetzungsschritte
- Definition of Done

Wichtig:
- Fokus auf lokale Dokumentquellen, nicht PST-Neuentwicklung
- Keine Platzhalterarchitektur
- Trade-offs explizit machen
```

## 6) Codex Prompt — ImportRun-Workflow implementieren

```text
Arbeite als erfahrener Python/FastAPI-Entwickler in einer bestehenden Codebasis.

Ziel:
Implementiere einen belastbaren ImportRun-Workflow mit lokaler Persistenz.

Kontext:
- rekursives Scannen lokaler Ordner existiert
- Parsing für PDF, DOCX, TXT, EML existiert
- In-Memory-Status soll ersetzt werden
- lokale Persistenz für Jobs/Status ist jetzt Priorität
- echte asynchrone Jobs werden noch nicht voll umgesetzt, aber das Statusmodell soll dafür vorbereitet sein

Implementiere:
1. Persistenzmodelle für ImportRun und ImportRunItem
2. Repository- und Service-Layer
3. Status-Enums und serverseitige Übergangsregeln
4. API-Endpunkte für:
   - ImportRun starten
   - ImportRun Status abrufen
   - ImportRuns listen
   - ImportRunItems abrufen
   - ImportRun retry
   - ImportRun cancel
5. Zählerstände und Fehlerabbildung auf Run- und Item-Ebene
6. Recovery-Logik für nach Neustart offen gebliebene Runs
7. Tests für Kernlogik und Statusübergänge

Anforderungen:
- SQLite mit SQLAlchemy oder SQLModel bevorzugen, falls kein belastbarerer Standard vorhanden ist
- Teilfehler dürfen nicht zum Totalabbruch führen, wenn sie isolierbar sind
- pro Item mindestens: Pfad, Status, Content-Type, Hash optional, Fehlercode, Fehlermeldung
- pro Run mindestens: ID, Source-ID, Status, Zeitstempel, Counters, Last Error, Restart-Bezug
- keine direkte Neo4j-Logik
- keine Analysepersistenz in diesem Task vermischen

Arbeitsmodus:
1. Analysiere die mutmaßlich betroffenen Dateien.
2. Formuliere einen konkreten Änderungsplan.
3. Implementiere den Code schrittweise.
4. Begründe wichtige Designentscheidungen.
5. Markiere offene Anschlussstellen zur Analysephase.

Wichtig:
- Keine Schein-Asynchronität ohne Statuskonsistenz
- Idempotenz und Recovery mitdenken
- Vorhandenes Scanning nicht blind neu schreiben
```

## 7) GitHub Copilot Prompt — ImportRun-Workflow im Editor

```text
Kontext der Codebasis:

Ich baue den ImportRun-Workflow einer Wissens- und Analyseplattform aus.
Bestehend:
- Quellenverwaltung
- rekursives Scannen lokaler Ordner
- Parsing von PDF, DOCX, TXT, EML
- FastAPI Backend
- React/Vite Frontend

Bitte hilf mir, den ImportRun-Workflow belastbar zu machen.

Ziele:
- In-Memory-Status durch persistente Runs ersetzen
- ImportRun und ImportRunItem sauber modellieren
- Statusübergänge robust abbilden
- Teilfehler auf Item-Ebene speichern
- Retry, Cancel und Recovery vorbereiten
- kleine, reviewbare Änderungen bevorzugen

Arbeite dateibasiert:
1. nenne zuerst die betroffenen Dateien
2. schlage konkrete Änderungen pro Datei vor
3. generiere dann implementierbaren Code
4. ergänze Tests für Statusübergänge, Counters und Recovery

Beachte:
- keine Vermischung mit Neo4j-Persistenz
- keine Analyseergebnislogik in diesen Task ziehen
- bestehende Scan-/Parse-Logik weiterverwenden, wo sinnvoll
```

## 8) ChatGPT Prompt — Spezifikation ImportRun-Workflow

```text
Arbeite als Product Owner, Systems Analyst und Software Reviewer.

Ich baue eine Wissens- und Analyseplattform.
Der nächste Schwerpunkt ist der operative ImportRun-Workflow für lokale Dokumentquellen.

Rahmen:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- lokale Quellenverwaltung vorhanden
- rekursives Dokumentenscanning vorhanden
- Parsing für PDF, DOCX, TXT, EML vorhanden
- In-Memory-Status ist der Engpass
- Lösung muss Neustarts, Teilfehler und defekte Dateien verkraften

Erstelle eine umsetzbare Spezifikation für den ImportRun-Workflow.

Benötigt:
1. fachliche Ziele
2. Nicht-Ziele
3. Domänenmodell für ImportRun und ImportRunItem
4. Statusmodell mit zulässigen Zustandsübergängen
5. API-Kontrakte
6. Akzeptanzkriterien
7. Testfälle
8. Betriebsrisiken
9. Messgrößen / Telemetrie
10. Definition of Done

Antwortformat:
- Zielbild
- Scope / Out of Scope
- Domänenmodell
- Zustandsautomat
- API-Spezifikation
- Akzeptanzkriterien
- Negativfälle / Edge Cases
- Teststrategie
- Betriebsmetriken
- Definition of Done

Zusatz:
Fokussiere auf Wiederanlauf, Teilfehlerisolierung, Statuskonsistenz und Reviewbarkeit.
```

---

## 9) Claude Prompt — Lokale Analysepersistenz

```text
Arbeite als Senior Software Architect und Systems Reviewer.

Kontext:
In der Plattform existieren bereits:
- Analyse-Grundgerüst für ImportRuns (`analysis_service`)
- Provider-Abstraktion für Ollama und DnaBot
- Analyse kann gestartet und abgefragt werden
- Analyseergebnisse werden aktuell noch nicht dauerhaft gespeichert
- Neo4j bleibt externe Zielinfrastruktur
- Freigegebene Ergebnisse sollen erst später getrennt nach Neo4j geschrieben werden
- Rohimport und fachliche Auswertung müssen getrennte Persistenzstufen bleiben

Deine Aufgabe:
1. Entwirf ein belastbares Zielmodell für lokale Analysepersistenz.
2. Definiere die benötigten Domänenobjekte:
   - AnalysisRun
   - AnalysisResult
   - optional AnalysisResultReview oder Event-Historie
3. Leite das Statusmodell für AnalysisRun und Review-Status für AnalysisResult ab.
4. Definiere, was lokal gespeichert werden muss und was bewusst noch nicht nach Neo4j gehört.
5. Beschreibe die Zuordnung zwischen ImportRun, ImportRunItem, analysiertem Dokument und Analyseergebnis.
6. Benenne Failure Modes:
   - Provider-Ausfall
   - ungültiger Output
   - Normalisierungsfehler
   - doppelte Ergebnisse
   - Re-Run / Supersession
7. Formuliere API- und Persistenzempfehlungen.
8. Gib einen priorisierten Implementierungsplan und eine Definition of Done aus.

Antwortformat:
- Annahmen
- Zielmodell lokale Analysepersistenz
- Domänenobjekte
- Zustandsautomat
- Persistenzregeln
- Risiken / Failure Modes
- API-Empfehlung
- priorisierte Umsetzungsschritte
- Definition of Done

Wichtig:
- Keine Vermischung mit Neo4j-Write
- Fokus auf lokale Nachvollziehbarkeit, Reviewfähigkeit und spätere Exportfähigkeit
- Trade-offs explizit benennen
```

## 10) Codex Prompt — Lokale Analysepersistenz implementieren

```text
Arbeite als erfahrener Python/FastAPI-Entwickler in einer bestehenden Codebasis.

Ziel:
Implementiere lokale Analysepersistenz für ImportRun-basierte Analysen.

Kontext:
- `analysis_service` existiert bereits als Grundgerüst
- Provider-Abstraktion für Ollama und DnaBot existiert
- Analyse kann gestartet und abgefragt werden
- Analyseergebnisse werden aktuell noch nicht dauerhaft gespeichert
- Freigegebene Ergebnisse sollen später getrennt nach Neo4j geschrieben werden
- Rohdaten und fachliche Ergebnisse müssen getrennt bleiben

Implementiere:
1. Persistenzmodelle für AnalysisRun und AnalysisResult
2. Statusmodell für AnalysisRun
3. Review-Status für AnalysisResult
4. Repository- und Service-Layer
5. API-Endpunkte für:
   - AnalysisRun starten
   - AnalysisRun Status abrufen
   - AnalysisRuns listen
   - Results eines AnalysisRun abrufen
   - einzelnes AnalysisResult abrufen
   - Review-Status setzen
6. Speicherung von:
   - provider
   - provider_model
   - input_hash
   - raw output
   - normalized output optional
   - confidence optional
   - review_status
7. Re-Run-/Supersession-Logik für mehrfach erzeugte Ergebnisse
8. Tests für Persistenz, Statusübergänge, Review und Fehlerfälle

Anforderungen:
- lokale Persistenz zuerst, kein Neo4j-Write in diesem Task
- Analyseergebnisse müssen ImportRun/Item/Dokument eindeutig referenzieren
- Raw Output darf nicht verloren gehen, auch wenn Normalisierung fehlschlägt
- Review-Status muss unabhängig vom Rohdatenbestand änderbar sein
- defensive Fehlerbehandlung für Provider- und Parsing-/Normalisierungsfehler

Arbeitsmodus:
1. Analysiere die mutmaßlich betroffenen Dateien.
2. Schlage konkrete Änderungen vor.
3. Implementiere schrittweise.
4. Begründe wichtige Modellierungsentscheidungen.
5. Markiere offene Anschlussstellen für späteren Neo4j-Export.

Wichtig:
- Keine Vermischung mit Graphmodellierung
- Keine direkte Frontend-Providerkopplung
- Kein Überschreiben von Rohdaten
```

## 11) GitHub Copilot Prompt — Lokale Analysepersistenz im Editor

```text
Kontext der Codebasis:

Ich erweitere eine bestehende Analysefunktion in einer Wissens- und Analyseplattform.
Vorhanden:
- `analysis_service`
- Provider-Abstraktion für Ollama und DnaBot
- Starten und Abfragen von Analysen
- FastAPI Backend
- React/Vite Frontend

Bitte hilf mir beim Ausbau der lokalen Analysepersistenz.

Ziele:
- AnalysisRun und AnalysisResult persistent speichern
- Raw Output und normalisierte Ergebnisse getrennt ablegen
- Review-Status lokal verwalten
- eindeutige Zuordnung zu ImportRun / ImportRunItem / Dokument
- spätere Neo4j-Freigabe vorbereiten, aber jetzt nicht implementieren

Arbeite dateibasiert:
1. nenne zuerst die betroffenen Dateien
2. schlage pro Datei konkrete Änderungen vor
3. generiere dann implementierbaren Code
4. ergänze Tests für Persistenz, Review, Re-Run und Fehlerfälle

Beachte:
- Rohdaten und fachliche Ergebnisse müssen getrennt bleiben
- kein Neo4j-Write in diesem Task
- bestehende Analysepfade möglichst weiterverwenden
```

## 12) ChatGPT Prompt — Spezifikation lokale Analysepersistenz

```text
Arbeite als Product Owner, Systems Analyst und Software Reviewer.

Ich baue eine Wissens- und Analyseplattform.
Die Analyse kann bereits gestartet und abgefragt werden, aber Ergebnisse werden noch nicht dauerhaft gespeichert.

Rahmen:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- Analyse-Grundgerüst vorhanden
- Provider-Abstraktion für Ollama und DnaBot vorhanden
- Neo4j ist externe Zielinfrastruktur
- Analyseergebnisse sollen zunächst lokal persistent gespeichert werden
- Freigegebene Ergebnisse werden später getrennt nach Neo4j geschrieben
- Rohdaten und fachliche Ergebnisse müssen getrennt bleiben

Erstelle eine umsetzbare Spezifikation für lokale Analysepersistenz.

Benötigt:
1. fachliche Ziele
2. Nicht-Ziele
3. Domänenmodell für AnalysisRun und AnalysisResult
4. Statusmodell mit zulässigen Zustandsübergängen
5. API-Kontrakte
6. Akzeptanzkriterien
7. Testfälle
8. Betriebsrisiken
9. Messgrößen / Telemetrie
10. Definition of Done

Antwortformat:
- Zielbild
- Scope / Out of Scope
- Domänenmodell
- Zustandsautomat
- API-Spezifikation
- Akzeptanzkriterien
- Negativfälle / Edge Cases
- Teststrategie
- Betriebsmetriken
- Definition of Done

Zusatz:
Fokussiere auf lokale Nachvollziehbarkeit, Reviewfähigkeit, Trennung von Rohdaten und fachlichen Ergebnissen sowie spätere Exportfähigkeit.
```

### 7. Benutzer

erstelle mir alle Promts für claude

### 8. Assistent

Hier sind alle Claude-Prompts, konsolidiert und in sinnvoller Arbeitsreihenfolge.

# 1) Claude Prompt — Architektur- und Persistenzfundament

```text
Du arbeitest als Senior Software Architect und Technical Product Owner.

Kontext:
Ich baue eine lokale Wissens- und Analyseplattform mit folgendem Zielbild:
- Frontend: React + Vite + TypeScript
- Backend: FastAPI
- Datenbank: externe Neo4j Aura oder Self-Managed Neo4j
- KI-Provider: Ollama lokal, optional DnaBot
- Parsing: PST später neu, lokal bereits PDF/DOCX/TXT/EML
- Architekturregel: kein Frontend-zu-Neo4j-Zugriff, kein Frontend-zu-Ollama-Zugriff, alle Integrationen nur über das Backend
- Rohdaten nie überschreiben
- Freigegebene Analyseergebnisse getrennt persistieren

Ist-Zustand:
- FastAPI-Backend vorhanden
- React-/Vite-Frontend vorhanden
- Quellenverwaltung vorhanden
- Dokumentenscanning lokal vorhanden
- Analyse-Grundgerüst vorhanden
- Persistenz für Jobs/Importstatus ist noch nicht belastbar
- Analyseergebnisse werden noch nicht in Neo4j persistiert
- PST-Pipeline ist zurückgesetzt und derzeit kein Umsetzungsschwerpunkt

Domänenobjekte:
- SourceSystem / Source
- ImportRun
- Folder
- Email
- Document
- Attachment
- Topic
- Entity
- AnalysisResult
- MergedCase

Roadmap-Prio jetzt:
Phase 1: Persistenz & Stabilität
- Job- und Import-Status von In-Memory auf dauerhafte Persistenz umstellen
- Analyse-Ergebnisse dauerhaft speichern
- robusteres Error Handling
- Encoding-Bereinigung

Deine Aufgabe:
1. Leite aus dem Kontext eine saubere Zielstruktur für Backend, Frontend und Persistenzschicht ab.
2. Definiere die minimal belastbare Architektur für Phase 1.
3. Schlage konkrete Module, Verantwortlichkeiten und Schnittstellen vor.
4. Benenne technische Risiken, versteckte Abhängigkeiten und typische Fehlentscheidungen.
5. Formuliere einen priorisierten Implementierungsplan in 8-12 Schritten.
6. Liefere Entscheidungstabellen für:
   - SQLite vs andere lokale Persistenzoptionen für Jobs/Status
   - synchrone vs asynchrone Job-Ausführung
   - Zwischenspeicherung von Analyseergebnissen lokal vs direkt nach Neo4j
7. Gib am Ende eine “Definition of Done” für Phase 1 aus.

Antwortformat:
- Annahmen
- Zielarchitektur Phase 1
- Modulzuschnitt
- API-/Datenmodell-Empfehlung
- Risiken / Failure Modes
- Priorisierte Implementierungsschritte
- Definition of Done

Wichtig:
- Keine generischen Best Practices ohne Bezug zum Kontext
- Beurteile Trade-offs explizit
- Denke in Änderbarkeit, Wiederanlauf, Fehlerisolierung und Reviewbarkeit
```

# 2) Claude Prompt — Quellenvalidierung

```text
Arbeite als Senior Software Architect und Systems Reviewer.

Kontext:
Ich baue eine Wissens- und Analyseplattform mit:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- Neo4j als externe Zielinfrastruktur
- KI-Provider nur über das Backend
- aktueller Source-Registry in JSON
- bestehender UI für Auflistung, Hinzufügen, Aktivieren und Bearbeiten von Quellen
- lokaler Dokumentenverarbeitung für PDF, DOCX, TXT, EML
- Architekturregel: kein Frontend-Zugriff auf Neo4j oder Ollama

Masterplan-relevante Punkte:
- Source-Validierung soll um Existenzprüfungen und lesbaren Zugriff erweitert werden
- Frontend soll bessere Inline-Validierung und UX für lokale Pfade erhalten
- Rohimport und fachliche Auswertung bleiben getrennt
- Persistenz & Stabilität haben aktuell Vorrang

Deine Aufgabe:
1. Entwirf eine belastbare Zielkonzeption für Quellenvalidierung.
2. Trenne klar zwischen:
   - Source registriert
   - Source technisch valide
   - Source operativ verwendbar
3. Definiere ein Validierungsmodell für lokale Quellenpfade mit:
   - Existenzprüfung
   - Pfadtypprüfung
   - Lesbarkeit
   - unterstützte Dateitypen
   - Erreichbarkeit
   - Fehlermeldungsmodell
4. Leite zulässige Source-Status und Statusübergänge ab.
5. Formuliere den minimalen Backend- und Frontend-Umfang für diese Ausbaustufe.
6. Benenne Failure Modes, Race Conditions und UX-Risiken.
7. Gib konkrete Empfehlungen für API-Verhalten, Validierungszeitpunkte und Persistenz der Prüfergebnisse.
8. Definiere eine Definition of Done.

Antwortformat:
- Annahmen
- Zielmodell Quellenvalidierung
- Statusmodell
- Backend-Verantwortlichkeiten
- Frontend-Verantwortlichkeiten
- Failure Modes / Risiken
- priorisierte Umsetzungsschritte
- Definition of Done

Wichtig:
- Keine generische Validierungsdiskussion
- Fokus auf lokale Pfade und stabile Betriebsfähigkeit
- Trade-offs explizit benennen
```

# 3) Claude Prompt — ImportRun-Workflow

```text
Arbeite als Senior Software Architect und Workflow Reviewer.

Kontext:
Ich habe bereits:
- lokale Quellenverwaltung
- rekursives Scannen lokaler Ordner
- Extraktion von Text und Metadaten aus PDF, DOCX, TXT und EML
- ein FastAPI-Backend
- ein React/Vite-Frontend
- ein Analyse-Grundgerüst

Aktuelles Problem:
Der ImportRun-Workflow ist noch nicht belastbar genug für Persistenz, Recovery und Teilfehler.
Job- und Import-Status sollen von In-Memory auf dauerhafte Persistenz umgestellt werden.
Echte asynchrone Job-Ausführung ist später relevant, muss aber jetzt vorbereitbar werden.

Deine Aufgabe:
1. Entwirf einen belastbaren ImportRun-Workflow für lokale Dokumentquellen.
2. Definiere die benötigten Domänenobjekte:
   - ImportRun
   - ImportRunItem
   - optionale Event-/Audit-Struktur
3. Definiere das Statusmodell mit zulässigen Übergängen.
4. Beschreibe das Verhalten bei:
   - defekten Dateien
   - Encoding-Problemen
   - teilweisem Erfolg
   - Cancel
   - Retry
   - Prozessabbruch / Neustart
5. Leite API-Endpunkte und Minimalverhalten für das Frontend ab.
6. Benenne technische Risiken, Race Conditions und Recovery-Fallen.
7. Formuliere einen priorisierten Implementierungsplan.
8. Gib eine Definition of Done aus.

Antwortformat:
- Annahmen
- Zielworkflow
- Domänenobjekte
- Zustandsautomat
- Recovery-/Retry-Modell
- API-Empfehlung
- Risiken / Failure Modes
- priorisierte Umsetzungsschritte
- Definition of Done

Wichtig:
- Fokus auf lokale Dokumentquellen, nicht PST-Neuentwicklung
- Keine Platzhalterarchitektur
- Trade-offs explizit machen
```

# 4) Claude Prompt — Lokale Analysepersistenz

```text
Arbeite als Senior Software Architect und Systems Reviewer.

Kontext:
In der Plattform existieren bereits:
- Analyse-Grundgerüst für ImportRuns (`analysis_service`)
- Provider-Abstraktion für Ollama und DnaBot
- Analyse kann gestartet und abgefragt werden
- Analyseergebnisse werden aktuell noch nicht dauerhaft gespeichert
- Neo4j bleibt externe Zielinfrastruktur
- Freigegebene Ergebnisse sollen erst später getrennt nach Neo4j geschrieben werden
- Rohimport und fachliche Auswertung müssen getrennte Persistenzstufen bleiben

Deine Aufgabe:
1. Entwirf ein belastbares Zielmodell für lokale Analysepersistenz.
2. Definiere die benötigten Domänenobjekte:
   - AnalysisRun
   - AnalysisResult
   - optional AnalysisResultReview oder Event-Historie
3. Leite das Statusmodell für AnalysisRun und Review-Status für AnalysisResult ab.
4. Definiere, was lokal gespeichert werden muss und was bewusst noch nicht nach Neo4j gehört.
5. Beschreibe die Zuordnung zwischen ImportRun, ImportRunItem, analysiertem Dokument und Analyseergebnis.
6. Benenne Failure Modes:
   - Provider-Ausfall
   - ungültiger Output
   - Normalisierungsfehler
   - doppelte Ergebnisse
   - Re-Run / Supersession
7. Formuliere API- und Persistenzempfehlungen.
8. Gib einen priorisierten Implementierungsplan und eine Definition of Done aus.

Antwortformat:
- Annahmen
- Zielmodell lokale Analysepersistenz
- Domänenobjekte
- Zustandsautomat
- Persistenzregeln
- Risiken / Failure Modes
- API-Empfehlung
- priorisierte Umsetzungsschritte
- Definition of Done

Wichtig:
- Keine Vermischung mit Neo4j-Write
- Fokus auf lokale Nachvollziehbarkeit, Reviewfähigkeit und spätere Exportfähigkeit
- Trade-offs explizit benennen
```

# 5) Claude Prompt — Gesamtworkflow Phase 1 als integrierte Zielarchitektur

```text
Arbeite als Senior Software Architect, Process Designer und Systems Reviewer.

Kontext:
Ich baue eine Wissens- und Analyseplattform mit:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- Neo4j als externe Zielinfrastruktur
- Ollama lokal und optional DnaBot nur über das Backend
- bestehender Quellenverwaltung
- bestehendem rekursiven lokalen Scanning
- bestehendem Parsing für PDF, DOCX, TXT, EML
- bestehendem Analyse-Grundgerüst
- Engpass in Persistenz, Recovery, Reviewbarkeit und Betriebsstabilität

Architekturregeln:
- kein Frontend-Zugriff auf Neo4j
- kein Frontend-Zugriff auf Ollama
- alle Integrationen nur über das Backend
- Rohdaten nie überschreiben
- fachliche Analyseergebnisse getrennt von Rohdaten persistieren
- freigegebene Ergebnisse erst später nach Neo4j schreiben

Deine Aufgabe:
1. Integriere die drei Teilbereiche
   - Quellenvalidierung
   - ImportRun-Workflow
   - lokale Analysepersistenz
   zu einer konsistenten Zielarchitektur für Phase 1.
2. Definiere die vollständige Prozesskette von:
   - Source anlegen
   - Source validieren
   - ImportRun starten
   - ImportRunItems verarbeiten
   - AnalysisRun starten
   - AnalysisResults lokal speichern
   - Ergebnisse reviewen
3. Zeige die Abhängigkeiten und Vorbedingungen zwischen den Stufen.
4. Benenne die entscheidenden Domänenobjekte, Zustände und Schnittstellen.
5. Identifiziere Bruchstellen, Race Conditions, Recovery-Fallen und Inkonsistenzen zwischen den Teilbereichen.
6. Erstelle einen priorisierten Implementierungsplan über alle Teilbereiche hinweg.
7. Definiere die minimal belastbare Version, die produktiv testbar ist.
8. Formuliere eine gemeinsame Definition of Done für Phase 1.

Antwortformat:
- Annahmen
- integriertes Zielbild
- Prozesskette Ende-zu-Ende
- Domänenmodell und Zustandsabhängigkeiten
- API-/Service-Schnittstellen
- Risiken / Failure Modes / Hidden Dependencies
- priorisierte Implementierungsreihenfolge
- minimale produktiv testbare Version
- Definition of Done

Wichtig:
- Keine isolierte Betrachtung einzelner Module
- Fokus auf Gesamtstabilität, Wiederanlauf, Fehlerisolierung und spätere Erweiterbarkeit
- Trade-offs explizit benennen
```

# 6) Claude Prompt — Architekturkritik des bestehenden Systems gegen den Masterplan

```text
Arbeite als Principal Architect und kritischer Systems Reviewer.

Kontext:
Ich habe bereits eine bestehende Codebasis für eine Wissens- und Analyseplattform mit:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- Quellenverwaltung
- lokalem Dokumentenscanning
- Analyse-Grundgerüst
- geplanter externer Neo4j-Zielinfrastruktur

Ziel:
Ich will das bestehende System gegen das Zielbild aus dem Masterplan kritisch prüfen lassen.

Prüfmaßstab:
- Frontend nur gegen Backend
- keine direkte Frontend-Kopplung an Neo4j oder Ollama
- belastbare Persistenz statt In-Memory-Status
- Rohdaten und fachliche Analyse getrennt
- lokale Analysepersistenz vor Neo4j-Export
- Review-/Freigabefähigkeit
- Neustartfestigkeit
- Recovery- und Retry-Fähigkeit
- saubere Statusmodelle
- Teilfehlerisolierung
- keine PST-Ablenkung in Phase 1

Deine Aufgabe:
1. Leite aus dem Zielbild die wichtigsten Architekturprinzipien ab.
2. Formuliere eine Review-Checkliste, mit der ich meine bestehende Codebasis prüfen kann.
3. Nenne typische Architekturverstöße und Antipatterns in genau diesem Kontext.
4. Beschreibe die wahrscheinlichsten versteckten Kopplungen und technischen Schulden.
5. Leite daraus einen konkreten Refactoring-Fahrplan für Phase 1 ab.
6. Priorisiere nach Risikowirkung und Abhängigkeitslogik, nicht nach kosmetischer Ordnung.
7. Formuliere harte Abnahmekriterien für die Architektur.

Antwortformat:
- Zielprinzipien
- Review-Checkliste
- typische Verstöße / Antipatterns
- technische Schulden / Hidden Dependencies
- priorisierter Refactoring-Fahrplan
- harte Abnahmekriterien

Wichtig:
- Keine allgemeine Software-Architekturtheorie
- Beurteile nur, was für diese Plattform und diesen Masterplan operativ relevant ist
- Fokus auf Änderbarkeit, Stabilität und spätere Neo4j-Exportfähigkeit
```

# 7) Claude Prompt — Risikoanalyse und Failure-Mode-Assessment für Phase 1

```text
Arbeite als Senior Systems Reviewer mit Fokus auf Failure Analysis.

Kontext:
Ich baue eine Wissens- und Analyseplattform mit:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- lokaler Quellenverwaltung
- lokalem Dokumentenscanning
- Analyse über Backend-gekapselte KI-Provider
- lokaler Persistenz für Runs und Analyseergebnisse als aktuelle Phase
- späterem Export freigegebener Ergebnisse nach Neo4j

Ich will die Risiken von Phase 1 systematisch verstehen.

Deine Aufgabe:
1. Erstelle eine Failure-Mode-Analyse für:
   - Quellenvalidierung
   - ImportRun-Workflow
   - lokale Analysepersistenz
2. Ordne Fehler nach:
   - Eintrittswahrscheinlichkeit
   - Schadenshöhe
   - Entdeckbarkeit
   - Recovery-Aufwand
3. Benenne pro Failure Mode:
   - Auslöser
   - sichtbares Symptom
   - Root Cause
   - betroffene Domänenobjekte
   - geeignete Gegenmaßnahmen
   - Monitoring-/Telemetry-Signal
4. Identifiziere systemische Risiken:
   - Race Conditions
   - Statusinkonsistenzen
   - Doppelverarbeitung
   - Datenverlust
   - Review-Inkonsistenz
   - Recovery-Fehlverhalten
5. Definiere die Top 10 Risiken, die vor produktivem Testbetrieb mitigiert sein müssen.
6. Formuliere eine operative Freigabeempfehlung für Phase 1.

Antwortformat:
- Annahmen
- Failure Modes nach Teilbereich
- Risikomatrix
- Top 10 produktionskritische Risiken
- empfohlene Gegenmaßnahmen
- minimale Monitoring-/Telemetry-Anforderungen
- Freigabeempfehlung mit Bedingungen

Wichtig:
- Keine allgemeine Risikobeschreibung
- Fokus auf operative Ausfälle, Datenkonsistenz und Wiederanlauf
- Priorisierung strikt nach Systemwirkung
```

# 8) Claude Prompt — Umsetzungsplan in Epic/Feature/Task-Struktur

```text
Arbeite als Technical Product Owner und Delivery Architect.

Kontext:
Ich baue eine Wissens- und Analyseplattform.
Für Phase 1 sind die relevanten Arbeitsbereiche:
- Architektur- und Persistenzfundament
- Quellenvalidierung
- ImportRun-Workflow
- lokale Analysepersistenz

Rahmenbedingungen:
- React/Vite/TypeScript Frontend
- FastAPI Backend
- Neo4j später, aber nicht operative Primärpersistenz in Phase 1
- Frontend nie direkt gegen Neo4j oder Ollama
- Rohdaten und fachliche Analyseergebnisse getrennt
- Recovery, Retry, Statuskonsistenz und Reviewbarkeit sind Pflicht

Deine Aufgabe:
1. Zerlege Phase 1 in Epics, Features und konkrete Tasks.
2. Berücksichtige Abhängigkeiten und sinnvolle Implementierungsreihenfolge.
3. Schätze Komplexität und Risiko qualitativ je Task.
4. Weise jedem Task ein klares Ergebnisartefakt zu:
   - Code
   - Migration
   - API
   - Test
   - Doku
   - Refactoring
5. Definiere pro Feature:
   - Ziel
   - Vorbedingungen
   - Abnahmekriterien
   - technische Risiken
6. Identifiziere Blocker und Parallelisierungspotenziale.
7. Formuliere einen realistischen Umsetzungsplan für ein kleines Team oder Solo-Entwicklung.

Antwortformat:
- Annahmen
- Epics
- Features je Epic
- konkrete Tasks je Feature
- Abhängigkeiten / Reihenfolge
- Risiko- und Komplexitätseinschätzung
- Ergebnisartefakte
- empfohlener Delivery-Plan

Wichtig:
- Keine agile Allgemeinsprache ohne Umsetzungsnutzen
- Fokus auf Entscheidbarkeit, Reihenfolge und technische Anschlussfähigkeit
- Tasks so formulieren, dass sie direkt in Tickets überführt werden können
```

# Empfohlene Reihenfolge

1. Architektur- und Persistenzfundament  
2. Quellenvalidierung  
3. ImportRun-Workflow  
4. Lokale Analysepersistenz  
5. Gesamtworkflow Phase 1  
6. Architekturkritik des Bestands  
7. Risikoanalyse  
8. Umsetzungsplan in Epic/Feature/Task-Struktur

Diese Reihenfolge minimiert Rework. Erst Architekturgrenzen, dann Eingangskontrolle, dann operative Pipeline, dann Ergebnispersistenz, danach Gesamtschnitt und Delivery-Plan.

### 9. Benutzer

beginne mit der umsetzung und dem coding

### 10. Assistent

Ich habe die Umsetzung als lauffähigen Backend-Starter für Phase 1 angelegt: SQLite-Persistenz, Sources, ImportRuns, ImportRunItems, AnalysisRuns, AnalysisResults, Review-Status, serverseitige Zustandsübergänge, Recovery von hängen gebliebenen Runs beim Start und Tests. Das passt zur Phase-1-Roadmap mit dauerhafter Statuspersistenz, lokaler Ergebnisspeicherung und strikter Backend-Kapselung. fileciteturn3file2turn3file3

Dateien:
- [Backend-Starter als ZIP](sandbox:/mnt/data/wdb_phase1_backend.zip)
- [Projektordner](sandbox:/mnt/data/wdb_phase1_backend)

Umgesetzt:
- `FastAPI`-App mit Routen für `sources`, `import-runs`, `analysis-runs`, `analysis-results`
- `SQLAlchemy`-Modelle für:
  - `Source`
  - `ImportRun`
  - `ImportRunItem`
  - `AnalysisRun`
  - `AnalysisResult`
- Zustandsautomat für Run- und Review-Transitionen
- serverseitige Quellenvalidierung für lokale Ordner
- lokale Persistenz von Analyseergebnissen, getrennt von Rohimport und ohne Neo4j-Write
- Startup-Recovery: `RUNNING -> ABANDONED`
- Tests für Quellenvalidierung, ImportRun-Lifecycle, Recovery, Analysepersistenz und Review

Bewusste Grenzen der ersten Coding-Runde:
- keine Integration in deine bestehende Codebasis, weil das Repository hier nicht vorliegt
- keine echte Hintergrund-Queue, nur vorbereitete Statuslogik
- kein Neo4j-Export, weil das laut Masterplan erst in Phase 2 gehört. fileciteturn3file3turn3file4

Nächster sinnvoller Schritt ist die Integration dieses Starters in dein bestehendes FastAPI-Projekt: bestehende `analysis_service`-, `import_job_service`- und Source-Registry-Pfade auf diese Persistenzschicht umstellen.

### 11. Benutzer

projekt ordnerdatei nochmals erstellen

### 12. Assistent

Projektordner wurde neu erstellt.

Download:  
[Projektordner als ZIP](sandbox:/mnt/data/wdb_phase1_backend_v2.zip)

Inhalt:

```
wdb_phase1_backend_v2
 ├─ app
 │  ├─ main.py
 │  ├─ db.py
 │  ├─ models.py
 │  └─ routes
 │     ├─ sources.py
 │     ├─ import_runs.py
 │     ├─ analysis_runs.py
 │     └─ analysis_results.py
 ├─ requirements.txt
 └─ README.md
```

Start lokal:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API-Endpunkte:

```
/api/sources
/api/import-runs
/api/analysis-runs
/api/analysis-results
```

Nächster Implementierungsschritt im Code:

1. Source-Validierungsservice
2. ImportRun-Scanner (Filesystem traversal)
3. ImportRunItem-Persistenz
4. AnalysisRun-Service
5. AnalysisResult-Persistenz + Review-State
6. Recovery-Logik (RUNNING → ABANDONED)

Danach folgt Phase-1-stabiler Workflow:

```
Source → Validate
       → ImportRun → ImportRunItems
       → AnalysisRun
       → AnalysisResults
       → Review
```

### 13. Benutzer

Beginne mit 1.

### 14. Assistent

Schritt 1 implementiert **Source-Validierung als Backend-Service**. Ziel: Registrierung ≠ Betriebsfähigkeit. Validierung muss deterministisch, serverseitig und persistent sein.

Implementierung erweitert das bestehende Scaffold um:

- `SourceValidationService`
- Validierungsstatusmodell
- echte Dateisystemprüfung
- Persistenz von Prüfergebnis + Timestamp
- API `/sources/{id}/validate`

---

# 1. Domänenstatus für Sources erweitern

Datei: `app/models.py`

```python
import enum

class SourceValidationStatus(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    VALID = "VALID"
    INVALID = "INVALID"
    INACCESSIBLE = "INACCESSIBLE"
```

Source Modell erweitern:

```python
class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    location_uri = Column(String, nullable=False)

    validation_status = Column(Enum(SourceValidationStatus), default=SourceValidationStatus.UNKNOWN)
    validation_message = Column(String, nullable=True)

    last_validated_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
```

---

# 2. Source Validation Service

Neuer Ordner:

```
app/services
```

Datei: `app/services/source_validation_service.py`

```python
import os
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import Source, SourceValidationStatus

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".eml"}


class SourceValidationService:

    @staticmethod
    def validate_source(db: Session, source: Source):

        path = source.location_uri

        if not os.path.exists(path):
            source.validation_status = SourceValidationStatus.INVALID
            source.validation_message = "Path does not exist"
            source.last_validated_at = datetime.utcnow()
            db.commit()
            return source

        if not os.access(path, os.R_OK):
            source.validation_status = SourceValidationStatus.INACCESSIBLE
            source.validation_message = "Path not readable"
            source.last_validated_at = datetime.utcnow()
            db.commit()
            return source

        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                source.validation_status = SourceValidationStatus.INVALID
                source.validation_message = f"Unsupported file type {ext}"
                source.last_validated_at = datetime.utcnow()
                db.commit()
                return source

        if os.path.isdir(path):
            found_supported = False
            for root, dirs, files in os.walk(path):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        found_supported = True
                        break
                if found_supported:
                    break

            if not found_supported:
                source.validation_status = SourceValidationStatus.INVALID
                source.validation_message = "No supported documents found"
                source.last_validated_at = datetime.utcnow()
                db.commit()
                return source

        source.validation_status = SourceValidationStatus.VALID
        source.validation_message = "Source valid"
        source.last_validated_at = datetime.utcnow()

        db.commit()

        return source
```

---

# 3. DB Dependency

Neue Datei:

`app/dependencies.py`

```python
from .db import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

# 4. API Endpoint erweitern

Datei: `app/routes/sources.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4

from ..models import Source
from ..dependencies import get_db
from ..services.source_validation_service import SourceValidationService

router = APIRouter()


@router.post("/")
def create_source(data: dict, db: Session = Depends(get_db)):

    source = Source(
        id=str(uuid4()),
        display_name=data["display_name"],
        location_uri=data["location_uri"],
    )

    db.add(source)
    db.commit()

    return source


@router.get("/")
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).all()


@router.post("/{source_id}/validate")
def validate_source(source_id: str, db: Session = Depends(get_db)):

    source = db.query(Source).filter(Source.id == source_id).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return SourceValidationService.validate_source(db, source)
```

---

# 5. Ergebnis: Verhalten der API

### Source erstellen

```
POST /api/sources
```

```json
{
  "display_name": "Mandant A",
  "location_uri": "/data/mandant_a"
}
```

---

### Source validieren

```
POST /api/sources/{source_id}/validate
```

Antwort:

```json
{
 "id": "...",
 "validation_status": "VALID",
 "validation_message": "Source valid"
}
```

---

# 6. Validierungslogik

Prüfungen:

| Check | Ergebnis |
|------|------|
Pfad existiert nicht | INVALID
keine Leserechte | INACCESSIBLE
Datei mit falschem Typ | INVALID
Ordner ohne unterstützte Dateien | INVALID
mindestens eine valide Datei | VALID

---

# 7. Nächster Schritt

Als nächstes wird implementiert:

**ImportRun Scanner + ImportRunItem Persistenz**

Erzeugt:

```
ImportRun
 ├─ ImportRunItems
 │   ├─ file path
 │   ├─ content type
 │   ├─ status
 │   └─ error
```

Dieser Schritt erzeugt die **erste echte Pipeline:**

```
Source
   ↓
Validation
   ↓
ImportRun
   ↓
ImportRunItems
```

Wenn du willst, implementiere ich im nächsten Schritt direkt:

**2. ImportRun Scanner + Statusmaschine (voll funktionsfähig).**

Das ist der Punkt, an dem dein System wirklich beginnt, Daten stabil zu ingestieren.

### 15. Benutzer

erstelle immer einen claude prompt für mich

### 16. Assistent

## Claude Prompt — Source Validation Service implementieren

```text
Arbeite als Senior Backend Engineer und Systems Architect.

Kontext:
Ich entwickle eine Wissens- und Analyseplattform.

Technischer Stack:
- Frontend: React + Vite + TypeScript
- Backend: FastAPI
- Datenbank: SQLite (Phase 1)
- Zielinfrastruktur später: Neo4j
- KI-Provider: Ollama / optional externe Provider
- Architekturregel: Frontend spricht ausschließlich mit FastAPI
- keine direkte Frontend-Kommunikation mit Neo4j oder KI-Providern

Aktueller Stand:
- FastAPI Backend existiert
- Source-Registry existiert
- Dokumentenscanning existiert
- unterstützte Dokumenttypen:
  - PDF
  - DOCX
  - TXT
  - EML

Problem:
Die aktuelle Source-Registry unterscheidet nicht zwischen:
- registrierter Source
- technisch validierter Source
- operativ nutzbarer Source

Ziel:
Implementierung eines **serverseitigen Source Validation Services**, der lokale Quellen zuverlässig prüft und das Ergebnis persistent speichert.

Anforderungen:

Die Validierung muss folgende Prüfungen durchführen:

1. Pfad existiert
2. Pfad ist lesbar
3. Pfadtyp:
   - Datei
   - Verzeichnis
4. Dateitypprüfung:
   unterstützte Typen:
   - .pdf
   - .docx
   - .txt
   - .eml
5. Ordnerprüfung:
   mindestens eine unterstützte Datei vorhanden
6. klare Fehlermeldungen

Persistierte Felder im Source Modell:

- source_id
- display_name
- location_uri
- validation_status
- validation_message
- last_validated_at
- created_at

Statusmodell:

SourceValidationStatus

UNKNOWN  
VALID  
INVALID  
INACCESSIBLE

API Verhalten:

POST /api/sources
→ Source registrieren

GET /api/sources
→ Liste aller Sources

POST /api/sources/{source_id}/validate
→ Source serverseitig validieren

Technische Anforderungen:

- FastAPI
- SQLAlchemy oder SQLModel
- SQLite
- serverseitige Dateisystemprüfung (os / pathlib)
- Dependency Injection für DB Sessions
- Service-Layer für Validation Logic

Deine Aufgabe:

1. Entwerfe die benötigten Backend-Module
2. Implementiere:
   - Source Model
   - Validation Status Enum
   - SourceValidationService
   - API Endpoints
3. Trenne klar:

routes  
services  
models  
db

4. Implementiere robuste Fehlerbehandlung.
5. Liefere vollständigen Beispielcode für:

- models.py
- source_validation_service.py
- dependencies.py
- routes/sources.py

Antwortformat:

1. Architekturüberblick
2. Datenmodell
3. Service Implementierung
4. API Implementierung
5. Beispielablauf

Wichtig:

- Fokus auf Stabilität und Wartbarkeit
- keine Pseudo-Implementierungen
- keine Frontend-Logik
- keine Neo4j-Integration in dieser Phase
- klare Trennung zwischen Rohdaten und Analyse
```

### 17. Benutzer

weiter

### 18. Assistent

## Claude Prompt — ImportRun Scanner + Statusmaschine implementieren

```text
Arbeite als Senior Backend Engineer, Workflow Architect und Systems Reviewer.

Kontext:
Ich entwickle eine Wissens- und Analyseplattform.

Technischer Stack:
- Frontend: React + Vite + TypeScript
- Backend: FastAPI
- Datenbank: SQLite in Phase 1
- spätere Zielinfrastruktur: Neo4j
- KI-Provider nur über das Backend
- Architekturregel: kein Frontend-Zugriff auf Neo4j oder KI-Provider

Bereits vorhanden:
- Source-Registry
- serverseitige Source-Validierung
- lokale Dokumentquellen
- unterstützte Dateitypen:
  - PDF
  - DOCX
  - TXT
  - EML

Jetzt umzusetzen:
ImportRun-Workflow mit Scanner, persistierten Run-Objekten, Item-Ebene und belastbarer Statusmaschine.

Ziel:
Eine lokale Source soll nach erfolgreicher Validierung in einen ImportRun überführt werden.
Der ImportRun scannt Dateiobjekte, legt pro Datei ImportRunItems an und hält Fortschritt, Teilfehler und Endstatus persistent fest.

Domänenobjekte:

1. ImportRun
Felder:
- id
- source_id
- status
- started_at
- finished_at
- files_discovered_count
- files_processed_count
- files_succeeded_count
- files_failed_count
- warning_count
- error_count
- last_error_code
- last_error_message
- restart_of_run_id optional
- created_at
- updated_at

2. ImportRunItem
Felder:
- id
- import_run_id
- path
- relative_path optional
- content_type
- file_extension
- parse_status
- content_hash optional
- size_bytes optional
- discovered_at
- processed_at optional
- error_code optional
- error_message optional
- created_at
- updated_at

Statusmodell für ImportRun:

CREATED  
QUEUED  
RUNNING  
PARTIALLY_COMPLETED  
COMPLETED  
FAILED  
CANCELLED  
ABANDONED

Statusmodell für ImportRunItem:

DISCOVERED  
PROCESSING  
SUCCEEDED  
FAILED  
SKIPPED

Verhalten:

1. Ein ImportRun darf nur für eine valide Source gestartet werden.
2. Scanner läuft über lokale Datei- oder Verzeichnisquelle.
3. Für jede gefundene unterstützte Datei wird ein ImportRunItem erzeugt.
4. Teilfehler dürfen den Gesamtlauf nicht abbrechen, solange sie isolierbar sind.
5. Defekte oder nicht lesbare Dateien müssen als FAILED auf Item-Ebene gespeichert werden.
6. Der Run aggregiert Counters laufend und persistiert sie.
7. Nach Prozessabbruch dürfen RUNNING-Runs beim Neustart nicht stillschweigend verschwinden:
   - Recovery-Regel: RUNNING → ABANDONED
8. Retry muss als neuer Run modelliert werden, optional mit restart_of_run_id.
9. Cancel muss sauber auf Run-Ebene möglich sein.
10. Keine Vermischung mit Analysepersistenz in diesem Schritt.

API-Endpunkte:

POST /api/import-runs
→ neuen ImportRun starten

GET /api/import-runs/{run_id}
→ Run-Status abrufen

GET /api/import-runs
→ Runs listen

GET /api/import-runs/{run_id}/items
→ Items des Runs abrufen

POST /api/import-runs/{run_id}/retry
→ Retry als neuer Run

POST /api/import-runs/{run_id}/cancel
→ kooperativer Abbruch

Technische Anforderungen:
- FastAPI
- SQLAlchemy oder SQLModel
- SQLite
- Service-Layer
- Repository-Struktur oder klare Persistenztrennung
- DB Session Dependency
- Dateisystemzugriff serverseitig
- keine Frontend-Logik
- keine Neo4j-Logik
- keine Analyse-Logik in diesem Task

Deine Aufgabe:

1. Entwerfe die nötige Backend-Struktur.
2. Implementiere vollständig:
   - RunStatus Enum
   - ItemStatus Enum
   - ImportRun Modell
   - ImportRunItem Modell
   - ImportRunService
   - Scan-Logik für lokale Sources
   - Statusübergänge
   - Counter-Aggregation
   - Recovery von RUNNING zu ABANDONED beim App-Start
   - API-Endpunkte
3. Liefere vollständigen Beispielcode für:
   - models.py
   - services/import_run_service.py
   - routes/import_runs.py
   - ggf. recovery/startup code
4. Implementiere robuste Fehlerbehandlung.
5. Erkläre Designentscheidungen dort, wo Statuskonsistenz und Recovery kritisch sind.

Antwortformat:

1. Architekturüberblick
2. Datenmodell
3. Statusmaschine
4. Service Implementierung
5. API Implementierung
6. Recovery-Mechanismus
7. Beispielablauf

Wichtig:
- Fokus auf Persistenz, Recovery und Teilfehlerisolierung
- keine Schein-Asynchronität
- keine Platzhalter
- keine Vermischung mit AnalysisRun oder AnalysisResult
- Code muss auf Phase 1 Stabilität optimiert sein
```

### 19. Benutzer

weiter

### 20. Assistent

## Claude Prompt — Lokales Parsing in den ImportRun integrieren

```text
Arbeite als Senior Backend Engineer, Parsing Architect und Systems Reviewer.

Kontext:
Ich entwickle eine Wissens- und Analyseplattform.

Technischer Stack:
- Frontend: React + Vite + TypeScript
- Backend: FastAPI
- Datenbank: SQLite in Phase 1
- spätere Zielinfrastruktur: Neo4j
- KI-Provider nur über das Backend
- Architekturregel: kein Frontend-Zugriff auf Neo4j oder KI-Provider

Bereits vorhanden:
- Source-Registry
- serverseitige Source-Validierung
- ImportRun-Workflow mit ImportRun und ImportRunItem
- Scanner für lokale Dokumentquellen
- unterstützte Dateitypen:
  - PDF
  - DOCX
  - TXT
  - EML

Jetzt umzusetzen:
Die Scan-Phase soll um eine belastbare Parsing- und Normalisierungsphase erweitert werden, ohne AnalysisRun oder KI-Analyse einzubeziehen.

Ziel:
Für jedes ImportRunItem soll aus einer unterstützten Quelldatei reproduzierbar ein lokales Rohtext-/Metadaten-Ergebnis erzeugt werden.
Die Verarbeitung muss fehlertolerant, persistent nachvollziehbar und pro Datei isoliert sein.

Domänenobjekte:

1. ImportRun
besteht bereits und aggregiert Counters sowie Gesamtstatus

2. ImportRunItem
besteht bereits und soll erweitert bzw. konkretisiert werden um:
- parse_status
- normalization_status optional
- raw_text_path oder raw_text_blob
- raw_metadata_json
- detected_encoding optional
- parser_name
- parser_version optional
- processed_at
- error_code
- error_message

Empfohlenes Statusmodell auf Item-Ebene:

DISCOVERED  
PROCESSING  
PARSED  
NORMALIZED  
FAILED  
SKIPPED

Verhalten:

1. Nur unterstützte Dateitypen werden verarbeitet.
2. Jede Datei wird parser-spezifisch behandelt:
   - PDF → Text + Basis-Metadaten
   - DOCX → Text + Basis-Metadaten
   - TXT → Text + Encoding-Erkennung/Absicherung
   - EML → Header, Body, Basis-Metadaten
3. Rohdaten dürfen nicht überschrieben werden.
4. Parser-Output muss lokal persistent ablegbar sein.
5. Parsing-Fehler müssen pro Item gespeichert werden.
6. Ein fehlerhaftes Item darf den Gesamtrun nicht abbrechen, sofern isolierbar.
7. Normalisierung ist von Parsing logisch getrennt.
8. Encoding-Probleme müssen explizit behandelt werden.
9. ImportRun-Counters müssen Parsing-Erfolg und Parsing-Fehler korrekt aggregieren.
10. Noch keine KI-Analyse in diesem Schritt.

Technische Anforderungen:
- FastAPI Backend
- SQLite
- lokale Persistenz
- klare Trennung zwischen:
  - Scan
  - Parse
  - Normalisierung
- Service-Layer
- parser-spezifische Adapter oder Strategien
- keine Frontend-Logik
- keine Neo4j-Logik
- keine AnalysisRun/AnalysisResult-Logik in diesem Schritt

Deine Aufgabe:

1. Entwerfe die Backend-Struktur für die Parsing-Stufe innerhalb des ImportRun-Workflows.
2. Definiere die Verantwortlichkeiten von:
   - ImportRunService
   - ParserRegistry oder ParserFactory
   - Dateityp-spezifischen Parsern
   - optionaler Normalisierungslogik
3. Implementiere vollständig:
   - erweiterte Item-Modelle/Felder
   - Parse-Statusmodell
   - Parser-Auswahl je Dateityp
   - persistente Ablage von Rohtext und Metadaten
   - Fehlerbehandlung pro Item
   - Aggregation auf Run-Ebene
4. Liefere vollständigen Beispielcode für:
   - models.py
   - services/import_run_service.py
   - services/parsers/*
   - routes/import_runs.py falls API-Anpassung nötig
5. Beschreibe, wie Rohtext und Metadaten gespeichert werden sollen:
   - direkt in SQLite
   - als Filesystem-Artefakt mit Referenz in DB
   - Trade-offs explizit
6. Erkläre die Recovery- und Wiederanlauf-Fähigkeit bei:
   - Parser-Absturz
   - Encoding-Fehler
   - korrupten Dateien
   - teilweise verarbeitetem Run

Antwortformat:

1. Architekturüberblick
2. Datenmodell
3. Parse- und Normalisierungsstatus
4. Service- und Parser-Struktur
5. Persistenzstrategie für Rohtext/Metadaten
6. Fehlerbehandlung und Recovery
7. API-Anpassungen
8. Beispielablauf

Wichtig:
- Fokus auf Rohdatenverarbeitung, nicht auf KI-Analyse
- Parsing und Normalisierung strikt von späterer Analyse trennen
- keine Scheinabstraktion ohne operativen Nutzen
- Code und Modellierung auf Neustartfestigkeit, Reviewbarkeit und Erweiterbarkeit ausrichten
```

### 21. Benutzer

weiter

### 22. Assistent

## Claude Prompt — AnalysisRun + lokale Analysepersistenz implementieren

```text
Arbeite als Senior Backend Engineer, Systems Architect und Review-Workflow Designer.

Kontext:
Ich entwickle eine Wissens- und Analyseplattform.

Technischer Stack:
- Frontend: React + Vite + TypeScript
- Backend: FastAPI
- Datenbank: SQLite in Phase 1
- spätere Zielinfrastruktur: Neo4j
- KI-Provider nur über das Backend
- Architekturregel: kein Frontend-Zugriff auf Neo4j oder KI-Provider

Bereits vorhanden bzw. umgesetzt:
- Source-Registry
- serverseitige Source-Validierung
- ImportRun-Workflow
- ImportRunItem-Scanning
- Parsing- und Normalisierungsstufe für lokale Dokumente
- lokale Rohdaten-/Metadatenpersistenz pro ImportRunItem

Jetzt umzusetzen:
AnalysisRun und lokale Analysepersistenz als getrennte fachliche Persistenzschicht oberhalb des Rohimports.

Ziel:
Ein abgeschlossener oder teilweise erfolgreicher ImportRun soll als Grundlage für einen AnalysisRun dienen.
Die Analyse erzeugt pro geeignetem ImportRunItem persistente AnalysisResults.
Diese Ergebnisse bleiben lokal gespeichert, reviewbar und von Rohdaten getrennt.
Ein späterer Export nach Neo4j wird vorbereitet, aber in diesem Schritt nicht implementiert.

Domänenobjekte:

1. AnalysisRun
Felder:
- id
- import_run_id
- source_id optional zur schnelleren Filterung
- provider
- provider_model
- status
- started_at
- finished_at
- documents_targeted_count
- documents_analyzed_count
- documents_succeeded_count
- documents_failed_count
- warning_count
- error_count
- last_error_code
- last_error_message
- restart_of_run_id optional
- created_at
- updated_at

2. AnalysisResult
Felder:
- id
- analysis_run_id
- import_run_item_id
- result_type
- review_status
- schema_version
- input_hash
- raw_output_json
- normalized_output_json optional
- confidence_score optional
- provider
- provider_model
- generated_at
- approved_at optional
- approved_by optional
- supersedes_result_id optional
- created_at
- updated_at

Empfohlenes Statusmodell für AnalysisRun:

CREATED  
QUEUED  
RUNNING  
PARTIALLY_COMPLETED  
COMPLETED  
FAILED  
CANCELLED  
ABANDONED

Review-Statusmodell für AnalysisResult:

UNREVIEWED  
APPROVED  
REJECTED  
SUPERSEDED

Verhalten:

1. Ein AnalysisRun darf nur gestartet werden, wenn der referenzierte ImportRun in einem geeigneten Zustand ist:
   - COMPLETED
   - PARTIALLY_COMPLETED
2. Es werden nur geeignete ImportRunItems analysiert:
   - erfolgreich geparst / normalisiert
   - Rohtext oder verwertbarer Inhalt vorhanden
3. Die Analyseergebnisse müssen lokal persistent gespeichert werden.
4. Rohdaten dürfen nie überschrieben werden.
5. Raw Output und normalisiertes Ergebnis müssen getrennt gespeichert werden.
6. Fehler pro analysiertem Dokument müssen isoliert speicherbar sein.
7. Ein fehlerhaftes Einzelresultat darf nicht automatisch den gesamten AnalysisRun abbrechen, sofern der Fehler isolierbar ist.
8. Doppelte oder erneute Analyseläufe müssen sauber modelliert werden:
   - Re-Run
   - Supersession
9. Review-Status muss unabhängig vom Rohdatenbestand änderbar sein.
10. Noch kein Neo4j-Write in diesem Schritt.
11. Keine direkte Providerkommunikation im Frontend.

API-Endpunkte:

POST /api/analysis-runs
→ neuen AnalysisRun starten

GET /api/analysis-runs/{run_id}
→ Status abrufen

GET /api/analysis-runs
→ Runs listen

GET /api/analysis-runs/{run_id}/results
→ Results des Runs abrufen

GET /api/analysis-results/{result_id}
→ einzelnes Result abrufen

POST /api/analysis-results/{result_id}/review
→ Review-Status setzen

Technische Anforderungen:
- FastAPI
- SQLite
- Service-Layer
- klare Trennung zwischen:
  - Import-/Rohdatenpersistenz
  - Analysepersistenz
  - späterem Export
- Provider-Abstraktion nur backendseitig
- defensive Fehlerbehandlung
- keine Neo4j-Logik
- keine Frontend-Logik

Deine Aufgabe:

1. Entwerfe die nötige Backend-Struktur für AnalysisRun und AnalysisResult.
2. Implementiere vollständig:
   - AnalysisRun Status Enum
   - ReviewStatus Enum
   - AnalysisRun Modell
   - AnalysisResult Modell
   - AnalysisRunService
   - lokale Persistenz von Analyseergebnissen
   - Re-Run-/Supersession-Logik
   - Review-Status-Update
   - Recovery von RUNNING zu ABANDONED beim App-Start
   - API-Endpunkte
3. Liefere vollständigen Beispielcode für:
   - models.py
   - services/analysis_run_service.py
   - routes/analysis_runs.py
   - routes/analysis_results.py
   - ggf. startup/recovery code
4. Begründe Designentscheidungen dort, wo Reviewbarkeit, Supersession und Trennung von Rohdaten kritisch sind.
5. Beschreibe explizit, was lokal gespeichert wird und was bewusst noch nicht nach Neo4j gehört.

Antwortformat:

1. Architekturüberblick
2. Datenmodell
3. Status- und Reviewmodell
4. Service Implementierung
5. API Implementierung
6. Recovery-Mechanismus
7. Re-Run- und Supersession-Strategie
8. Beispielablauf

Wichtig:
- Fokus auf lokale Analysepersistenz, Reviewbarkeit und spätere Exportfähigkeit
- keine Vermischung mit Neo4j-Write
- keine Überschreibung von Rohdaten
- keine Pseudo-Implementierung
- Code und Modellierung auf Stabilität, Nachvollziehbarkeit und Erweiterbarkeit ausrichten
```

### 23. Benutzer

weiter

### 24. Assistent

## Claude Prompt — Review-Workflow, Freigabelogik und Export-Vorbereitung zu Neo4j vorbereiten

```text
Arbeite als Senior Systems Architect, Review-Workflow Designer und Backend Engineer.

Kontext:
Ich entwickle eine Wissens- und Analyseplattform.

Technischer Stack:
- Frontend: React + Vite + TypeScript
- Backend: FastAPI
- Datenbank: SQLite in Phase 1
- spätere Zielinfrastruktur: Neo4j
- KI-Provider nur über das Backend
- Architekturregel: kein Frontend-Zugriff auf Neo4j oder KI-Provider

Bereits vorhanden bzw. umgesetzt:
- Source-Registry
- serverseitige Source-Validierung
- ImportRun-Workflow
- ImportRunItem-Scanning
- Parsing- und Normalisierungsstufe
- AnalysisRun
- lokale AnalysisResult-Persistenz
- Review-Status auf AnalysisResult-Ebene

Jetzt umzusetzen:
Ein belastbarer Review-Workflow für lokale Analyseergebnisse sowie die technische Vorbereitung eines späteren, strikt getrennten Exports freigegebener Ergebnisse nach Neo4j.

Ziel:
Analyseergebnisse sollen vor einem späteren Graph-Export fachlich geprüft, freigegeben, verworfen oder durch neuere Ergebnisse ersetzt werden können.
Phase 1 endet weiterhin lokal. Es soll aber ein sauberes Modell entstehen, das den späteren Neo4j-Export ohne Rework ermöglicht.

Domänenobjekte:

1. AnalysisResult
bereits vorhanden mit:
- id
- analysis_run_id
- import_run_item_id
- result_type
- review_status
- schema_version
- input_hash
- raw_output_json
- normalized_output_json
- confidence_score
- provider
- provider_model
- generated_at
- approved_at optional
- approved_by optional
- supersedes_result_id optional
- created_at
- updated_at

2. ReviewEvent oder AnalysisResultReviewEvent
neu zu prüfen / optional einzuführen:
- id
- analysis_result_id
- previous_review_status
- new_review_status
- changed_by
- changed_at
- comment optional
- reason_code optional

3. ExportCandidate oder ExportQueueEntry
nur als Vorbereitungsmodell, noch ohne Neo4j-Write:
- id
- analysis_result_id
- export_status
- eligible_at
- blocked_reason optional
- created_at
- updated_at

Empfohlenes Review-Statusmodell:

UNREVIEWED  
APPROVED  
REJECTED  
SUPERSEDED

Optionales ExportStatus-Modell:

NOT_ELIGIBLE  
ELIGIBLE  
BLOCKED  
EXPORTED  
EXPORT_FAILED

Wichtige Rahmenbedingungen:

1. Kein Neo4j-Write in diesem Schritt.
2. Nur APPROVED Results dürfen später grundsätzlich exportfähig sein.
3. Rohdaten und Analyseergebnisse bleiben getrennt.
4. Review-Entscheidungen müssen auditierbar sein.
5. Re-Run und Supersession müssen fachlich sauber modelliert werden.
6. Spätere Graph-Transformation darf nicht implizit in die lokale Analysepersistenz eingebaut werden.
7. Frontend bleibt rein gegen FastAPI.
8. Kein Direktzugriff aus dem Frontend auf Neo4j oder Provider.

Fachliches Verhalten:

1. AnalysisResults starten als UNREVIEWED.
2. Reviewer können ein Ergebnis:
   - APPROVED
   - REJECTED
3. Ein neueres Ergebnis kann ein altes Ergebnis superseden:
   - APPROVED → SUPERSEDED
   - REJECTED → SUPERSEDED optional nur bei fachlicher Relevanz
4. Review-Änderungen müssen nachvollziehbar sein.
5. Ein Ergebnis ist exportfähig nur wenn:
   - review_status = APPROVED
   - normalized_output_json vorhanden und strukturell valide
   - Ergebnis nicht SUPERSEDED
6. Exportfähigkeit ist noch nur lokal vorzubereiten, nicht tatsächlich auszuführen.
7. Es muss klar getrennt sein zwischen:
   - fachlicher Freigabe
   - technischer Exportfähigkeit
   - tatsächlichem Export

API-Endpunkte:

GET /api/analysis-runs/{run_id}/results
→ Ergebnisse eines Laufs abrufen

GET /api/analysis-results/{result_id}
→ einzelnes Ergebnis abrufen

POST /api/analysis-results/{result_id}/review
→ Review-Status setzen

GET /api/analysis-results/{result_id}/history
→ Review-/Statushistorie abrufen

GET /api/export-candidates
→ lokal exportfähige Ergebnisse listen

Technische Anforderungen:
- FastAPI
- SQLite
- Service-Layer
- auditierbare Review-Änderungen
- klare Trennung von Review-Logik und späterer Export-Logik
- keine Neo4j-Integration in diesem Task
- keine Frontend-Logik
- defensive Fehlerbehandlung

Deine Aufgabe:

1. Entwerfe die nötige Backend-Struktur für:
   - Review-Workflow
   - Review-Historie
   - Export-Vorbereitung
2. Definiere, welche zusätzlichen Tabellen/Modelle sinnvoll sind.
3. Implementiere vollständig:
   - ReviewEvent oder äquivalentes Audit-Modell
   - Regeln für zulässige Review-Status-Übergänge
   - Supersession-Logik
   - Berechnung lokaler Exportfähigkeit
   - API-Endpunkte für Review, Historie und Export-Candidates
4. Liefere vollständigen Beispielcode für:
   - models.py
   - services/review_service.py
   - routes/analysis_results.py
   - optional routes/export_candidates.py
5. Begründe Designentscheidungen dort, wo Trennung von Freigabe, Exportfähigkeit und späterem Export kritisch ist.
6. Beschreibe explizit, welche Informationen jetzt lokal persistiert werden und welche bewusst erst in einer späteren Neo4j-Exportphase entstehen dürfen.

Antwortformat:

1. Architekturüberblick
2. Datenmodell
3. Review- und Supersession-Regeln
4. Audit-/Historienmodell
5. Export-Vorbereitungslogik
6. API Implementierung
7. Beispielablauf

Wichtig:
- Fokus auf Reviewbarkeit, Nachvollziehbarkeit und Export-Vorbereitung
- kein Neo4j-Write
- keine Vermischung von lokaler Freigabelogik mit Graph-Persistenz
- keine Pseudo-Implementierung
- Modellierung auf spätere Erweiterbarkeit und geringe Rework-Kosten ausrichten
```
