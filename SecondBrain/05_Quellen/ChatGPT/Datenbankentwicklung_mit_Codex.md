---
title: "Datenbankentwicklung mit Codex"
type: chatgpt_conversation
source: chatgpt
source_id: "69f1f03e-aab0-838d-bc69-58767eebb9b7"
created: 2026-04-29
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
  - verein
---


# Datenbankentwicklung mit Codex

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69f1f03e-aab0-838d-bc69-58767eebb9b7`
- Nachrichten: 12

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

verwende für die entwicklung der neuen Datenbank (DB) den masterplan und das entwicklungs dokument. Promprt werden im mit bezeichnung des tool welches verwendet wird erstellt. Tools Claude Cowork und codex. die gui wird mit claude studio erstellt. liefere die prompts schritt für schritt. beachte tokensparrend zu entwickeln

### 2. Assistent

Nach Masterplan und Entwicklungsplan ist die Reihenfolge: Backend-Datenbasis zuerst, dann Bereichskontext, danach KI/Import/Review/Suche/Export/GUI. MVP-Kern: Import, Analyse, Freigabe, Suche, Themen-Merge, PDF-Export, Dashboard, Einstellungen, Bereichsfilter. fileciteturn0file1L3-L25 Entwicklung folgt den Phasen 0–12. fileciteturn0file0L3-L99

## Prompt 1 — Codex — Projektbasis

```text
Tool: Codex

Erstelle die technische Basis für die Wissensdatenbank MVP.

Kontext:
- Monorepo
- Frontend: React + Vite
- Backend: Express
- Persistenz vorbereiten
- Health API
- Storage-Struktur
- Basisrouting

Anforderungen:
1. Lege folgende Struktur an:
   /apps/web
   /apps/api
   /packages/shared
   /storage/imports
   /storage/markdown
   /storage/exports
2. Backend:
   - Express Server
   - GET /health
   - Fehler-Middleware
   - JSON Middleware
   - CORS lokal
3. Frontend:
   - React/Vite App
   - Routing vorbereiten
   - Seiten: Dashboard, Import, Analyse, Themen, Suche, Einstellungen
4. Shared:
   - gemeinsame Types vorbereiten
5. Keine Businesslogik implementieren.
6. Keine KI-Integration implementieren.
7. Token sparend arbeiten:
   - nur notwendige Dateien ändern
   - keine langen Erklärtexte
   - kurze Commits/Änderungen
   - erst lauffähige Basis, dann Erweiterung

Lieferung:
- Dateiliste
- geänderte Dateien
- Startbefehle
- kurzer Testnachweis
```

## Prompt 2 — Codex — Datenmodell

```text
Tool: Codex

Implementiere das SQL-Datenmodell für die Wissensdatenbank MVP.

Tabellen:
areas, users, knowledge_items, knowledge_versions, knowledge_tags, tags,
knowledge_area_permissions, import_jobs, import_items, analysis_items,
analysis_matches, topic_merge_jobs, topic_merge_sources, knowledge_chunks,
search_queries, search_results_log, pdf_exports, user_settings,
ai_settings, ai_provider_config, audit_logs.

Regeln:
1. Nutze Migrationen.
2. Nutze UUIDs.
3. Ergänze created_at, updated_at, created_by wo sinnvoll.
4. Ergänze Statusfelder für Import, Analyse, Review, Export.
5. knowledge_items müssen Bereich, Titel, Beschreibung, Summary, Markdown-Pfad, Vertraulichkeit, Dokumenttyp und Quelle speichern.
6. Tags zentral normalisieren.
7. Audit-Logs müssen Entity-Typ, Entity-ID, Aktion, Actor und Payload speichern.
8. Keine UI bauen.
9. Keine KI-Calls bauen.
10. Token sparend: nur Schema, Migrationen, DB-Adapter, minimale Tests.

Lieferung:
- Migrationen
- DB-Adapter
- Seed für Default-Bereich
- Test für Migration
```

## Prompt 3 — Codex — Bereichskontext

```text
Tool: Codex

Implementiere MVP-Bereichskontext ohne Login.

Anforderungen:
1. Backend:
   - X-Area-Id Header auslesen
   - Request Context erstellen
   - Serverseitige Filterung nach area_id
   - Fehler bei fehlendem oder ungültigem Bereich
2. Frontend:
   - Bereichsauswahl per Button
   - current_area_id in localStorage
   - API Client sendet X-Area-Id Header
3. Daten:
   - Default-Bereiche seedbar
4. Tests:
   - Request ohne Bereich wird abgelehnt
   - Request mit Bereich wird akzeptiert
   - Daten anderer Bereiche werden nicht geliefert

Nicht bauen:
- Login
- Rollenmodell
- komplexe Rechteverwaltung

Tokenregel:
- Middleware isoliert halten
- keine Seiteneffekte in Controllern
```

## Prompt 4 — Codex — KI-Einstellungen

```text
Tool: Codex

Implementiere KI- und Theme-Einstellungen.

