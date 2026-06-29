---
title: "Code-Stand vs. Masterplan"
type: chatgpt_conversation
source: chatgpt
source_id: "6a310127-f518-83eb-91f2-bc25a34c2cd9"
created: 2026-06-16
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
---


# Code-Stand vs. Masterplan

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6a310127-f518-83eb-91f2-bc25a34c2cd9`
- Nachrichten: 19

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Ich prüfe den ZIP-Inhalt, suche Masterplan-/Entwicklungsdokumente und gleiche danach Code, Architektur, Features, Tests und bekannte Release-Gates gegen den Plan ab.

### 2. Benutzer

das ist der aktuelle Code stand vergleiche es mit dem Masterplan

### 3. Assistent

## Vergleich Code-Stand vs. Masterplan

**Gesamturteil: BLOCKED. Keine RC-Freigabe.**

| Bereich | Masterplan-Ziel | Code-Stand | Bewertung |
|---|---:|---:|---|
| Produktreife | RC ≥ 80 / GA ≥ 85 | 53 | BLOCKED |
| Gold Path | RC ≥ 7/8, GA 8/8 | 4/8 | BLOCKED |
| Technische IDs in UI | 0 | 0 | PASS |
| Security Blocker | 0 | 0 | PASS |
| Frontend Tests | stabil | 134/134 PASS | PASS |
| Release Gate | CONDITIONAL_RC möglich | BLOCKED | FAIL |

## Hauptabweichungen

1. **Topics / Themen**
   - Masterplan: Themen finden, filtern, anzeigen, zusammenführen.
   - Code-Stand: `TopicsPage.jsx` und `topics.js` vorhanden, aber Backend/ORM/API laut Status nicht vollständig.
   - Wirkung: **GP-04 FAIL**, Themen-Reife 0.

2. **Analyse**
   - Masterplan: Analyse starten, Ergebnis anzeigen, bearbeiten, freigeben, importieren.
   - Code-Stand: Backend-Services vorhanden, aber `AnalysisPage.jsx` fehlt als produktiver UX-Pfad.
   - Wirkung: **GP-05 FAIL**, **GP-06 FAIL sicherheitskritisch**.

3. **Export**
   - Masterplan: Such-/Analyseergebnis exportierbar, PDF relevant.
   - Code-Stand: Export Center fehlt produktiv; JSON/MD nur als geplante RC-Limitation.
   - Wirkung: **GP-07 FAIL**, GA blockiert durch fehlenden PDF-Export.

4. **Dashboard**
   - Masterplan: modernes Dashboard mit allen wichtigen Anzeigen.
   - Code-Stand: W01–W05 vorhanden, Drift-Widget/API fehlt.
   - Wirkung: kein RC-Blocker, aber Reifeverlust.

5. **Dokumentenbereich**
   - Masterplan: Import, Anzeige, Metadaten, keine technischen IDs.
   - Code-Stand: weitgehend erfüllt. Technische ID-Leaks wurden behoben.
   - Wirkung: stabiler Bereich.

## Aktueller Status aus Reports

- `masterplan_status.json`: **BLOCKED**, Fortschritt **42 %**
- `product_maturity_v3.json`: Score **53**
- `product_gold_path.json`: **4/8 PASS**
- `conditional_rc_decision.json`: **BLOCKED**
- `ui_technical_id_leak_audit.json`: **PASS**, 0 Leaks
- `product_release_gate.json`: **BLOCKED**

## Priorisierte nächste Umsetzung

1. Topics-Backend komplettieren: ORM, API, Detailansicht, Dokument-Verknüpfung.
2. `AnalysisPage.jsx` produktiv bauen: Start, Jobstatus, Ergebnis, Bearbeitung, Approval.
3. Approval-Sicherheit absichern: keine Freigabe ohne expliziten User-Commit.
4. Export Center MVP bauen: mindestens Markdown/JSON; PDF-Entscheidung für GA festlegen.
5. Dashboard Drift-Endpoint ergänzen.
6. Danach Gold Path erneut ausführen.

## Entscheidung

**Nicht releasefähig.**

**RC erst möglich bei:**
- Product Maturity ≥ 80
- Gold Path mindestens 7/8
- GP-06 zwingend PASS
- technische IDs weiterhin 0
- offene Limitationen dokumentiert

Aktuell fehlen vor allem produktrelevante Hauptpfade, nicht Architekturgrundlagen.

### 4. Assistent

# PRI-1 – Themenbereich (Topics) vollständig implementieren
Ziel: GP-04 schließen und den Themenbereich gemäß Masterplan produktiv nutzbar machen.

Abschlusskriterien:
- Themenübersicht vorhanden
- Filter nach Kategorien und Tags
- Dokumentzuordnung sichtbar
- KI-Zusammenführung möglich
- Bearbeitungsworkflow vorhanden
- Freigabe vor Persistierung
- Tests grün

---

# Prompt 1.1 – Datenmodell Topics finalisieren

```text
Analysiere das bestehende Prisma-Schema und implementiere das vollständige Themenmodell.

Anforderungen:

Entity Topic:
- id UUID
- title
- slug
- summary
- status:
  DRAFT
  REVIEW
  APPROVED
  ARCHIVED
- createdAt
- updatedAt
- createdBy
- approvedAt nullable

Entity TopicDocument:
- id UUID
- topicId
- documentId
- relationType:
  PRIMARY
  RELATED
  REFERENCE

Entity TopicTag:
- topicId
- tagId

Anforderungen:
- Alle Tabellen mit Indizes versehen
- Soft-Delete berücksichtigen
- Workspacefähigkeit vorbereiten
- Migration erzeugen
- Seeddaten erstellen
- Repository Layer vorbereiten

Lieferung:
- Prisma Schema
- Migration
- Repository Interfaces
- Seeddateien
```

---

# Prompt 1.2 – Topic Service Layer

```text
Implementiere den vollständigen TopicService.

Funktionen:

createTopic()
updateTopic()
deleteTopic()
archiveTopic()
approveTopic()
getTopic()
listTopics()
searchTopics()
attachDocument()
detachDocument()
addTag()
removeTag()

Anforderungen:
- Transaktionen verwenden
- Fehlerklassen einführen
- DTO Validation
- Pagination
- Sortierung
- Filter:
  Status
  Kategorie
  Tag
  Zeitraum

Tests:
- Service Unit Tests
- Repository Integration Tests
```

---

# Prompt 1.3 – Topic API

```text
Implementiere die REST API für Topics.

Endpoints:

GET /api/topics
GET /api/topics/:id
POST /api/topics
PUT /api/topics/:id
DELETE /api/topics/:id

POST /api/topics/:id/approve
POST /api/topics/:id/archive

POST /api/topics/:id/documents
DELETE /api/topics/:id/documents/:documentId

POST /api/topics/:id/tags
DELETE /api/topics/:id/tags/:tagId

Anforderungen:
- Zod Validation
- OpenAPI Dokumentation
- Error Middleware
- Contract Tests
- Response DTOs

Tests:
- Success
- Validation Error
- Not Found
- Duplicate
- Rollback
```

---

# Prompt 1.4 – Themenübersicht GUI

```text
Implementiere die vollständige TopicsPage.

Aufbau:

Header
- Seitentitel
- Suche
- Neuerstellen

Filterleiste:
- Status
- Kategorie
- Tags
- Zeitraum

Content:
- Kartenansicht
- Tabellenansicht

Topic Card:
- Titel
- Kurzbeschreibung
- Anzahl Dokumente
- Anzahl Tags
- Status
- Letzte Änderung

Aktionen:
- Öffnen
- Bearbeiten
- Archivieren
- Löschen

Responsive Design.
Telekom Branding.
Dark Mode unterstützen.
```

---

# Prompt 1.5 – Topic Detailseite

```text
Implementiere TopicDetailPage.

Bereiche:

1. Stammdaten
2. Zusammenfassung
3. Verknüpfte Dokumente
4. Tags
5. Historie

Dokumentbereich:
- Dokument hinzufügen
- Dokument entfernen
- Vorschau

Tagbereich:
- Tags hinzufügen
- Tags entfernen

Status Workflow:
DRAFT
REVIEW
APPROVED
ARCHIVED

Approval Dialog:
- Zusammenfassung anzeigen
- Benutzerbestätigung notwendig
- Erst nach Bestätigung persistieren
```

---

# Prompt 1.6 – KI-Zusammenführung

```text
Implementiere TopicMergeService.

Workflow:

1. Mehrere Dokumente auswählen
2. Inhalte laden
3. KI-Zusammenfassung erzeugen
4. Quellen referenzieren
5. Ergebnis editierbar machen
6. Vorschau anzeigen
7. Benutzerfreigabe
8. Topic persistieren