Scope:
1. Light/Dark Mode im Frontend.
2. ai_settings und ai_provider_config CRUD im Backend.
3. Provider:
   - Ollama aktiv implementieren
   - OpenAI, Gemini, Custom nur als Platzhalter-Konfiguration
4. Verbindungstest:
   - POST /api/settings/ai/test
   - Ollama Health/Model-Test
5. Keine Analysepipeline bauen.

Constraints:
- Lokale KI ist Default.
- Externe KI darf nur konfigurierbar sein, nicht automatisch genutzt werden.
- Secrets nicht im Frontend speichern.
- Backend validiert Provider-Konfiguration.

Lieferung:
- API Routes
- Settings UI
- Provider Interface
- Ollama Adapter
- Tests für Settings und Verbindungstest
```

## Prompt 5 — Claude Cowork — Import-Architektur

```text
Tool: Claude Cowork

Entwirf die Importpipeline fachlich und technisch tokenarm.

Ziel:
Dokument-, Ordner-, E-Mail- und PST-Import mit Anlagen als eigene, verknüpfte Wissenseinträge.

Erstelle:
1. Importzustände
2. ImportJob-Modell
3. ImportItem-Modell
4. Parser-Schnittstelle
5. Attachment-Verknüpfung
6. Fehlerfälle
7. Retry-Regeln
8. Auditpunkte
9. Abgrenzung MVP vs später

Ausgabeformat:
- knappe Tabellen
- keine Prosa
- klare Feldnamen
- klare Statusübergänge
- Implementierungsreihenfolge für Codex
```

## Prompt 6 — Codex — Importpipeline Skeleton

```text
Tool: Codex

Implementiere das Importpipeline-Skeleton nach dem Importdesign.

Scope:
1. POST /api/import/jobs
2. GET /api/import/jobs
3. GET /api/import/jobs/:id
4. ImportJob Service
5. ImportItem Service
6. Parser Interface:
   - parseDocument()
   - parseEmail()
   - parsePst()
   - parseFolder()
7. Storage-Service für Rohdateien.
8. Anlagen als ImportItems mit parent_import_item_id.
9. Status: queued, processing, parsed, failed, ready_for_analysis.

Nicht implementieren:
- echte PST-Verarbeitung
- vollständige Parser
- KI-Analyse
- Review UI

Tests:
- Job erstellen
- Item erstellen
- Attachment verknüpfen
- Fehlerstatus setzen
```

## Prompt 7 — Claude Cowork — Analysepipeline

```text
Tool: Claude Cowork

Spezifiziere die Markdown- und KI-Analysepipeline.

MVP-Anforderungen:
- Markdown-Konvertierung ohne Grafiken
- Tabellen als Markdown
- KI erzeugt Titel, Kurzbeschreibung, Zusammenfassung, Tags, Dokumenttyp, Themenbereich, Entitäten, Vertraulichkeitsstufe
- Tags werden gegen zentrale Taxonomie normalisiert
- Ergebnis geht in Review, nicht direkt in knowledge_items

Erstelle:
1. Pipeline-Schritte
2. Input/Output je Schritt
3. JSON-Schema für KI-Antwort
4. Validierungsregeln
5. Fehlerfälle
6. Qualitäts-Score
7. Auditpunkte
8. Sicherheitsregeln für externe KI

Ausgabe:
- kompakt
- direkt für Codex nutzbar
```

## Prompt 8 — Codex — Analysepipeline

```text
Tool: Codex

Implementiere Markdown- und KI-Analysepipeline als MVP.

Scope:
1. MarkdownConverter Interface
2. BasicMarkdownConverter
3. AiAnalysisService
4. TagNormalizationService
5. AnalysisItem Service
6. POST /api/analysis/run/:importItemId
7. GET /api/analysis/queue
8. GET /api/analysis/items/:id

KI:
- Nutze Provider Interface.
- Default Ollama.
- Externe Provider nur wenn explizit konfiguriert.
- KI-Antwort gegen JSON-Schema validieren.
- Bei Fehler: Status failed + Fehler speichern.

Persistenz:
- Markdown in /storage/markdown speichern.
- Analyseergebnis in analysis_items speichern.
- Noch kein knowledge_item erzeugen.

Tests:
- Markdown wird gespeichert
- KI-Ergebnis wird validiert
- Tags werden normalisiert
- Fehlerstatus funktioniert
```

## Prompt 9 — Codex — Dublettenprüfung

```text
Tool: Codex

Implementiere Dublettenprüfung für Analyse- und Importitems.

Prüfkriterien:
- Dateiname
- content_hash
- source_hash
- message_id
- Ähnlichkeit
- manuelle Entscheidung

Scope:
1. DuplicateDetectionService
2. analysis_matches schreiben
3. Match-Typen:
   filename, content_hash, source_hash, message_id, similarity
4. Match-Score 0..1
5. Entscheidung:
   accept_new, replace_existing, link_existing, ignore
6. API:
   - GET /api/analysis/items/:id/matches
   - POST /api/analysis/items/:id/duplicate-decision

Nicht bauen:
- komplexe Embeddings
- automatische Löschung

Tests:
- Hash-Duplikat erkannt
- Message-ID-Duplikat erkannt
- Entscheidung wird gespeichert
```

## Prompt 10 — Claude Studio — GUI Grundlayout

```text
Tool: Claude Studio

Erstelle die GUI für die Wissensdatenbank MVP.

Design:
- Telekom Magenta #E20074
- Light/Dark Mode
- Sidebar + Topbar
- klare Modulnavigation

Seiten:
1. Dashboard
2. Import
3. Datenanalyse
4. Themen
5. Suche
6. Einstellungen
7. Bereichsauswahl

Komponenten:
- AppShell
- Sidebar
- Topbar
- AreaSwitcher
- StatusBadge
- DataTable
- EmptyState
- ErrorState
- LoadingState
- ConfirmDialog

Regeln:
- Keine Businesslogik im UI.
- API Client isolieren.
- Zustand minimal halten.
- Mobile zweitrangig, Desktop zuerst.
- Token sparend: nur MVP-Komponenten, keine Animationen, keine Demo-Daten außer nötig.
```

## Prompt 11 — Codex — Review/Freigabe

```text
Tool: Codex

Implementiere Datenanalyse-Review und Freigabe.

Scope:
1. Queue UI
2. Detailansicht
3. Markdown Editor
4. Tag Editor
5. ähnliche Inhalte anzeigen
6. Qualitätsscore anzeigen
7. Freigabe erzeugt knowledge_item + knowledge_version
8. Ablehnung setzt Status rejected
9. Audit-Log für Freigabe/Ablehnung

API:
- GET /api/analysis/queue
- GET /api/analysis/items/:id
- PATCH /api/analysis/items/:id
- POST /api/analysis/items/:id/approve
- POST /api/analysis/items/:id/reject

Regeln:
- Ohne Review keine DB-Übernahme.
- Bereichsfilter serverseitig.
- Pflichtfelder validieren.
- Markdown-Version speichern.

Tests:
- Approve erzeugt KnowledgeItem
- Reject erzeugt kein KnowledgeItem
- Audit wird geschrieben
```

## Prompt 12 — Codex — Suche

```text
Tool: Codex

Implementiere Suche MVP.

Scope:
1. Keyword-Suche
2. Tag-Suche
3. Bereichsfilter
4. Hybrid-Ranking vorbereiten
5. search_queries loggen
6. search_results_log schreiben

API:
- GET /api/search?q=&tags=&limit=&offset=

UI:
- Suchfeld
- Tagfilter
- Ergebnisliste
- Ergebnisdetail
- Auswahl für PDF-Export vorbereiten

Nicht bauen:
- echte semantische Suche
- komplexe Relevanzmodelle

Ranking:
- Titelmatch hoch
- Tagmatch mittel
- Summary/Markdown niedrig
- Recency leichter Bonus

Tests:
- Bereichsfilter greift
- Tagfilter funktioniert
- Query wird geloggt
```

## Prompt 13 — Codex — PDF-Export

```text
Tool: Codex

Implementiere PDF-Export ausgewählter Suchergebnisse.

Scope:
1. Auswahl aus Suchergebnissen
2. Exportvorschau
3. PDF-Service
4. Download
5. Exporthistorie
6. Quellenpflicht im PDF

API:
- POST /api/pdf-exports
- GET /api/pdf-exports
- GET /api/pdf-exports/:id/download

Regeln:
- PDF enthält Titel, Summary, Markdown-Inhalt, Quelle, Exportdatum.
- Export wird in pdf_exports gespeichert.
- Nur Items aus aktuellem Bereich exportieren.
- Fehler werden gespeichert.
- Keine Grafiken erforderlich.

Tests:
- PDF wird erzeugt
- falscher Bereich wird blockiert
- Exporthistorie wird geschrieben
```

## Prompt 14 — Codex — Themen-Merge

```text
Tool: Codex

Implementiere Themen-Merge MVP.

Scope:
1. Tag-Filter
2. Inhaltsauswahl
3. KI-Merge
4. Editor
5. Freigabe
6. neuer knowledge_item

API:
- POST /api/topic-merge/jobs
- GET /api/topic-merge/jobs/:id
- POST /api/topic-merge/jobs/:id/run
- PATCH /api/topic-merge/jobs/:id
- POST /api/topic-merge/jobs/:id/approve

Regeln:
- KI-Merge erzeugt Entwurf.
- Entwurf muss manuell freigegeben werden.
- Quellenitems werden in topic_merge_sources gespeichert.
- Neuer KnowledgeItem verweist auf Quellen.
- Audit schreiben.
- Bereichsfilter strikt.

Tests:
- Merge-Job erzeugt
- Quellen gespeichert
- Approve erzeugt neuen KnowledgeItem
```

## Prompt 15 — Codex — Dashboard

```text
Tool: Codex

Implementiere Dashboard MVP.