Provider:
- Ollama
- OpenAI
- Gemini

Provider Interface:
generateTopicSummary()

Anforderungen:
- Retry Mechanismus
- Timeout
- Tokenbegrenzung
- Progress Events
- Audit Logging

Tests erstellen.
```

---

# Prompt 1.7 – Zusammenführungsdialog GUI

```text
Implementiere TopicMergeDialog.

Schritte:

Step 1:
Dokumente auswählen

Step 2:
Prompt konfigurieren

Step 3:
KI Analyse starten

Step 4:
Ergebnis anzeigen

Step 5:
Manuelle Bearbeitung

Step 6:
Freigabe

Step 7:
Persistierung

Anforderungen:
- Autosave
- Loading States
- Fehlerdialoge
- Retry
- Fortschrittsanzeige
```

---

# Prompt 1.8 – Topics Suchintegration

```text
Erweitere die globale Suche.

Anforderungen:

Suche über:
- Titel
- Zusammenfassungen
- Tags
- Dokumente

Ergebnisse:
- Relevanzscore
- Trefferhighlighting
- Filter
- Sortierung

Pagination:
Cursor basiert.

Tests erstellen.
```

---

# Prompt 1.9 – Topics Dashboard Widgets

```text
Implementiere Dashboard Widgets.

Widgets:

- Anzahl Themen
- Themen pro Kategorie
- Themenstatus
- Neu erzeugte Themen
- Unbearbeitete Reviews
- Häufig verwendete Tags

Charts:
- Balkendiagramm
- Donut
- Trenddiagramm

Skeleton Loader implementieren.
```

---

# Prompt 1.10 – Topics Gate

```text
Führe vollständige Produktprüfung durch.

Prüfen:

Backend
Frontend
API
Tests
Performance
Accessibility
Dark Mode
Error Handling

Erzeuge:

topics_coverage.json
topics_gold_path.json
topics_release_report.json
masterplan_status.json
development.md

Aktualisiere:
Masterplan.md
Entwicklung.md

Dokumentiere:
- Implementierte Features
- Offene Punkte
- Bekannte Limitationen
- Reifegrad
- Nächste Prioritäten
```

---

# PRI-2 (nach Abschluss von PRI-1)
Analysebereich vollständig produktiv.

# PRI-3
Export Center inklusive PDF.

# PRI-4
Dashboard Drift Analytics.

# PRI-5
Release Hardening, Gold Path, RC-Gates und GA-Gates.

Regel für alle weiteren Pakete:

```text
Nach Abschluss jedes Pakets:

1. Masterplan.md aktualisieren
2. Entwicklung.md aktualisieren
3. masterplan_status.json aktualisieren
4. product_maturity_v3.json neu berechnen
5. product_gold_path.json neu berechnen
6. release_gate.json aktualisieren
7. Offene Risiken dokumentieren
8. Nächste Prioritäten automatisch einplanen
```

### 5. Benutzer

entwickle auf grundlage des masterplan und deiner analyse die pri Themen punkt für punkt ab und liefere mir die entwicklungsprompts dazu. nach jedem Paket werden die dokumentationen aktualieseirt

### 6. Assistent

# PRI-2 – Analysebereich produktiv fertigstellen

Ziel: GP-05 und GP-06 schließen.

---

# Prompt 2.1 – Analyse-Datenmodell finalisieren

```text
Implementiere das vollständige Datenmodell für Analyse-Jobs.

Entities:

AnalysisJob:
- id UUID
- workspaceId nullable
- status: QUEUED | RUNNING | COMPLETED | FAILED | CANCELLED
- sourceType: DOCUMENTS | TOPIC | SEARCH_RESULT
- sourceIds JSON
- prompt
- provider
- model
- resultId nullable
- errorMessage nullable
- createdAt
- startedAt nullable
- finishedAt nullable
- createdBy nullable

AnalysisResult:
- id UUID
- jobId
- title
- summary
- contentMarkdown
- sources JSON
- confidenceScore nullable
- status: DRAFT | REVIEW | APPROVED | REJECTED
- approvedAt nullable
- approvedBy nullable
- createdAt
- updatedAt

Anforderungen:
- Prisma Schema erweitern
- Migration erzeugen
- Indizes für status, createdAt, sourceType
- Repository Layer bauen
- Seed/Testdaten ergänzen
```

---

# Prompt 2.2 – AnalysisService implementieren

```text
Implementiere AnalysisService als produktiven Backend-Service.

Funktionen:

createAnalysisJob()
startAnalysisJob()
cancelAnalysisJob()
getAnalysisJob()
listAnalysisJobs()
retryAnalysisJob()
getAnalysisResult()
updateAnalysisResult()
approveAnalysisResult()
rejectAnalysisResult()

Anforderungen:
- Jobstatus strikt validieren
- Keine direkte Persistierung als Wissenseintrag ohne Approval
- Transaktionen nutzen
- Fehlerklassen verwenden
- Audit Logging
- Timeout je Provider
- Retry mit max. 2 Versuchen
- Quellenpflicht bei Dokumentbezug erzwingen

Tests:
- queued -> running -> completed
- queued -> cancelled
- running -> failed
- completed result editieren
- approve nur nach Useraktion
- reject
- retry failed
```

---

# Prompt 2.3 – Provider-Abstraktion für Analyse

```text
Erweitere das bestehende KI-Provider-Interface für Analysefunktionen.

Interface:

generateAnalysisSummary(input):
- sourceDocuments
- topicContext optional
- userPrompt optional
- outputFormat
- maxTokens
- language

Provider:
- Ollama
- OpenAI
- Gemini

Anforderungen:
- Einheitliche Response-Struktur
- Quellenreferenzen erhalten
- Tokenbegrenzung
- Timeout
- Retry
- Provider-Fehler normalisieren
- Keine Secrets im Log
- Privacy Mode berücksichtigen

Tests:
- Provider Mock
- Timeout
- Fehlerantwort
- leere Quellen
- ungültige Antwort
```

---

# Prompt 2.4 – Analyse API

```text
Implementiere REST API für Analyse-Jobs.

Endpoints:

GET /api/analysis/jobs
GET /api/analysis/jobs/:id
POST /api/analysis/jobs
POST /api/analysis/jobs/:id/start
POST /api/analysis/jobs/:id/cancel
POST /api/analysis/jobs/:id/retry

GET /api/analysis/results/:id
PUT /api/analysis/results/:id
POST /api/analysis/results/:id/approve
POST /api/analysis/results/:id/reject

Anforderungen:
- Zod Validation
- Pagination
- Statusfilter
- Response DTOs
- Error Middleware
- OpenAPI aktualisieren
- Contract Tests erstellen

Sicherheitsregel:
Approval darf ausschließlich über POST /approve erfolgen.
Kein Import, keine Topic-Aktualisierung und kein Wissenseintrag ohne explizite Approval-Aktion.
```

---

# Prompt 2.5 – AnalysisPage GUI

```text
Implementiere produktive AnalysisPage.

Bereiche:

1. Header
- Titel "Analyse"
- Neuer Analyse-Job
- Provider-Auswahl

2. Jobliste
- Status
- Quelle
- Provider
- Erstellt am
- Aktionen

3. Jobdetails
- Prompt
- Quellen
- Statusverlauf
- Fehlermeldung
- Retry
- Cancel

4. Ergebnisbereich
- Markdown-Ergebnis
- Quellen
- Confidence Score
- Bearbeiten
- Speichern
- Zur Freigabe markieren
- Freigeben
- Ablehnen

Anforderungen:
- Loading States
- Empty States
- Error States
- Responsive Layout
- Dark Mode
- Telekom Branding
- Keine technischen IDs sichtbar
```

---

# Prompt 2.6 – Neuer Analyse-Job Dialog

```text
Implementiere NewAnalysisJobDialog.

Schritte:

Step 1: Quelle wählen
- Dokumente
- Topic
- Suchergebnis

Step 2: Quellen auswählen
- Mehrfachauswahl Dokumente
- Topic-Auswahl
- Search Result Auswahl

Step 3: Prompt konfigurieren
- Standardprompt
- Benutzerprompt
- Detailgrad
- Sprache
- Ausgabeformat

Step 4: Provider wählen
- Ollama
- OpenAI
- Gemini
- Modell

Step 5: Vorschau und Start

Validierung:
- Mindestens eine Quelle
- Provider verfügbar
- Prompt nicht leer
- Max Token Limit

UX:
- Wizard
- Fortschritt
- Zurück/Weiter
- Start Analyse
```

---

# Prompt 2.7 – Approval-Sicherheit

```text
Implementiere harte Approval-Sicherheitsregeln.

Regeln:

1. KI-Ergebnisse bleiben DRAFT.
2. DRAFT darf nie automatisch in Wissensbestand übernommen werden.
3. REVIEW ist nur Benutzerentscheidung.
4. APPROVED nur über expliziten Confirm-Dialog.
5. Confirm-Dialog muss Zusammenfassung, Quellen und Änderungsdiff anzeigen.
6. Jede Approval-Aktion erzeugt Audit-Log.
7. Rejected Results bleiben nachvollziehbar.
8. Import in Topics/Documents nur nach APPROVED.

Tests:
- Kein Auto-Approve
- Kein Approve ohne Confirm Payload
- Kein Import bei Draft
- Kein Import bei Rejected
- Audit Log vorhanden
- Quellen vorhanden
```

---

# Prompt 2.8 – Analyse Ergebnis in Wissensbestand übernehmen

```text
Implementiere kontrollierte Übernahme genehmigter Analyse-Ergebnisse.

Funktionen:

importApprovedAnalysisToTopic()
createTopicFromApprovedAnalysis()
appendAnalysisToExistingTopic()
createDocumentFromApprovedAnalysis()

Regeln:
- Nur AnalysisResult.status = APPROVED
- Quellen müssen erhalten bleiben
- Ursprünglicher Analysejob bleibt referenziert
- Diff vor Import anzeigen
- Import erzeugt neuen Datensatz oder neue Version
- Kein Überschreiben ohne Versionierung

API:
POST /api/analysis/results/:id/import/topic
POST /api/analysis/results/:id/import/document

Tests:
- Approved Import erfolgreich
- Draft Import blockiert
- Quellen bleiben erhalten
- Version wird erzeugt
- Fehler rollback
```

---

# Prompt 2.9 – Analyse Gold Path Tests

```text
Erstelle vollständige Gold-Path-Tests für den Analysebereich.

Gold Path:

1. Dokumente auswählen
2. Analysejob erstellen
3. Job starten
4. Provider-Mock erzeugt Ergebnis
5. Ergebnis anzeigen
6. Ergebnis bearbeiten
7. Ergebnis zur Freigabe bringen
8. Confirm Dialog bestätigen
9. Ergebnis approve
10. Ergebnis in Topic übernehmen
11. Topic enthält Quellenreferenzen

Erzeuge Tests für:
- Backend Integration
- API Contract
- Frontend Component
- E2E Flow
- Error States
- Accessibility
- technische ID-Leaks

Output:
analysis_gold_path.json
analysis_security_report.json
analysis_coverage.json
```

---

# Prompt 2.10 – Dokumentation aktualisieren

```text
Aktualisiere nach Abschluss von PRI-2 alle Projektdokumentationen.

Dateien:

Masterplan.md
Entwicklung.md
masterplan_status.json
product_maturity_v3.json
product_gold_path.json
conditional_rc_decision.json
release_gate.json

Dokumentiere:

- Analysebereich produktiv umgesetzt
- Datenmodell
- API
- GUI
- Approval-Regeln
- Sicherheitsprüfungen
- Tests
- bekannte Limitationen
- neue Reifegradbewertung
- verbleibende RC-Blocker

Bewertung neu berechnen:
- GP-05
- GP-06
- Product Maturity
- RC-Status

Abschlussregel:
Wenn GP-05 und GP-06 PASS sind, PRI-3 Export Center als nächste Priorität setzen.
```

### 7. Benutzer

weiter

### 8. Assistent

# PRI-3 – Export Center inkl. PDF produktiv fertigstellen

Ziel: GP-07 schließen und Exportfähigkeit für Suche, Analyse und Themen herstellen.

---

# Prompt 3.1 – Export-Datenmodell

```text
Implementiere das vollständige Datenmodell für Export-Jobs.

Entities:

ExportJob:
- id UUID
- workspaceId nullable
- status: QUEUED | RUNNING | COMPLETED | FAILED | CANCELLED
- sourceType: SEARCH_RESULT | ANALYSIS_RESULT | TOPIC | DOCUMENT_COLLECTION
- sourceIds JSON
- exportFormat: MARKDOWN | JSON | PDF
- fileName
- filePath nullable
- errorMessage nullable
- createdBy nullable
- createdAt
- startedAt nullable
- finishedAt nullable

ExportTemplate:
- id UUID
- name
- format: MARKDOWN | JSON | PDF
- layoutConfig JSON
- isDefault boolean
- createdAt
- updatedAt

Anforderungen:
- Prisma Schema erweitern
- Migration erzeugen
- Repository Layer bauen
- Indizes auf status, format, createdAt
- Testdaten ergänzen
```

---

# Prompt 3.2 – ExportService

```text
Implementiere ExportService.

Funktionen:

createExportJob()
startExportJob()
cancelExportJob()
retryExportJob()
getExportJob()
listExportJobs()
downloadExportFile()
deleteExportFile()

Quellen:
- Search Results
- Analysis Results
- Topics
- Documents

Formate:
- Markdown
- JSON
- PDF

Regeln:
- Nur freigegebene Analyseergebnisse exportieren
- Quellenreferenzen erhalten
- Keine technischen IDs im Export
- Keine Secrets im Export
- Dateinamen normalisieren
- Exportpfad absichern
- Fehler rollbackfähig behandeln

Tests:
- Export Markdown
- Export JSON
- Export PDF
- ungültige Quelle
- Draft Analysis blockiert
- fehlende Datei
- Download nach Completed
```

---

# Prompt 3.3 – PDF Renderer

```text
Implementiere PDF-Rendering für Exporte.

Anforderungen:

PDF Struktur:
1. Deckblatt
2. Inhaltsverzeichnis
3. Zusammenfassung
4. Hauptinhalt
5. Quellen
6. Export-Metadaten ohne technische IDs

Branding:
- Telekom kompatibles Layout
- klare Typografie
- Kopf-/Fußzeilen
- Seitenzahlen
- Datum

Technik:
- Server-seitiges Rendering
- Markdown zu PDF
- Tabellen unterstützen
- Listen unterstützen
- lange Inhalte umbrechen
- Quellen sauber nummerieren

Sicherheit:
- HTML sanitizen
- keine externen Ressourcen laden
- keine Scripts
- keine technischen IDs
- keine Secrets

Tests:
- Snapshot PDF Metadaten
- Seitenzahl vorhanden
- Quellen vorhanden
- technische IDs nicht vorhanden
- ungültiges Markdown robust
```

---

# Prompt 3.4 – Export API

```text
Implementiere REST API für Export Center.

Endpoints:

GET /api/export/jobs
GET /api/export/jobs/:id
POST /api/export/jobs
POST /api/export/jobs/:id/start
POST /api/export/jobs/:id/cancel
POST /api/export/jobs/:id/retry
GET /api/export/jobs/:id/download
DELETE /api/export/jobs/:id/file

GET /api/export/templates
POST /api/export/templates
PUT /api/export/templates/:id
DELETE /api/export/templates/:id

Anforderungen:
- Zod Validation
- Pagination
- Statusfilter
- Formatfilter
- Response DTOs
- Contract Tests
- OpenAPI aktualisieren
- Error Middleware nutzen
```

---

# Prompt 3.5 – Export Center GUI

```text
Implementiere ExportCenterPage.

Bereiche:

1. Header
- Titel "Export Center"
- Neuer Export
- Formatfilter

2. Jobliste
- Status
- Quelle
- Format
- Dateiname
- Erstellt am
- Aktionen

3. Jobdetails
- Quelle
- Format
- Template
- Statusverlauf
- Fehler
- Download
- Retry
- Cancel
- Datei löschen

4. Templatebereich
- Templates anzeigen
- Template erstellen
- Template bearbeiten
- Standardtemplate setzen

Anforderungen:
- Loading States
- Empty States
- Error States
- Dark Mode
- Responsive Layout
- Telekom Branding
- Keine technischen IDs sichtbar
```

---

# Prompt 3.6 – Neuer Export Dialog

```text
Implementiere NewExportDialog.

Schritte:

Step 1: Quelle wählen
- Suchergebnis
- Analyseergebnis
- Topic
- Dokumentensammlung

Step 2: Quelle konkret auswählen
- Mehrfachauswahl wo sinnvoll
- Nur exportfähige Quellen anzeigen
- Draft Analysis Results ausblenden oder deaktivieren

Step 3: Format wählen
- Markdown
- JSON
- PDF

Step 4: Template wählen
- Standardtemplate vorauswählen
- Vorschau anzeigen

Step 5: Dateiname
- automatisch generieren
- manuell änderbar
- Validierung

Step 6: Start

Validierung:
- Quelle erforderlich
- Format erforderlich
- Dateiname gültig
- Template kompatibel
```

---

# Prompt 3.7 – Export Integration in Suche, Analyse und Themen

```text
Integriere Exportfunktionen in bestehende Produktbereiche.