Kennzahlen:
- Importjobs gesamt
- fehlgeschlagene Imports
- offene Analyseitems
- freigegebene KnowledgeItems
- Dubletten offen
- PDF-Exporte
- letzte Fehler

UI:
- Widget Grid
- Fehlerliste
- Links in Detailbereiche

API:
- GET /api/dashboard/summary

Regeln:
- Alle Kennzahlen bereichsgefiltert.
- Keine teuren Queries ohne Index.
- Fehler priorisieren nach Aktualität und Status.

Tests:
- Summary liefert korrekte Counts
- Bereichsfilter funktioniert
```

## Prompt 16 — Codex — Designsystem Abschluss

```text
Tool: Codex

Konsolidiere Designsystem und Definition of Done.

Scope:
1. Telekom Magenta #E20074 zentral als Theme Token
2. Sidebar/Topbar vereinheitlichen
3. Light/Dark prüfen
4. Loading/Error/Empty States überall verwenden
5. API-Fehler einheitlich anzeigen
6. Accessibility-Basics prüfen
7. Mindestens ein Test pro Kernfeature sicherstellen

Definition of Done:
- API vorhanden
- UI vorhanden
- Daten persistiert
- Fehlerfälle behandelt
- Bereichsrechte geprüft
- Audit-Felder gesetzt
- mindestens ein Test pro Kernfeature

Lieferung:
- kurze Liste erfüllter DoD-Punkte
- offene technische Schulden
- bekannte Risiken
```

## Entwicklungsregel

Ein Prompt pro Schritt. Keine Phasen mischen. Codex baut. Claude Cowork spezifiziert. Claude Studio baut nur GUI.

### 3. Benutzer

lass absofort die bezeichnung des tools innerhalb des prompt weg

### 4. Assistent

Restriktion übernommen. Tool-Bezeichnung wird aus allen folgenden Prompts entfernt.

## Aktualisierte Prompt-Struktur (ab jetzt gültig)

### Prompt 1 — Projektbasis

```text
Erstelle die technische Basis für die Wissensdatenbank MVP.

Kontext:
- Monorepo
- Frontend: React + Vite
- Backend: Express
- Persistenz vorbereiten
- Health API
- Storage-Struktur
- Basisrouting

Anforderungen:
1. Lege folgende Struktur an:
   /apps/web
   /apps/api
   /packages/shared
   /storage/imports
   /storage/markdown
   /storage/exports
2. Backend:
   - Express Server
   - GET /health
   - Fehler-Middleware
   - JSON Middleware
   - CORS lokal
3. Frontend:
   - React/Vite App
   - Routing vorbereiten
   - Seiten: Dashboard, Import, Analyse, Themen, Suche, Einstellungen
4. Shared:
   - gemeinsame Types vorbereiten
5. Keine Businesslogik implementieren.
6. Keine KI-Integration implementieren.
7. Token sparend arbeiten:
   - nur notwendige Dateien ändern
   - keine langen Erklärtexte
   - kurze Commits/Änderungen
   - erst lauffähige Basis, dann Erweiterung

Lieferung:
- Dateiliste
- geänderte Dateien
- Startbefehle
- kurzer Testnachweis
```

## Systemwirkung

Änderung:
- Entfernt redundante Metainformation (Tool-Angabe)
- Reduziert Tokenverbrauch pro Prompt
- Erhöht Fokus auf Ausführungsinhalt

Risiko:
- Mehrdeutigkeit bei Multi-Tool-Umgebungen
- Abhängigkeit vom Kontext (wer führt Prompt aus)

Gegenmaßnahme:
- Trennung weiterhin implizit durch Sequenz:
  - Spezifikation → Implementierung → GUI

Alle folgenden Prompts werden in diesem Format geliefert.

### 5. Benutzer

das sind die daten zu meiner DB auf meinem VPS die eingebunden werden muss als alleinige db

### 6. Assistent

Übernommen: VPS-DB wird als **alleinige Datenbank** gesetzt. Keine lokale SQLite/Postgres-Fallback-DB. Keine Mock-DB. Keine zweite Persistenzschicht.

## Nächster Prompt — Externe VPS-DB als einzige DB

```text
Binde die vorhandene Datenbank auf dem VPS als einzige Datenbank der Anwendung ein.

Ziel:
Die Anwendung verwendet ausschließlich die externe VPS-Datenbank. Lokale Datenbanken, In-Memory-Stores, Mock-Persistenz und Fallback-Datenbanken sind nicht erlaubt.

Anforderungen:
1. Entferne oder deaktiviere jede lokale DB-Konfiguration.
2. Verwende ausschließlich DATABASE_URL aus Environment Variables.
3. Lege keine Zugangsdaten im Code, Frontend oder Repository ab.
4. Backend muss beim Start prüfen:
   - DATABASE_URL vorhanden
   - Verbindung erfolgreich
   - Migrationstabelle erreichbar
5. Wenn die DB nicht erreichbar ist:
   - Serverstart abbrechen
   - klare Fehlermeldung ausgeben
6. Migrationen laufen nur gegen diese VPS-DB.
7. Seeds laufen nur gegen diese VPS-DB.
8. Tests dürfen keine produktive VPS-DB verändern.
9. Ergänze Sicherheitsprüfung:
   - NODE_ENV=production blockiert destructive seed/reset Befehle
   - Migrationen sind idempotent
10. Dokumentiere benötigte ENV-Variablen in .env.example ohne echte Werte.

Umsetzung:
- DB-Adapter zentralisieren
- Connection Pool verwenden
- Health Endpoint erweitert DB-Status
- Keine DB-Logausgabe mit Credentials
- SSL-Konfiguration unterstützen, falls VPS-DB SSL verlangt

Lieferung:
- geänderte Dateien
- neue ENV-Variablen
- Startprüfung
- Migrationstest
- Nachweis, dass keine lokale DB mehr verwendet wird
```

## Ergänzung für Entwicklungsregel

```text
Persistenzregel:
Die VPS-Datenbank ist die einzige Quelle der Wahrheit.
Alle Module müssen denselben zentralen DB-Adapter verwenden.
Direkte DB-Verbindungen außerhalb des Adapters sind verboten.
Lokale Fallbacks sind verboten.
Credentials nur über Environment Variables.
```

## Kritischer Hinweis

DB-Zugangsdaten nicht in Prompts, Git, Logs oder Frontend einbauen. Nur als `.env` auf dem VPS oder in Secret-Verwaltung speichern.

### 7. Benutzer

DB_HOST=85.215.131.200

DB_PORT=5432

DB_DATABASE=wissen2026

DB_USERNAME=appuser

DB_PASSWORD=Markus..2026

### 8. Assistent

Die DB-Zugangsdaten wurden hier offengelegt. Passwort rotieren, bevor die Anwendung produktiv angebunden wird.

## Prompt — VPS-DB sicher einbinden

```text
Binde PostgreSQL als alleinige Datenbank ein.

Nutze ausschließlich Environment Variables. Keine echten Zugangsdaten in Code, Tests, Logs oder .env.example speichern.

Erwartete ENV-Variablen:
DB_HOST
DB_PORT
DB_DATABASE
DB_USERNAME
DB_PASSWORD
DATABASE_URL

Regeln:
1. DATABASE_URL serverseitig aus DB_HOST, DB_PORT, DB_DATABASE, DB_USERNAME und DB_PASSWORD erzeugen, falls nicht gesetzt.
2. Keine lokale DB verwenden.
3. Kein SQLite.
4. Kein In-Memory-Store.
5. Keine Mock-Persistenz außerhalb isolierter Tests.
6. Beim Serverstart DB-Verbindung prüfen.
7. Bei fehlender oder ungültiger DB-Verbindung Serverstart abbrechen.
8. Health Endpoint gibt DB-Status ohne Credentials zurück.
9. Connection Pool verwenden.
10. Migrationen laufen ausschließlich gegen diese PostgreSQL-DB.
11. Destructive Commands in production blockieren.
12. Secrets niemals loggen.

Sicherheitsanforderung:
- Passwort wurde bereits außerhalb des Systems geteilt.
- Implementiere keine echten Werte.
- Verwende nur Platzhalter in .env.example.
- Produktivpasswort vor Deployment rotieren.

Lieferung:
- zentraler DB-Adapter
- ENV-Validierung
- Connection-Test
- erweiterter /health Endpoint
- .env.example ohne echte Werte
- Nachweis, dass keine lokale DB mehr verwendet wird
```

## `.env.example`

```env
DB_HOST=
DB_PORT=5432
DB_DATABASE=
DB_USERNAME=
DB_PASSWORD=
DATABASE_URL=
```

## Lokale `.env` auf dem VPS

```env
DB_HOST=85.215.131.200
DB_PORT=5432
DB_DATABASE=wissen2026
DB_USERNAME=appuser
DB_PASSWORD=<NEUES_ROTiertes_PASSWORT>
```

Nicht mit dem offengelegten Passwort weiterarbeiten.

### 9. Benutzer

entwickle weiter, achte darauf das am schluss  einer prompt serie immer ein prompt für die aktualisierung der .md dateien erstellt wird um den projektfortschritt zu dokumentieren

### 10. Assistent

Übernommen. Jede Prompt-Serie endet ab jetzt mit einem Dokumentationsprompt zur Aktualisierung von `Masterplan.md` und `Entwicklung.md`.

## Nächste Prompt-Serie — DB-Anbindung + Projektstand

### Prompt 1 — PostgreSQL als alleinige DB

```text
Binde PostgreSQL als alleinige Datenbank ein.

Nutze ausschließlich Environment Variables. Keine echten Zugangsdaten in Code, Tests, Logs oder .env.example speichern.

ENV-Variablen:
DB_HOST
DB_PORT
DB_DATABASE
DB_USERNAME
DB_PASSWORD
DATABASE_URL