Suche:
- Button "Exportieren"
- aktuelles Suchergebnis als Exportquelle übergeben
- Filterzustand speichern

Analyse:
- Button "Exportieren"
- nur APPROVED Results exportierbar
- DRAFT zeigt Hinweis mit Freigabeanforderung

Themen:
- Button "Topic exportieren"
- verknüpfte Dokumente optional einschließen
- Quellen immer einschließen

Dokumente:
- Mehrfachauswahl
- Sammlung exportieren

Anforderungen:
- Einheitliche Export-UX
- Routing ins Export Center
- Statusfeedback
- keine technischen IDs sichtbar
```

---

# Prompt 3.8 – Export Security Audit

```text
Implementiere vollständigen Export Security Audit.

Prüfungen:

1. Keine technischen IDs sichtbar
2. Keine Secrets in Exportdateien
3. Keine Draft-Analyse exportierbar
4. Keine Pfadmanipulation möglich
5. Keine externen Ressourcen im PDF
6. Keine Script-Ausführung
7. Quellenpflicht erfüllt
8. Download nur für Completed Jobs
9. Fehler werden ohne sensible Daten angezeigt

Outputs:
export_security_report.json
export_id_leak_audit.json
export_secret_scan.json

Tests:
- automatisiert
- CI-fähig
- Gate-relevant
```

---

# Prompt 3.9 – Export Gold Path Tests

```text
Erstelle vollständige Gold-Path-Tests für Export.

Gold Path:

1. Approved Analysis Result öffnen
2. Export starten
3. PDF als Format wählen
4. Template wählen
5. Job erstellen
6. Job starten
7. Job completed
8. PDF herunterladen
9. PDF enthält Inhalt
10. PDF enthält Quellen
11. PDF enthält keine technischen IDs
12. PDF enthält keine Secrets

Zusätzlich:
- Topic Markdown Export
- Search Result JSON Export
- Draft Analysis blockiert
- fehlgeschlagener Export Retry

Outputs:
export_gold_path.json
export_coverage.json
export_release_report.json
```

---

# Prompt 3.10 – Dokumentation aktualisieren

```text
Aktualisiere nach Abschluss von PRI-3 alle Projektdokumentationen.

Dateien:

Masterplan.md
Entwicklung.md
masterplan_status.json
product_maturity_v3.json
product_gold_path.json
conditional_rc_decision.json
release_gate.json

Dokumentiere:

- Export Center umgesetzt
- Markdown Export
- JSON Export
- PDF Export
- Templates
- Integration in Suche, Analyse, Themen und Dokumente
- Sicherheitsregeln
- Tests
- bekannte Limitationen
- neue Reifegradbewertung
- verbleibende RC-Blocker

Bewertung neu berechnen:
- GP-07
- Product Maturity
- RC-Status

Abschlussregel:
Wenn GP-07 PASS ist, PRI-4 Dashboard Drift Analytics als nächste Priorität setzen.
```

### 9. Benutzer

weiter

### 10. Benutzer

weiter

### 11. Assistent

# PRI-4 – Dashboard Drift Analytics fertigstellen

Ziel: Dashboard produktreif machen und Drift-/Qualitätsstatus sichtbar machen.

---

# Prompt 4.1 – Drift-Datenmodell

```text
Implementiere das Datenmodell für Drift Analytics.

Entities:

DriftSnapshot:
- id UUID
- workspaceId nullable
- snapshotType:
  PRODUCT_MATURITY
  GOLD_PATH
  RELEASE_GATE
  TEST_COVERAGE
  ID_LEAK_AUDIT
  SECURITY_AUDIT
- score nullable
- status:
  PASS
  WARNING
  FAIL
  BLOCKED
- payload JSON
- createdAt
- createdBy nullable

DriftMetric:
- id UUID
- snapshotId
- metricKey
- metricLabel
- metricValue
- metricUnit nullable
- thresholdWarning nullable
- thresholdFail nullable
- status
- createdAt

Anforderungen:
- Prisma Schema erweitern
- Migration erzeugen
- Repository Layer bauen
- Indizes auf snapshotType, status, createdAt
- Seed/Testdaten ergänzen
```

---

# Prompt 4.2 – DriftService

```text
Implementiere DriftService.

Funktionen:

createSnapshot()
getLatestSnapshot()
listSnapshots()
getSnapshotMetrics()
calculateProductMaturityDrift()
calculateGoldPathDrift()
calculateReleaseGateDrift()
calculateTestCoverageDrift()
calculateIdLeakDrift()
calculateSecurityDrift()

Regeln:
- Snapshots sind immutable
- Dashboard liest immer latest Snapshot je Typ
- Fehlende Daten ergeben WARNING, nicht PASS
- BLOCKED hat Vorrang vor FAIL
- FAIL hat Vorrang vor WARNING
- Thresholds zentral konfigurieren

Tests:
- latest Snapshot
- Statuspriorität
- Threshold WARNING
- Threshold FAIL
- fehlende Daten
- immutable Snapshot
```

---

# Prompt 4.3 – Drift API

```text
Implementiere REST API für Drift Analytics.

Endpoints:

GET /api/drift/overview
GET /api/drift/snapshots
GET /api/drift/snapshots/:id
GET /api/drift/snapshots/:id/metrics
POST /api/drift/snapshots/recalculate

Response /overview:
- productMaturity
- goldPath
- releaseGate
- testCoverage
- idLeakAudit
- securityAudit
- lastUpdated
- globalStatus

Anforderungen:
- Zod Validation
- Pagination
- Statusfilter
- Typefilter
- Response DTOs
- Contract Tests
- OpenAPI aktualisieren
```

---

# Prompt 4.4 – Dashboard Backend Aggregation

```text
Erweitere DashboardService um Drift-Daten.

Dashboard Overview muss liefern:

Bestehende Widgets:
- Dokumente
- Themen
- Analysejobs
- Exportjobs
- offene Reviews

Neue Drift Widgets:
- Product Maturity Score
- Gold Path Status
- Release Gate Status
- Test Coverage
- Technical ID Leak Status
- Security Status

Regeln:
- Keine technischen IDs in Response
- Fehlende Drift-Daten sichtbar als "Keine Daten"
- Status farblich klassifizierbar:
  PASS
  WARNING
  FAIL
  BLOCKED

Tests:
- vollständige Daten
- fehlende Drift-Daten
- BLOCKED Priorität
- technische IDs nicht enthalten
```

---

# Prompt 4.5 – Dashboard Drift Widgets GUI

```text
Implementiere Drift Widgets im Dashboard.

Widgets:

1. Product Maturity
- Score
- Zielwert RC
- Zielwert GA
- Status

2. Gold Path
- PASS / TOTAL
- fehlende Pfade
- Status

3. Release Gate
- Status
- Blocker
- Warnungen

4. Test Coverage
- Backend
- Frontend
- E2E

5. Technical ID Leak Audit
- Anzahl Leaks
- Status

6. Security Audit
- Blocker
- Warnungen
- Status

UX:
- Kartenlayout
- Status-Badges
- Tooltip mit Erklärung
- Klick führt zur Detailansicht
- Loading State
- Empty State
- Error State
- Dark Mode
- Telekom Branding
```

---

# Prompt 4.6 – Drift Detailseite

```text
Implementiere DriftDetailPage.

Bereiche:

1. Übersicht
- Snapshot-Typ
- Status
- Score
- Erzeugt am

2. Metriken
- Key
- Label
- Wert
- Einheit
- Threshold Warning
- Threshold Fail
- Status

3. Payload Ansicht
- lesbare JSON-Ansicht
- einklappbar
- keine technischen IDs anzeigen

4. Historie
- frühere Snapshots
- Score-Trend
- Statusverlauf

Anforderungen:
- Tabellenansicht
- Trenddiagramm
- Filter
- Sortierung
- keine technischen IDs sichtbar
```

---

# Prompt 4.7 – Recalculate Drift Workflow

```text
Implementiere Workflow "Drift neu berechnen".

Backend:
- POST /api/drift/snapshots/recalculate
- erzeugt neue Snapshots je Typ
- liest aktuelle Reports:
  masterplan_status.json
  product_maturity_v3.json
  product_gold_path.json
  release_gate.json
  security reports
  id leak reports

Frontend:
- Button "Neu berechnen"
- Confirm Dialog
- Fortschrittsanzeige
- Ergebnis anzeigen
- Dashboard refresh

Regeln:
- alte Snapshots bleiben erhalten
- Fehler je Snapshot isolieren
- Gesamtergebnis berechnen
- Audit Log schreiben