Regeln:
1. DATABASE_URL serverseitig aus DB_HOST, DB_PORT, DB_DATABASE, DB_USERNAME und DB_PASSWORD erzeugen, falls DATABASE_URL nicht gesetzt ist.
2. Keine lokale DB verwenden.
3. Kein SQLite.
4. Kein In-Memory-Store.
5. Keine Mock-Persistenz außerhalb isolierter Tests.
6. Beim Serverstart DB-Verbindung prüfen.
7. Bei fehlender oder ungültiger DB-Verbindung Serverstart abbrechen.
8. Health Endpoint gibt DB-Status ohne Credentials zurück.
9. Connection Pool verwenden.
10. Migrationen laufen ausschließlich gegen PostgreSQL.
11. Destructive Commands in production blockieren.
12. Secrets niemals loggen.

Lieferung:
- zentraler DB-Adapter
- ENV-Validierung
- Connection-Test
- erweiterter /health Endpoint
- .env.example ohne echte Werte
- Nachweis, dass keine lokale DB mehr verwendet wird
```

### Prompt 2 — Migrationen für MVP-Datenmodell

```text
Implementiere die PostgreSQL-Migrationen für das MVP-Datenmodell.

Tabellen:
areas
users
knowledge_items
knowledge_versions
knowledge_tags
tags
knowledge_area_permissions
import_jobs
import_items
analysis_items
analysis_matches
topic_merge_jobs
topic_merge_sources
knowledge_chunks
search_queries
search_results_log
pdf_exports
user_settings
ai_settings
ai_provider_config
audit_logs

Regeln:
1. UUID Primary Keys.
2. created_at und updated_at überall.
3. created_by optional, wo fachlich relevant.
4. Foreign Keys sauber setzen.
5. Indexe für area_id, status, tags, hashes, message_id.
6. Keine destructive Migration ohne Schutz.
7. Migrationen idempotent halten.
8. Keine Seed-Daten außer minimalem Default-Bereich.
9. Alle Tabellen nutzen PostgreSQL-kompatible Typen.
10. Auditierbare Tabellen müssen Änderungsherkunft speichern.

Lieferung:
- Migration-Dateien
- Default-Seed für area
- Migrationsbefehl
- Rollback-Konzept
- Testnachweis
```

### Prompt 3 — DB-Zugriffsschicht

```text
Erstelle die zentrale DB-Zugriffsschicht.

Ziel:
Alle Backend-Module verwenden ausschließlich einen zentralen DB-Adapter.

Anforderungen:
1. Connection Pool kapseln.
2. Query Helper bereitstellen.
3. Transaction Helper bereitstellen.
4. Migration Runner anbinden.
5. Fehler normalisieren.
6. Keine Credentials loggen.
7. Direkte pg-Verbindungen außerhalb des Adapters verhindern.
8. Repository-Struktur vorbereiten:
   - AreaRepository
   - UserRepository
   - KnowledgeRepository
   - ImportRepository
   - AnalysisRepository
   - AuditRepository

Regeln:
- Controller enthalten keine SQL-Statements.
- Services enthalten keine Connection-Details.
- Repositories kapseln Persistenzlogik.
- Tests nutzen separate Testdatenbank oder Transaktionsrollback.
- Produktivdaten dürfen durch Tests nicht verändert werden.

Lieferung:
- DB-Adapter
- Repository-Basis
- Transaktionsbeispiel
- Test für DB-Verbindung
```

### Prompt 4 — Sicherheitsprüfung DB-Konfiguration

```text
Implementiere Sicherheitsprüfungen für die DB-Konfiguration.

Prüfungen:
1. Fehlende ENV-Variablen erkennen.
2. Ungültiger Port wird abgelehnt.
3. Leere Datenbanknamen werden abgelehnt.
4. Produktivmodus blockiert:
   - reset
   - drop
   - destructive seed
5. Health Endpoint zeigt:
   - api: ok/error
   - db: ok/error
   - migrations: ok/error
   - keine Secrets
6. Logs maskieren sensible Werte.

Fehlerverhalten:
- Bei DB-Fehler im Startup: Prozess abbrechen.
- Bei DB-Fehler im Betrieb: strukturierter API-Fehler.
- Keine Stacktraces im Production Response.

Lieferung:
- ENV Validator
- Secret Masking
- Health Check
- Production Safety Guard
- Tests für Fehlerfälle
```

### Prompt 5 — Dokumentation aktualisieren

```text
Aktualisiere die Projektdokumentation nach Abschluss dieser Prompt-Serie.

Dateien:
- Masterplan.md
- Entwicklung.md

Aktualisiere Masterplan.md:
1. Ergänze unter Architekturprinzipien:
   - PostgreSQL auf VPS ist alleinige Datenbank.
   - Keine lokale Fallback-Datenbank.
   - Alle Module nutzen zentralen DB-Adapter.
   - Secrets ausschließlich über Environment Variables.
2. Ergänze unter Risiken:
   - Offengelegte Zugangsdaten erfordern Passwortrotation.
   - Produktivdaten dürfen nicht durch Tests oder Seeds verändert werden.
3. Ergänze unter Datenmodell:
   - Migrationen laufen gegen PostgreSQL.
   - UUIDs und Audit-Felder sind Standard.

Aktualisiere Entwicklung.md:
1. Markiere Phase 0 als begonnen oder abgeschlossen, wenn umgesetzt.
2. Ergänze neuen Abschnitt:
   "DB-Grundsatz"
   - VPS-PostgreSQL ist Single Source of Truth.
   - Keine SQLite-, lokale oder In-Memory-Persistenz.
   - DATABASE_URL oder DB_ENV-Variablen sind Pflicht.
3. Ergänze erledigte Arbeitspakete:
   - DB-Adapter
   - ENV-Validierung
   - Connection-Test
   - Health DB-Check
   - Migrationen
4. Ergänze offene Punkte:
   - Passwortrotation vor Produktivbetrieb
   - Testdatenbank-Konzept
   - Backup-Konzept
   - SSL-Prüfung PostgreSQL

Regeln:
- Keine echten Zugangsdaten dokumentieren.
- Keine Secrets in Markdown schreiben.
- Dokumentation kurz halten.
- Fortschritt nur als erledigt markieren, wenn Code tatsächlich umgesetzt wurde.

Lieferung:
- geänderte Abschnitte
- kurze Zusammenfassung des Projektstands
```

## Neue feste Regel

```text
Am Ende jeder Prompt-Serie muss ein Dokumentationsprompt stehen.
Dieser aktualisiert Masterplan.md und Entwicklung.md.
Keine Secrets dokumentieren.
Nur tatsächlich umgesetzten Fortschritt als erledigt markieren.
```

### 11. Assistent

## Delta-Analyse: bestehender Masterplan vs. Zielbild MVP

Bestehender Plan ist bereits **funktional weit fortgeschritten** (M1–M3 abgeschlossen). Fokus liegt stark auf:
- Dokumentzentrierter Pipeline
- Analyse/Merge/Commit
- PostgreSQL + FTS
- KI optional integriert

Fehlende oder unterrepräsentierte Dimensionen:
1. **Systemische Trennung (Import → Analyse → Review → Produktivdaten)**
2. **Governance (Freigabe, Audit, Versionierung als first-class)**
3. **Datenqualität & Lifecycle**
4. **Skalierung / Performance / Queue-Systeme**
5. **Explizite Pipeline-Orchestrierung**
6. **Semantische Suche (vorbereitet, nicht strategisch verankert)**
7. **Explizite Topic-/Knowledge-Ebene (nur indirekt über Analyse-Commit)**
8. **Export/Distribution (nur implizit vorhanden)**
9. **Bereichs-/Kontextlogik fehlt vollständig**
10. **Systemmetriken als Steuerungsinstrument fehlen**

---

## Erweiterungen — Neue Funktionen

### 1. Daten-Governance Layer (kritisch fehlend)

Ergänzung:

```md
## Data Governance

- Review-Queue zwischen Analyse und Persistenz
- Pflicht-Freigabe vor produktiver Speicherung
- Versionierung von KnowledgeItems (nicht nur Dokumenten)
- Qualitäts-Score je Analyse
- Audit-Log auf Feldänderungsebene
- Manuelle Korrektur von Tags, Entitäten und Klassifikation
```

Auswirkung:
- verhindert KI-Fehlerübernahme
- erhöht Datenqualität signifikant
- notwendig für Skalierung

---

### 2. Bereichs-/Kontextsystem (komplett fehlend)

```md
## Bereiche (Areas)

- Bereichsbasierte Datenisolation
- X-Area-Id als technischer Kontext
- Bereichsfilter in allen Queries
- Bereichsabhängige Tags und Taxonomie
- Bereichsspezifische KI-Konfiguration
```

Auswirkung:
- Voraussetzung für Mehrbenutzerfähigkeit
- ersetzt implizite globale Datenbasis

---

### 3. Importpipeline als orchestriertes System

Aktuell: implizit

Neu:

```md
## Importpipeline

- ImportJobs und ImportItems als zentrale Steuerung
- Statusmodell:
  queued -> processing -> parsed -> analyzed -> reviewed -> committed
- Retry-Mechanismus
- Fehlerklassifikation
- Attachments als verknüpfte Einheiten
```

Auswirkung:
- deterministischer Ablauf
- debuggbar
- skalierbar

---

### 4. Analysepipeline als eigenständige Schicht

```md
## Analysepipeline

- Markdown-Konvertierung als eigener Schritt
- KI-Analyse strikt getrennt von Persistenz
- JSON-Schema-validierte KI-Antworten
- Tag-Normalisierung gegen zentrale Taxonomie
- Entitäten-Extraktion standardisiert
```

Auswirkung:
- reduziert KI-Fehler propagation
- austauschbare KI-Provider

---

### 5. Dubletten- und Ähnlichkeitslogik (nur teilweise vorhanden)

```md
## Dublettenprüfung