Tests:
- erfolgreiche Neuberechnung
- teilweise fehlende Reports
- fehlerhafte JSON-Datei
- Audit Log vorhanden
```

---

# Prompt 4.8 – Dashboard Gold Path Integration

```text
Integriere Gold Path Status in Dashboard und Navigation.

Anforderungen:

- Globaler Statusindikator in App Shell
- Anzeige:
  PASS
  WARNING
  FAIL
  BLOCKED

- Navigation markiert blockierte Bereiche:
  Themen
  Analyse
  Export
  Dashboard
  Suche
  Dokumente

- Klick auf Status öffnet Drift Detailseite
- Blocker werden kurz angezeigt
- keine technischen IDs
- keine internen Dateipfade sichtbar

Tests:
- Statusanzeige korrekt
- Navigation Badge korrekt
- BLOCKED priorisiert
- fehlende Daten = WARNING
```

---

# Prompt 4.9 – Drift Gold Path Tests

```text
Erstelle vollständige Gold-Path-Tests für Drift Analytics.

Gold Path:

1. Reports liegen vor
2. Recalculate Drift starten
3. Snapshots werden erzeugt
4. Dashboard zeigt Product Maturity
5. Dashboard zeigt Gold Path
6. Dashboard zeigt Release Gate
7. BLOCKED wird priorisiert
8. Detailseite zeigt Metriken
9. Historie bleibt erhalten
10. keine technischen IDs sichtbar

Outputs:
drift_gold_path.json
drift_coverage.json
dashboard_release_report.json
```

---

# Prompt 4.10 – Dokumentation aktualisieren

```text
Aktualisiere nach Abschluss von PRI-4 alle Projektdokumentationen.

Dateien:

Masterplan.md
Entwicklung.md
masterplan_status.json
product_maturity_v3.json
product_gold_path.json
conditional_rc_decision.json
release_gate.json

Dokumentiere:

- Drift Analytics umgesetzt
- Dashboard Widgets
- Drift Snapshots
- Drift API
- Recalculate Workflow
- Gold Path Integration
- technische ID Prüfung
- bekannte Limitationen
- neue Reifegradbewertung
- verbleibende RC-Blocker

Bewertung neu berechnen:
- Dashboard-Reife
- Drift-Reife
- Product Maturity
- RC-Status

Abschlussregel:
Wenn Dashboard Drift PASS ist, PRI-5 Release Hardening starten.
```

### 12. Benutzer

weiter

### 13. Assistent

# PRI-5 – Release Hardening, Gold Path und RC-Gate

Ziel: Anwendung von BLOCKED auf CONDITIONAL_RC oder RC_READY bringen.

---

# Prompt 5.1 – Release-Gate-Regeln finalisieren

```text
Finalisiere die Release-Gate-Regeln im Code und in der Dokumentation.

Gate-Stufen:

BLOCKED:
- Security FAIL
- technische ID-Leaks > 0
- Gold Path < 7/8
- Product Maturity < 80
- kritische Tests rot
- GP-06 FAIL

CONDITIONAL_RC:
- Security PASS oder WARNING ohne Blocker
- technische ID-Leaks = 0
- Gold Path >= 7/8
- Product Maturity >= 80
- bekannte Limitationen dokumentiert
- keine kritischen Tests rot

RC_READY:
- Gold Path 8/8
- Product Maturity >= 85
- Security PASS
- Export PDF PASS
- Dokumentation aktuell
- keine offenen Blocker

GA_READY:
- Product Maturity >= 90
- Gold Path 8/8 stabil
- E2E vollständig
- Performance akzeptiert
- Backup/Restore dokumentiert
- Betriebshandbuch vorhanden

Lieferung:
- release_gate_rules.ts
- release_gate_evaluator.ts
- Tests
- Doku
```

---

# Prompt 5.2 – Gold Path Matrix finalisieren

```text
Implementiere und dokumentiere die vollständige Gold Path Matrix.

Gold Paths:

GP-01 Login / Bereichsauswahl
GP-02 Dokument importieren
GP-03 Dokument suchen
GP-04 Themen finden und bearbeiten
GP-05 Analyse starten und Ergebnis anzeigen
GP-06 Analyse freigeben und übernehmen
GP-07 Export erzeugen
GP-08 Dashboard Status prüfen

Für jeden Gold Path dokumentieren:

- Ziel
- Nutzerrolle
- Vorbedingungen
- Schritte
- erwartetes Ergebnis
- API-Abhängigkeiten
- UI-Komponenten
- Testdateien
- Status
- Blocker
- Risiko

Output:
product_gold_path.json
gold_path_matrix.md
```

---

# Prompt 5.3 – End-to-End Tests stabilisieren

```text
Stabilisiere vollständige E2E-Testabdeckung.

Testumfang:

1. Import Flow
2. Suche Flow
3. Topics Flow
4. Analyse Flow
5. Approval Flow
6. Export Flow
7. Dashboard Flow
8. Error Flow

Anforderungen:
- Playwright Tests
- isolierte Testdaten
- deterministic provider mocks
- keine Live-Provider-Abhängigkeit
- keine echten Secrets
- TEST_DATABASE_URL verwenden
- DB Reset vor Tests
- Artefakte speichern:
  Screenshots
  Trace
  Video nur bei Fehler

Output:
e2e_report.json
gold_path_e2e_report.json
```

---

# Prompt 5.4 – Contract Tests vollständig machen

```text
Vervollständige API Contract Tests.

Bereiche:

- Documents
- Search
- Topics
- Analysis
- Export
- Dashboard
- Drift
- Auth/Bereichsauswahl
- Error Middleware

Anforderungen:
- OpenAPI gegen Implementierung prüfen
- Response DTOs validieren
- Error DTOs validieren
- Pagination prüfen
- Filter prüfen
- Edge Cases prüfen

Edge Cases:
- leere Daten
- ungültige IDs
- fehlende Quellen
- Draft-Status
- doppelte Anfrage
- abgebrochener Job
- fehlende Datei
- ungültige JSON-Reports

Output:
contract_test_report.json
api_coverage_report.json
```

---

# Prompt 5.5 – Security Hardening

```text
Führe Security Hardening vollständig durch.

Prüfbereiche:

1. Secret Handling
- keine Secrets in Logs
- keine Secrets in Exports
- keine Secrets in AI Context
- Secret Scanner CI-fähig

2. Privacy Mode
- require_not_privacy_mode() in:
  MemoryExtractor
  ConversationService
  FileImportService
  AnalysisService
  ExportService

3. DataClassification
- eingebaut in:
  MemoryExtractor
  FileImportService
  AnalysisService
  AuditLogger
  ExportService

4. Authorization
- workspace scope prüfen
- owner scope prüfen
- prepared multi-user structure erhalten

5. Input Security
- Zod Validation
- Markdown Sanitizing
- PDF HTML Sanitizing
- Path Traversal blockieren

6. Audit Logging
- Import
- Analyse
- Approval
- Export
- Delete
- Archive

Output:
security_hardening_report.json
privacy_mode_report.json
data_classification_report.json
secret_scan_report.json
```

---

# Prompt 5.6 – Technische-ID-Leak Gate absichern

```text
Implementiere ein dauerhaftes Technical-ID-Leak Gate.

Regel:
Keine technischen IDs in sichtbarer UI, Exporten oder Reports.

Prüfen auf:
- document.id
- workspaceId
- ownerUserId
- userId
- jobId
- analysisId
- exportId
- topicId
- uuid
- interne Dateipfade
- Prisma IDs
- raw database IDs

Bereiche:
- Frontend DOM
- API Response DTOs für UI
- Exporte
- PDF
- Dashboard
- Drift Detailseite
- Error States

Ergebnis:
technical_id_leak_gate.json

Tests:
- automatisiert
- CI-fähig
- FAIL bei Leak
```

---

# Prompt 5.7 – Performance Baseline

```text
Erstelle Performance Baseline für RC.

Messpunkte:

Backend:
- GET /api/documents
- GET /api/search
- GET /api/topics
- POST /api/analysis/jobs
- POST /api/export/jobs
- GET /api/dashboard/overview

Frontend:
- Dashboard First Load
- Dokumentliste
- Suche
- Topic Detail
- AnalysisPage
- ExportCenter

Grenzwerte RC:
- API p95 < 800 ms bei Testdaten
- Frontend initial load < 3 s lokal
- Suchantwort < 1,5 s
- PDF Export < 10 s bei 20 Seiten
- keine Memory Leaks im Smoke Test

Output:
performance_baseline_report.json
performance_risks.md
```

---

# Prompt 5.8 – Operational Readiness

```text
Erstelle Operational Readiness für RC.

Lieferung:

1. .env.example vollständig
2. docker-compose.yml validiert
3. Migration Runbook
4. Backup Runbook
5. Restore Runbook
6. Troubleshooting Guide
7. Healthcheck Matrix
8. Logging-Konzept
9. Provider-Konfiguration
10. Testdaten-Setup