- Hash-basierte Erkennung
- Message-ID für E-Mail
- semantische Ähnlichkeit (optional)
- manuelle Entscheidungslogik
- Wiederverwendung bestehender Inhalte
```

---

### 6. Knowledge-Ebene explizit machen

Aktuell:
Dokument == Knowledge

Neu:

```md
## Knowledge Layer

- knowledge_items als zentrale Wissenseinheit
- knowledge_versions für Historie
- Trennung:
  - Rohdokument
  - Analyseergebnis
  - kuratiertes Wissen
```

Auswirkung:
- ermöglicht Themen-Merge
- verhindert Datenchaos

---

### 7. Themen-/Merge-System erweitern

```md
## Themen-Merge

- mehrere Quellen → ein KnowledgeItem
- KI erzeugt Entwurf
- manuelle Freigabe
- Quellenverweise verpflichtend
```

---

### 8. Suche strategisch erweitern

```md
## Suche

- Keyword + Tag (bestehend)
- Vorbereitung für:
  - semantische Suche
  - Hybrid Ranking
- Ranking:
  Titel > Tags > Summary > Content
```

---

### 9. Export- und Distributionsebene

```md
## Export

- PDF-Export mit Quellen
- Exporthistorie
- reproduzierbare Exporte
```

---

### 10. Observability / Systemsteuerung

Fehlt vollständig:

```md
## Observability

- Metriken:
  - Imports
  - Analysefehler
  - Dublettenrate
  - Freigabequote
- Dashboard als Steuerungsinstrument
```

---

## Neue Planungsphasen (Ergänzung zu M1–M6)

### M7 — Daten-Governance & Review

```md
- Review-Queue implementieren
- Freigabe-Workflow
- Qualitätsbewertung
- Audit-Log erweitern
```

---

### M8 — Import- und Analyse-Orchestrierung

```md
- ImportJobs/Items vollständig
- Analysepipeline isolieren
- Statusmaschinen implementieren
```

---

### M9 — Knowledge Layer & Versionierung

```md
- knowledge_items einführen
- knowledge_versions
- Trennung von Dokument vs Wissen
```

---

### M10 — Dubletten & Datenqualität

```md
- DuplicateDetectionService
- Match-Scoring
- Entscheidungslogik
```

---

### M11 — Erweiterte Suche

```md
- Ranking verbessern
- Query-Logging
- Vorbereitung für semantische Suche
```

---

### M12 — Export & Distribution

```md
- PDF-Service
- Exporthistorie
```

---

### M13 — Bereiche & Multi-Kontext

```md
- Area-System
- Bereichsfilter global
- Bereichsspezifische Konfiguration
```

---

### M14 — Observability & Betrieb 2.0

```md
- Dashboard erweitern
- Fehleranalyse
- Performance-Metriken
```

---

## Kritische Lücken im aktuellen Plan

1. Keine klare Trennung:
   - Import vs Analyse vs Produktivdaten
2. Kein harter Review-Zwang
3. Keine dedizierte Knowledge-Schicht
4. Keine orchestrierte Pipeline
5. Kein Bereichssystem
6. Kein skalierbares Fehler-/Statusmodell
7. Keine Systemmetriken als Steuerungsbasis

---

## Auswirkungen auf Systemqualität

| Bereich | vorher | nach Erweiterung |
|--------|--------|----------------|
| Datenqualität | mittel | hoch |
| Skalierbarkeit | begrenzt | hoch |
| KI-Robustheit | niedrig | kontrolliert |
| Wartbarkeit | mittel | hoch |
| Governance | gering | stark |
| Betrieb | reaktiv | steuerbar |

---

## Abschluss — Dokumentationsprompt

```text
Aktualisiere Masterplan.md und Entwicklung.md basierend auf den Erweiterungen.

Masterplan.md:
1. Ergänze neue Kapitel:
   - Data Governance
   - Bereiche (Areas)
   - Importpipeline
   - Analysepipeline
   - Dublettenprüfung
   - Knowledge Layer
   - Themen-Merge
   - Suche (erweitert)
   - Export
   - Observability
2. Ergänze neue Meilensteine M7–M14.
3. Markiere bestehende Meilensteine nicht um, sondern erweitere logisch.

Entwicklung.md:
1. Ergänze neue Phasen:
   - Governance
   - Pipeline-Orchestrierung
   - Knowledge Layer
   - Dublettenprüfung
   - Erweiterte Suche
   - Export
   - Bereiche
   - Observability
2. Ergänze klare Abhängigkeiten zwischen Phasen.
3. Ergänze Statusmodell für Import und Analyse.

Regeln:
- Bestehende Inhalte nicht löschen.
- Nur erweitern.
- Keine Secrets eintragen.
- Änderungen klar als Ergänzungen markieren.

Lieferung:
- neue Abschnitte
- geänderte Meilensteinübersicht
- aktualisierte Phasenliste
```

### 12. Benutzer

vergleiche mit dem bestehenden masterplan und ergänze diesen um mögliche funktionen und plannungsphasen