Dateien:
docs/operations/runbook.md
docs/operations/backup_restore.md
docs/operations/troubleshooting.md
docs/operations/healthchecks.md
.env.example
```

---

# Prompt 5.9 – RC Final Gate

```text
Führe RC Final Gate aus.

Prüfen:

1. Unit Tests
2. Integration Tests
3. Contract Tests
4. E2E Gold Path
5. Security Reports
6. Technical ID Leak Gate
7. Product Maturity
8. Release Gate
9. Performance Baseline
10. Dokumentation

Erzeuge:

rc_final_gate_report.json
rc_decision.md
product_maturity_v3.json
product_gold_path.json
release_gate.json
masterplan_status.json

Bewertung:

- BLOCKED
- CONDITIONAL_RC
- RC_READY

Dokumentiere:
- Ergebnis
- Blocker
- Warnings
- Limitationen
- nächste Schritte
```

---

# Prompt 5.10 – Dokumentation aktualisieren

```text
Aktualisiere nach Abschluss von PRI-5 alle Projektdokumentationen.

Dateien:

Masterplan.md
Entwicklung.md
README.md
docs/operations/runbook.md
docs/operations/backup_restore.md
docs/operations/troubleshooting.md
docs/operations/healthchecks.md
masterplan_status.json
product_maturity_v3.json
product_gold_path.json
release_gate.json
conditional_rc_decision.json
rc_decision.md

Dokumentiere:

- Release-Hardening abgeschlossen
- Gold Path Matrix
- Security Hardening
- Privacy Mode
- DataClassification
- Technical ID Leak Gate
- Performance Baseline
- Operational Readiness
- RC Final Gate
- bekannte Limitationen
- verbleibende GA-Punkte

Abschlussregel:

Wenn Status = CONDITIONAL_RC:
- RC-Limitationen klar dokumentieren
- GA-Backlog erzeugen

Wenn Status = RC_READY:
- GA-Vorbereitung starten

Wenn Status = BLOCKED:
- Blocker priorisieren und PRI-6 erstellen
```

### 14. Benutzer

weiter

### 15. Assistent

# PRI-6 – Blocker-Beseitigung nach RC Final Gate

Ziel: Alle verbleibenden BLOCKED- oder WARNING-Befunde aus PRI-5 schließen und auf mindestens CONDITIONAL_RC heben.

---

# Prompt 6.1 – RC Gate Report auswerten

```text
Analysiere die aktuellen Gate-Reports und leite daraus eine priorisierte Blocker-Matrix ab.

Einlesen:

- rc_final_gate_report.json
- rc_decision.md
- release_gate.json
- product_gold_path.json
- product_maturity_v3.json
- security_hardening_report.json
- technical_id_leak_gate.json
- performance_baseline_report.json
- contract_test_report.json
- e2e_report.json

Erzeuge:

blocking_matrix.json
blocking_matrix.md

Struktur je Blocker:

- ID
- Kategorie
- Schweregrad
- betroffener Gold Path
- betroffene Komponente
- Ursache
- Impact
- Fix-Aufwand
- Risiko bei Nichtbehebung
- empfohlene Reihenfolge
```

---

# Prompt 6.2 – Critical Blocker zuerst beheben

```text
Behebe alle Critical Blocker aus blocking_matrix.json.

Regeln:

1. Security vor Funktion.
2. Datenverlust vor UX.
3. GP-06 vor GP-07.
4. Technical-ID-Leaks vor Dashboard-Polish.
5. Contract-Brüche vor E2E-Stabilisierung.

Vorgehen je Blocker:

- Ursache lokalisieren
- minimalinvasiven Fix implementieren
- Regressionstest ergänzen
- betroffenen Gold Path erneut testen
- Report aktualisieren

Outputs:

critical_blocker_fix_report.json
critical_blocker_fix_report.md
```

---

# Prompt 6.3 – Warning-Befunde konsolidieren

```text
Analysiere alle WARNING-Befunde aus den Release-Reports.

Ziel:
Warnings entweder beheben oder als RC-Limitation dokumentieren.

Kriterien:

Beheben:
- beeinflusst User-Gold-Path
- betrifft Security
- betrifft Datenintegrität
- erzeugt Supportaufwand
- blockiert GA

Als Limitation dokumentieren:
- kein RC-User-Impact
- kein Security-Risiko
- kein Datenverlust
- klarer Workaround vorhanden
- GA-Ticket angelegt

Erzeuge:

warning_disposition_report.json
rc_limitations.md
ga_backlog.md
```

---

# Prompt 6.4 – Gold Path Re-Run

```text
Führe nach Blocker-Fixes alle Gold Paths erneut aus.

Gold Paths:

GP-01 Login / Bereichsauswahl
GP-02 Dokument importieren
GP-03 Dokument suchen
GP-04 Themen finden und bearbeiten
GP-05 Analyse starten und Ergebnis anzeigen
GP-06 Analyse freigeben und übernehmen
GP-07 Export erzeugen
GP-08 Dashboard Status prüfen

Erwartung:
- mindestens 7/8 PASS für CONDITIONAL_RC
- 8/8 PASS für RC_READY

Outputs:

product_gold_path.json
gold_path_rerun_report.json
gold_path_evidence.md

Bei FAIL:
- Screenshot/Trace referenzieren
- Ursache dokumentieren
- Blocker-ID erzeugen
```

---

# Prompt 6.5 – Product Maturity neu berechnen

```text
Berechne Product Maturity nach Blocker-Fixes neu.

Bewertungsbereiche:

- Dokumente
- Suche
- Themen
- Analyse
- Approval
- Export
- Dashboard
- Security
- Tests
- Betrieb
- Dokumentation

Regeln:

RC:
- Score >= 80

GA:
- Score >= 85

Output:

product_maturity_v3.json
product_maturity_delta.md

Dokumentiere:
- alter Score
- neuer Score
- Veränderung je Bereich
- verbleibende Schwächen
- Hebel für nächste +5 Punkte
```

---

# Prompt 6.6 – Conditional RC Decision

```text
Erzeuge neue Conditional-RC-Entscheidung.

Eingaben:

- product_gold_path.json
- product_maturity_v3.json
- release_gate.json
- security_hardening_report.json
- technical_id_leak_gate.json
- warning_disposition_report.json
- rc_limitations.md

Entscheidungslogik:

CONDITIONAL_RC, wenn:
- Gold Path >= 7/8 PASS
- Product Maturity >= 80
- Security keine Blocker
- Technical-ID-Leaks = 0
- GP-06 PASS
- alle Limitationen dokumentiert

RC_READY, wenn zusätzlich:
- Gold Path 8/8 PASS
- Product Maturity >= 85
- PDF Export PASS
- Performance Baseline PASS
- Operational Readiness PASS

BLOCKED sonst.

Output:

conditional_rc_decision.json
rc_decision.md
```

---

# Prompt 6.7 – GA Backlog erzeugen

```text
Erzeuge strukturierten GA-Backlog aus allen verbleibenden Limitationen.

Backlog-Kategorien:

1. Produktfunktion
2. UX
3. Security
4. Performance
5. Betrieb
6. Tests
7. Dokumentation
8. Skalierung

Je Backlog Item:

- ID
- Titel
- Beschreibung
- Kategorie
- betroffene Komponente
- betroffener Gold Path
- Priorität
- Aufwand
- Akzeptanzkriterien
- Risiko bei Verschiebung
- Abhängigkeiten

Output:

ga_backlog.md
ga_backlog.json
```

---

# Prompt 6.8 – RC Release Notes

```text
Erstelle RC Release Notes.

Inhalt:

1. Release Status
2. Implementierte Hauptfunktionen
3. Gold Path Ergebnis
4. Security Status
5. Bekannte Limitationen
6. Workarounds
7. Nicht enthaltene GA-Funktionen
8. Teststatus
9. Betriebsanforderungen
10. Upgrade-/Migrationshinweise

Output:

release_notes_rc.md
```

---

# Prompt 6.9 – Dokumentation aktualisieren

```text
Aktualisiere nach Abschluss von PRI-6 alle Projektdokumentationen.

Dateien:

Masterplan.md
Entwicklung.md
README.md
docs/operations/runbook.md
docs/operations/troubleshooting.md
docs/operations/healthchecks.md
masterplan_status.json
product_maturity_v3.json
product_gold_path.json
release_gate.json
conditional_rc_decision.json
rc_decision.md
ga_backlog.md
release_notes_rc.md

Dokumentiere:

- beseitigte Blocker
- verbleibende Warnings
- RC-Limitationen
- GA-Backlog
- neue Gate-Bewertung
- Release-Entscheidung

Abschlussregel:

Wenn Status = CONDITIONAL_RC:
- PRI-7 GA-Vorbereitung starten

Wenn Status = RC_READY:
- PRI-7 GA-Hardening starten

Wenn Status = BLOCKED:
- neue Blocker-Matrix erzeugen und PRI-6 wiederholen
```

---

# Prompt 6.10 – Abschlussprüfung PRI-6

```text
Führe Abschlussprüfung für PRI-6 aus.

Prüfen:

- blocking_matrix.json vorhanden
- alle Critical Blocker geschlossen
- warning_disposition_report.json vorhanden
- Gold Path Re-Run durchgeführt
- Product Maturity neu berechnet
- Conditional RC Decision erzeugt
- GA Backlog vorhanden
- RC Release Notes vorhanden
- Dokumentation aktualisiert

Erzeuge:

pri6_completion_report.json

Bewertung:

PASS:
- CONDITIONAL_RC oder RC_READY erreicht

FAIL:
- BLOCKED bleibt bestehen

Dokumentiere bei FAIL:
- verbleibende Blocker
- Ursache
- nächster Fix-Prompt
```

### 16. Assistent

# PRI-7 – GA-Hardening und Produktionsfreigabe

Ziel: Von `CONDITIONAL_RC` oder `RC_READY` auf `GA_READY` mit Produktreife ≥ 90.

---

# Prompt 7.1 – Architekturreview und Technical Debt

```text
Führe ein vollständiges Architekturreview durch.

Bereiche:

- Frontend Architektur
- Backend Architektur
- Datenmodell
- API Design
- Provider Integration
- Export Pipeline
- Analyse Pipeline
- Dashboard
- Testarchitektur
- Dokumentation

Identifiziere:

- Duplicate Code
- Zyklische Abhängigkeiten
- God Services
- Große Komponenten
- Fehlende Abstraktionen
- Veraltete Interfaces
- Performance-Risiken
- Skalierungsrisiken

Erzeuge:

architecture_review.md
technical_debt_register.json
technical_debt_register.md

Je Eintrag:

- ID
- Beschreibung
- Kategorie
- Aufwand
- Risiko
- Priorität
- Empfohlene Lösung
```

---

# Prompt 7.2 – Skalierbarkeit vorbereiten

```text
Bereite die Anwendung auf größere Datenmengen vor.

Bereiche:

Documents
Topics
Search
Analysis
Export
Dashboard

Implementiere:

- Cursor Pagination
- Query Limits
- Lazy Loading
- Server Side Pagination
- Query Optimierung
- N+1 Analyse
- Indizes prüfen
- Response Caching
- Hintergrundjobs optimieren

Erzeuge:

scalability_report.json
query_optimization_report.md
```

---

# Prompt 7.3 – Hintergrundjobs konsolidieren

```text
Analysiere sämtliche Hintergrundprozesse.

Jobs:

- Import
- Analyse
- Export
- Drift Recalculation
- Indexierung
- Synchronisation

Implementiere:

- einheitliches Job Interface
- Retry Strategie
- Timeout Strategie
- Dead Letter Queue
- Progress Events
- Cancellation
- Job Cleanup
- Status Historie

Erzeuge:

job_framework_report.json
job_state_machine.md
```

---

# Prompt 7.4 – Backup und Restore vollständig testen

```text
Implementiere vollständige Backup- und Restore-Tests.

Sichern:

- Datenbank
- Uploads
- Exporte
- Reports
- Konfiguration

Tests:

1. Full Backup
2. Incremental Backup
3. Restore Empty System
4. Restore Existing System
5. Restore nach Fehler
6. Datenintegrität prüfen

Erzeuge:

backup_report.json
restore_report.json
backup_restore_test_report.md
```

---

# Prompt 7.5 – Monitoring und Observability

```text
Implementiere produktionsfähiges Monitoring.

Metriken:

System:
- CPU
- RAM
- Disk

Application:
- Requests
- Fehler
- Jobs
- Provider
- Exporte
- Analysen

Business:
- Dokumente
- Themen
- Suchanfragen
- Exporte
- Reviews

Implementiere:

- strukturierte Logs
- Error Tracking
- Health Checks
- Metrics Endpoint
- Dashboard Metrics

Erzeuge:

observability_report.json
metrics_catalog.md
health_matrix.md
```

---

# Prompt 7.6 – Multi-User Vorbereitung abschließen

```text
Finalisiere die vorbereitete Multi-User-Architektur.

Prüfen:

- owner scope
- workspace scope
- Repository Filter
- DTOs
- Services
- Audit Logs
- Exporte
- Analysejobs

Implementiere:

- UserContext Service
- WorkspaceContext Service
- Scope Middleware
- Ownership Validation

Noch keine Loginpflicht.

Erzeuge:

multi_user_readiness_report.json
workspace_architecture.md
```

---

# Prompt 7.7 – Betriebshandbuch erzeugen

```text
Erstelle vollständige Betriebsdokumentation.

Kapitel:

1. Systemübersicht
2. Architektur
3. Deployment
4. Migration
5. Backup
6. Restore
7. Fehleranalyse
8. Monitoring
9. Logs
10. Provider Konfiguration
11. Updates
12. Rollback
13. Testbetrieb
14. Releaseprozess

Dateien:

docs/operations/
- operations_manual.md
- deployment.md
- rollback.md
- maintenance.md
```

---

# Prompt 7.8 – GA Regression Suite

```text
Erstelle vollständige GA Regression Suite.

Bereiche:

- Documents
- Search
- Topics
- Analysis
- Approval
- Export
- Dashboard
- Drift
- Reports
- Jobs

Tests:

- Unit
- Integration
- Contract
- E2E
- Performance
- Security
- Accessibility

Erzeuge:

ga_regression_report.json
ga_test_matrix.md
```

---

# Prompt 7.9 – GA Final Gate

```text
Führe vollständiges GA Final Gate aus.

Prüfen:

- Gold Path 8/8
- Product Maturity >= 90
- Security PASS
- Technical ID Leaks = 0
- Performance PASS
- Backup PASS
- Restore PASS
- Monitoring PASS
- Operations Documentation PASS
- Regression Suite PASS

Erzeuge:

ga_final_gate_report.json
ga_decision.md
release_gate.json
product_maturity_v3.json
product_gold_path.json
masterplan_status.json

Status:

- GA_READY
- BLOCKED
```

---

# Prompt 7.10 – Dokumentation aktualisieren

```text
Aktualisiere sämtliche Projektdokumentationen.

Dateien:

Masterplan.md
Entwicklung.md
README.md
docs/operations/*
masterplan_status.json
product_maturity_v3.json
product_gold_path.json
release_gate.json
ga_final_gate_report.json
ga_decision.md

Dokumentiere:

- Technical Debt Status
- Skalierungsstatus
- Monitoring
- Backup/Restore
- Multi-User Readiness
- Betriebsdokumentation
- Regression Suite
- GA Final Gate
- finale Produktreife
- verbleibende Risiken

Abschlussregel:

Wenn Status = GA_READY:
- Version 1.0 markieren
- Release Tag v1.0 vorbereiten
- CHANGELOG.md erzeugen
- Installationsanleitung finalisieren

Wenn Status = BLOCKED:
- PRI-8 Blockerbehebung erzeugen
```

---

# PRI-8 – Post-GA Roadmap (v1.1 / v2.0)

Erst nach `GA_READY`.

Epics:

1. Authentifizierung aktivieren
2. Rollen- und Berechtigungssystem
3. Echte Mehrbenutzerfähigkeit
4. Dokumentversionierung erweitern
5. Wissensgraph mit Neo4j
6. Agentische KI-Workflows
7. Automatische Wissensextraktion
8. Mobile PWA
9. Benachrichtigungen
10. Plugin-System
11. API Keys und Webhooks
12. Reporting und BI-Dashboard
13. Mandantenfähigkeit
14. Offline-Modus
15. KI-gestützte Wissenspflege
16. Fine-Grained Sharing und Freigaben
17. Semantic Memory und Langzeitkontext
18. Betriebsmetriken und Self-Healing Jobs

Nach jedem Paket obligatorisch:

```text
1. Masterplan.md aktualisieren
2. Entwicklung.md aktualisieren
3. CHANGELOG.md aktualisieren
4. product_maturity_v3.json neu berechnen
5. product_gold_path.json neu berechnen
6. release_gate.json aktualisieren
7. bekannte Risiken dokumentieren
8. nächste Prioritäten einplanen
```

### 17. Benutzer

weiter

### 18. Benutzer

PRI-7 abgeschlossen. Alle 26 Deliverables erzeugt, GA Final Gate ausgeführt.
Ergebnis: BLOCKED → PRI-8 Blockerbehebung
GA Final Gate-Kriterien (10 geprüft):

3× PASS: Gold Path 8/8, ID-Leaks=0, Operations Doku
4× FAIL: Maturity 68.7/100 (< 90), CSP fehlt, GIN-Index fehlt, Monitoring fehlt
3× BLOCKED: Backup-Tests, Restore-Tests, Regression Suite (alle wegen SCGB-01)

PRI-8 Backlog (docs/pri8_backlog.md) enthält 6 Blocker mit Code-Snippets und Priorisierung. Alle 4 internen Blocker (GIN-Index S, CSP S, Prometheus M, Integrations-Tests M) sind in einem Sprint behebbar. Maturity-Prognose nach PRI-8: ~85.8 — GA_READY erreichbar.

### 19. Assistent

# PRI-8 – GA Blockerbehebung

Ziel: Von `BLOCKED` auf `GA_READY`.

Ausgangslage:

| Kriterium | Status | Priorität |
|-----------|---------|------------|
| Gold Path 8/8 | PASS | - |
| Technical ID Leaks | PASS | - |
| Operations Docs | PASS | - |
| Product Maturity 68.7 | FAIL | Kritisch |
| CSP fehlt | FAIL | Kritisch |
| GIN-Index fehlt | FAIL | Kritisch |
| Monitoring fehlt | FAIL | Hoch |
| Backup Tests | BLOCKED | Hoch |
| Restore Tests | BLOCKED | Hoch |
| Regression Suite | BLOCKED | Hoch |

Ziel nach Sprint:

- Product Maturity ≥ 85
- Alle BLOCKED auf PASS
- Security PASS
- Performance PASS
- Monitoring PASS
- Backup PASS
- Restore PASS
- Regression PASS
- GA Final Gate erneut ausführen

---

# Sprint 8.1 – PostgreSQL GIN-Indizes

```text
Analysiere sämtliche Suchabfragen und fehlenden Datenbank-Indizes.

Implementiere:

Documents:
- tags
- metadata
- fulltext search

Topics:
- title
- summary
- tags

Analysis:
- contentMarkdown
- sources

Export:
- filename
- sourceType

Verwende:

GIN:
- tsvector
- jsonb
- arrays

Implementiere:

Prisma Migration
Alembic Migration falls vorhanden
Index Naming Convention
Rollback Migration

Erzeuge:

database_index_report.json
query_plan_before.md
query_plan_after.md

Tests:

EXPLAIN ANALYZE
Benchmark:
10k
50k
100k Datensätze
```

---

# Sprint 8.2 – Content Security Policy

```text
Implementiere vollständige Content Security Policy.

Anforderungen:

default-src 'self'

script-src:
'self'

style-src:
'self'
'unsafe-inline'

img-src:
'self'
data:
blob:

font-src:
'self'

connect-src:
'self'
Ollama Endpoint
OpenAI API
Gemini API

frame-src:
'none'

object-src:
'none'

base-uri:
'self'

frame-ancestors:
'none'

form-action:
'self'

upgrade-insecure-requests

Zusätzlich:

X-Content-Type-Options
Referrer-Policy
Permissions-Policy
X-Frame-Options

Implementiere:

Express/Fastify Middleware
Helmet Konfiguration
Development Override
Production Override

Tests:

CSP Header vorhanden
Inline Script Block
External Script Block
Iframe Block

Erzeuge:

csp_report.json
security_header_report.json
```

---

# Sprint 8.3 – Prometheus Monitoring

```text
Implementiere produktionsfähiges Monitoring.

Metrics Endpoint:

GET /metrics

Systemmetriken:

CPU
RAM
Heap
GC
Event Loop
Uptime

HTTP:

Request Count
Response Time
Error Count
Status Codes

Business:

Document Count
Topic Count
Analysis Jobs
Export Jobs
Open Reviews

Provider:

Provider Requests
Provider Errors
Provider Duration

Jobsystem:

Running Jobs
Failed Jobs
Queue Length
Retry Count

Implementiere:

prom-client
Structured Metrics
Labels
Histogramme
Counter
Gauge

Erzeuge:

monitoring_report.json
metrics_catalog.md
```

---

# Sprint 8.4 – Health Checks

```text
Erweitere Health Checks.

Endpoint:

GET /health

Bereiche:

Database
Provider
Filesystem
Metrics
Job Queue
Reports
Storage

Status:

UP
DEGRADED
DOWN

Response:

status
components
version
uptime
timestamp

Tests:

Service unavailable
Provider timeout
Storage readonly
Metrics unavailable

Erzeuge:

health_report.json
health_matrix.md
```

---

# Sprint 8.5 – Backup Integration Tests

```text
Implementiere vollständige Backup Tests.

Szenarien:

Test 1:
Leeres System sichern

Test 2:
Befülltes System sichern

Test 3:
Große Datenmenge

Test 4:
Fehlerhafte Konfiguration

Test 5:
Abbruch während Backup

Prüfen:

Database
Exports
Reports
Configuration

Assertions:

Dateien vorhanden
Checksummen korrekt
Manifest korrekt

Erzeuge:

backup_integration_report.json
backup_evidence.md
```

---

# Sprint 8.6 – Restore Integration Tests

```text
Implementiere vollständige Restore Tests.

Szenarien:

Restore:
Empty System

Restore:
Existing System

Restore:
Corrupted Backup

Restore:
Partial Backup

Prüfen:

Datenintegrität
Referenzen
Reports
Exporte
Konfiguration

Assertions:

Checksummen
Datensätze
Indizes
Reports

Erzeuge:

restore_integration_report.json
restore_evidence.md
```

---

# Sprint 8.7 – Regression Suite entsperren

```text
Entkopple Regression Suite von SCGB-01.

Vorgehen:

1.
Identifiziere harte Abhängigkeiten.

2.
Mocke:

Provider
Filesystem
Metrics
Backup
Restore

3.
Führe Regression isoliert aus.

Bereiche:

Documents
Search
Topics
Analysis
Approval
Export
Dashboard
Drift

Artefakte:

Screenshots
Traces
Coverage
Error Reports

Erzeuge:

ga_regression_report.json
ga_regression_evidence.md
```

---

# Sprint 8.8 – Product Maturity erhöhen

```text
Berechne neue Product Maturity.

Bereiche:

Security
Monitoring
Operations
Performance
Backup
Restore
Regression

Erzeuge:

product_maturity_v3.json
product_maturity_delta.md

Erwartung:

Vorher:
68.7

Nachher:
>=85

Dokumentiere:

Delta pro Bereich
Verbleibende Schwächen
GA-Risiken
```

---

# Sprint 8.9 – GA Final Gate erneut ausführen

```text
Führe vollständiges GA Final Gate erneut aus.

Prüfen:

Gold Path 8/8
Technical ID Leaks = 0
Operations PASS
Security PASS
GIN Index PASS
CSP PASS
Monitoring PASS
Backup PASS
Restore PASS
Regression PASS
Product Maturity >=85

Erzeuge:

ga_final_gate_report.json
ga_decision.md
release_gate.json
product_maturity_v3.json
product_gold_path.json
masterplan_status.json

Status:

GA_READY
oder
BLOCKED
```

---

# Sprint 8.10 – Dokumentation aktualisieren

```text
Aktualisiere:

Masterplan.md
Entwicklung.md
README.md
CHANGELOG.md
docs/operations/*
masterplan_status.json
product_maturity_v3.json
product_gold_path.json
release_gate.json
ga_final_gate_report.json
ga_decision.md

Dokumentiere:

- GIN-Indizes implementiert
- CSP implementiert
- Monitoring implementiert
- Backup Tests abgeschlossen
- Restore Tests abgeschlossen
- Regression Suite freigegeben
- neue Product Maturity
- finale Gate-Entscheidung
- verbleibende Risiken
- nächste Roadmap v1.1
```

---

# Empfehlung zur tatsächlichen Umsetzung

Auf Basis des bisherigen Projektverlaufs ist die effektivste Reihenfolge:

1. Sprint 8.2 – CSP (ca. 1 h)
2. Sprint 8.1 – GIN-Indizes (ca. 2–3 h)
3. Sprint 8.3 – Prometheus (ca. 2 h)
4. Sprint 8.4 – Health Checks (ca. 1 h)
5. Sprint 8.5 – Backup Tests (ca. 2 h)
6. Sprint 8.6 – Restore Tests (ca. 2 h)
7. Sprint 8.7 – Regression Suite (ca. 2–3 h)
8. Sprint 8.8–8.10 – Gates und Dokumentation (ca. 1 h)

Gesamtschätzung: ca. 12–15 Stunden Entwicklungsaufwand für eine realistische Chance auf `GA_READY`.
