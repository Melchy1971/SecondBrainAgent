---
title: "Datenbank-Schema für E-Mails"
type: chatgpt_conversation
source: chatgpt
source_id: "698091da-1a1c-8394-84b0-dfcd5dfc0f3c"
created: 2026-02-02
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
---


# Datenbank-Schema für E-Mails

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `698091da-1a1c-8394-84b0-dfcd5dfc0f3c`
- Nachrichten: 6

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

erstelle mir einen Prompt zum erstellen einer datenbank nach folgenden kriterien: # Masterplan: E-Mail Wissensdatenbank

## ✅ Abgeschlossene Features

### 1. Datenbank-Schema
- ✅ PostgreSQL-Datenbank mit Extensions (uuid-ossp, pg_trgm, vector)
- ✅ Tabelle `emails` (id, message_id, subject, sender, recipients, sent_date, body_text, body_html, summary_text, etc.)
- ✅ Tabelle `categories` (id, name, description)
- ✅ Tabelle `email_categories` (email_id, category_id, confidence)
- ✅ Tabelle `email_embeddings` (email_id, model, dim, vector)
- ✅ Tabelle `folders` (id, pst_id, parent_id, name, path)
- ✅ Tabelle `threads` (id, root_message_id, subject)
- ✅ Tabelle `ollama_config` (id, base_url, model_name, timeout_seconds, enabled, status-felder)
- ✅ Tabelle `pst_files` (id, original_name, stored_path, uploaded_at, status, processed_count, last_error)

### 2. Projektstruktur
- ✅ Einstiegspunkt `main.py` (FastAPI-Anwendung)
- ✅ Applikationspaket `app/` mit klar getrennten Modulen:
  - ✅ `app/api/` – Routen/Controller (`email_routes.py`, `search_routes.py`, `admin_routes.py`, `provider_routes.py`, `job_routes.py`)
  - ✅ `app/core/` – Konfiguration, Logging, Security (`config.py`, `settings.py`, `logging_config.py`, `security.py`)
  - ✅ `app/db/` – Datenbank-Setup (`database.py`, `base.py`, `init_db.py`, `migrations/`)
  - ✅ `app/models/` – ORM-Modelle (`email.py`, `category.py`, `embedding.py`, `jobs.py`, `provider.py`, `analysis_history.py`)
  - ✅ `app/schemas/` – Pydantic-Schemas (`email_data.py`, `analysis_result.py`, `search.py`, `provider.py`)
  - ✅ `app/services/` – Fachlogik/Use-Cases (Import, Analyse, Embeddings, Suche, Qualität, Kategorien, LLM-Wrapper)
  - ✅ `app/services/llm/` – LLM-Provider-Fabrik und Implementierungen (Ollama, OpenAI, Gemini, Embedding-Backends)
  - ✅ `app/prompts/` – Prompt-Definitionen für Analyse & Quality-Check
  - ✅ `app/utils/` – Helfer (JSON-Fix, Text-Cleaning, Timing, OS-Helpers)
  - ✅ `app/templates/` – Jinja2-Templates (Listen, Detail, Debug, Admin, Settings)
  - ✅ `app/static/` – CSS, JS, Icons

### 3. Backend (FastAPI)
- ✅ FastAPI-Anwendung (`app/web/main.py`)
- ✅ Dependency Injection für Datenbank-Sessions
- ✅ Template-Rendering mit Jinja2
- ✅ Static File Serving

### 4. E-Mail-Import
- ✅ PST-Importer (`app/pst_importer.py`) - optional (libpff-python)
- ✅ EML-Importer (`app/eml_importer.py`)
- ✅ Mock-Importer (`app/mock_importer.py`) für Tests
- ✅ Import-Service (`app/services/import_service.py`)
  - ✅ Ordner-Verwaltung
  - ✅ Duplikaterkennung
  - ✅ Batch-Import

### 5. Ollama-Integration
- ✅ Ollama-Analyzer (`app/ollama_analyzer.py`)
  - ✅ E-Mail-Zusammenfassung
  - ✅ E-Mail-Kategorisierung
  - ✅ `analyze()`-Methode für kombinierte Analyse
- ✅ Ollama-Konfigurationsservice (`app/services/ollama_config_service.py`)
- ✅ Ollama-Test-Service (`app/services/ollama_test_service.py`)
- ✅ Ollama-Status-Service (`app/services/ollama_status_service.py`)
- ✅ Ollama-Analyzer-Factory (`app/services/ollama_analyzer_factory.py`)
- ✅ Analyse-Service (`app/services/analyze_service.py`)
  - ✅ Batch-Verarbeitung unverarbeiteter E-Mails
  - ✅ Automatische Kategorisierung

### 6. Web-Interface (Frontend)
- ✅ Base-Template (`templates/base.html`)
  - ✅ Navigation
  - ✅ Ollama-Status-Badge im Header
  - ✅ Responsive Design
- ✅ E-Mail-Liste (`templates/emails_list.html`)
  - ✅ Volltextsuche
  - ✅ Filter (Ordner, Kategorie, Datum)
  - ✅ Pagination
  - ✅ Analyse-Button
  - ✅ Status-Anzeige
- ✅ E-Mail-Detail (`templates/email_detail.html`)
  - ✅ Vollständige E-Mail-Anzeige
  - ✅ Kategorien-Badges
  - ✅ Zusammenfassung
  - ✅ Ordnerpfad
- ✅ Kategorien-Übersicht (`templates/categories.html`)
- ✅ PST-Import (`templates/import_pst.html`)
  - ✅ Datei-Upload
  - ✅ Live-Status-Updates (JavaScript Polling)
  - ✅ Analyse-Button
- ✅ PST-Historie (`templates/pst_history.html`)
  - ✅ Übersicht aller Importe
  - ✅ Status-Anzeige
- ✅ Ollama-Einstellungen (`templates/settings_ollama.html`)
  - ✅ Konfigurationsformular
  - ✅ Verbindungstest
  - ✅ Status-Anzeige

### 7. API-Endpoints
- ✅ `GET /` - Weiterleitung zu `/emails`
- ✅ `GET /emails` - E-Mail-Liste mit Filtern
- ✅ `GET /emails/{email_id}` - E-Mail-Detail
- ✅ `GET /categories` - Kategorien-Übersicht
- ✅ `GET /import/pst` - PST-Import-Formular
- ✅ `POST /import/pst` - PST-Datei-Upload mit Hintergrundverarbeitung
- ✅ `GET /import/pst/status/{pst_id}` - Status-Abfrage (JSON)
- ✅ `GET /import/pst/history` - PST-Import-Historie
- ✅ `GET /settings/ollama` - Ollama-Einstellungen anzeigen
- ✅ `POST /settings/ollama` - Ollama-Einstellungen speichern
- ✅ `POST /settings/ollama/test` - Ollama-Verbindung testen
- ✅ `POST /analyze/run` - E-Mail-Analyse im Hintergrund starten

### 8. Konfiguration
- ✅ Umgebungsvariablen (`.env`)
- ✅ Pydantic Settings (`app/config.py`)
  - ✅ Datenbank-Konfiguration
  - ✅ Ollama-Konfiguration
  - ✅ Upload-Verzeichnis-Konfiguration
- ✅ Datenbankgestützte Ollama-Konfiguration

### 9. Hintergrundverarbeitung
- ✅ FastAPI BackgroundTasks für PST-Import
- ✅ FastAPI BackgroundTasks für E-Mail-Analyse
- ✅ Status-Tracking für PST-Importe
- ✅ Fehlerbehandlung und -speicherung

### 10. Scripts
- ✅ `scripts/init_db.py` - Datenbankinitialisierung
- ✅ `scripts/import_and_analyze_pst.py` - CLI-Import und -Analyse
- ✅ `scripts/check_db.py` - Datenbankprüfung
- ✅ `scripts/test_api.py` - API-Tests
- ✅ `scripts/test_create_tables.py` - Tabellenerstellungstest
- ✅ `scripts/test_ollama_config.py` - Ollama-Konfigurationstest
- ✅ `scripts/test_settings_endpoint.py` - Settings-Endpoint-Test
- ✅ `scripts/debug_ollama_models.py` - Ollama-Modell-Debugging
- ✅ `scripts/test_import_endpoint.py` - Import-Endpoint-Test

### 11. Dokumentation
- ✅ README.md mit umfassender Dokumentation
  - ✅ Projektbeschreibung
  - ✅ Features
  - ✅ Schnellstart
  - ✅ Verwendung
  - ✅ Projektstruktur
  - ✅ Technologien
  - ✅ Konfiguration
  - ✅ Datenbank-Schema
  - ✅ Entwicklung
  - ✅ API-Dokumentation
  - ✅ Fehlerbehebung

### 12. Features
- ✅ E-Mail-Import aus PST/EML-Dateien
- ✅ Duplikaterkennung
- ✅ Ordnerstruktur-Erhaltung
- ✅ E-Mail-Analyse mit Ollama (Zusammenfassung + Kategorisierung)
- ✅ Dynamische Kategorisierung
- ✅ Volltextsuche
- ✅ Embeddings-basierte semantische Suche
- ✅ "Ähnliche E-Mails"-Feature
- ✅ Volltextsuche mit PostgreSQL Full-Text-Search
- ✅ Filter (Ordner, Kategorie, Datum)
- ✅ Erweiterte Filteroptionen
- ✅ Erweiterte Statistiken/Dashboard
- ✅ Pagination
- ✅ Benutzer-Authentifizierung (JWT-Login)
- ✅ API-Token-Authentifizierung
- ✅ E-Mail-Markierungen/Tags
- ✅ E-Mail-Export (CSV)
- ✅ Erweiterte Export-Funktionen (CSV-/JSON-Export über Auswahl/Bulk)
- ✅ E-Mail-Anhänge-Verwaltung (Listen & Download)
- ✅ E-Mail-Threading (vollständig)
- ✅ Erweiterte Kategorisierungsoptionen (Mapping, Embeddings, Quality-Layer)
- ✅ Ollama-Konfiguration über Web-UI
- ✅ Ollama-Verbindungstest
- ✅ Ollama-Status-Anzeige im Header
- ✅ PST-Import mit Hintergrundverarbeitung
- ✅ PST-Import-Status-Tracking
- ✅ PST-Import-Historie
- ✅ E-Mail-Analyse im Hintergrund
- ✅ Batch-Analyse mit Fortschrittsanzeige
- ✅ Live-Status-Updates (JavaScript Polling)

## 🔄 In Arbeit / Geplant

### Mögliche Erweiterungen

- [ ] Verbesserte Thread-Ansicht
  - Baumansicht von Konversationen, Collapse/Expand, „nur Thread anzeigen“-Filter
- [ ] Gespeicherte Suchen & Custom Views
  - Benannte Filter/Suchen, die per Klick oder Shortcut geladen werden können
- [ ] Erweiterte Power-Search
  - Query-Builder mit komplexen Bedingungen (Ordner, Kategorie, Tags, Zeitraum, Status)
- [ ] Clustering & Themenübersicht
  - Automatisches Clustering von E-Mails nach Embeddings, „Themen“-Dashboard
- [ ] Kommentare & interne Notizen
  - Pro E-Mail kommentierbare Notizen, optional mit @Mentions
- [ ] Aufgaben-/Status-Workflow
  - Statusfelder wie „open / in_progress / done“ und Zuweisungen an Benutzer
- [ ] IMAP/SMTP-Integration
  - Direktes Abrufen aus Postfächern und Antworten/Weiterleiten aus der App
- [ ] Webhooks & Event-API
  - Events wie „E-Mail importiert“, „Analyse fertig“, „Tag geändert“ nach außen senden
- [ ] 2FA & erweiterte Rollen/Rechte
  - Rollenmodell (Admin / Power-User / Read-Only) plus TOTP-basierte Zwei-Faktor-Auth
- [ ] Smart Reply & Antwortvorschläge
  - AI-gestützte Antwortvorschläge auf Basis des Thread-Kontexts
- [ ] Automatische Aufgaben-Extraktion
  - Todos/Action Items aus E-Mails extrahieren und als Liste anzeigen
- [ ] Feedback-Schleife für Analysequalität
  - User-Feedback („gut/schlecht“) zur kontinuierlichen Verbesserung der Prompts/Modelle

##  Technologie-Stack

- **Backend**: FastAPI, Python 3.x
- **Datenbank**: PostgreSQL mit Extensions (uuid-ossp, pg_trgm, vector)
- **ORM**: SQLAlchemy 2.0
- **Konfiguration**: Pydantic Settings
- **Frontend**: Jinja2 Templates, HTMX (teilweise), Vanilla JavaScript
- **AI-Analyse**: Ollama (lokaler LLM-Server)
- **Email-Import**: libpff-python (PST), Standard-Bibliothek (EML)
- **Web-Server**: Uvicorn

## 🎯 Projektstatus

**Status**: ✅ **Funktionsfähiges MVP**

Das Projekt ist vollständig funktionsfähig und bietet:
- E-Mail-Import aus verschiedenen Quellen
- AI-gestützte Analyse und Kategorisierung
- Vollständiges Web-Interface
- Konfigurierbare Ollama-Integration
- Hintergrundverarbeitung für große Datenmengen
- Status-Tracking und Historie

### 2. Assistent

Klar — hier ist ein **copy-&-paste Prompt**, den du z.B. in ChatGPT / Claude / Gemini werfen kannst, damit dir das Modell **eine PostgreSQL-Datenbank inkl. Extensions, Tabellen, Indizes, Constraints und Migrations-Strategie** für deine **E-Mail-Wissensdatenbank** generiert.

Ich pack dir außerdem ein paar **“Sparringspartner”-Checks** rein: Wo dein Masterplan stillschweigende Annahmen macht, die später wehtun könnten (z.B. Threading, Message-ID-Uniqueness, Embeddings-Versionierung, PST-Folder-Hierarchie).

---

## Prompt: PostgreSQL DB-Schema für E-Mail Wissensdatenbank (MVP → Prod)

**Rolle/Modus:** Du bist ein Senior Database Architect (PostgreSQL) mit Fokus auf Search/Vector/Fulltext. Du designst produktionsreife Schemas inkl. Constraints, Indizes, Performance- und Migrationshinweisen.

**Aufgabe:** Erstelle ein vollständiges PostgreSQL-Schema (DDL) für eine E-Mail-Wissensdatenbank gemäß den folgenden Anforderungen. Liefere:
1) `CREATE EXTENSION` Statements  
2) `CREATE TABLE` Statements mit passenden Datentypen  
3) Primary Keys, Foreign Keys, Unique Constraints, Check Constraints  
4) Indizes (btree, gin, trigram, ggf. partial indexes)  
5) Full-Text Search Setup (tsvector-Spalte + Trigger oder generated column)  
6) Vector-Embeddings Setup (pgvector) inkl. Indexempfehlung (ivfflat/hnsw je nach pgvector)  
7) Hinweise zu Migrations/Revisions (Alembic-kompatibel) und erwarteten Cardinalities  
8) Beispiel: 2–3 sinnvolle Queries (Volltext, semantisch, Filter+Pagination)

### Muss-Tabellen (mit groben Feldern, bitte ergänzen wo sinnvoll)

#### `emails`
- `id` UUID PK (uuid-ossp oder gen_random_uuid)  
- `message_id` TEXT (RFC Message-ID), muss deduplizierbar sein  
- `subject` TEXT  
- `sender` TEXT oder strukturierter (Name + Email)  
- `recipients` (To/Cc/Bcc) – geeignete Struktur wählen (Array/JSONB/Relation) und begründen  
- `sent_date` TIMESTAMPTZ  
- `body_text` TEXT  
- `body_html` TEXT  
- `summary_text` TEXT (AI Summary)  
- zusätzliche sinnvolle Metadaten: `has_attachments`, `language`, `import_source`, `folder_id`, `thread_id`, `in_reply_to`, `references`, `created_at`, `updated_at`  
- Fulltext: `search_vector` (Deutsch+Englisch tauglich)  
- Duplikate: Strategie für EML/PST Import

#### `categories`
- `id` UUID PK  
- `name` TEXT UNIQUE  
- `description` TEXT  

#### `email_categories` (N:M)
- `email_id` FK  
- `category_id` FK  
- `confidence` REAL (0..1) mit CHECK  
- Unique Constraint (email_id, category_id)

#### `email_embeddings`
- `email_id` FK  
- `model` TEXT  
- `dim` INT  
- `vector` VECTOR(dim) (pgvector)  
- optional: `scope`/`field` (z.B. body/summary/subject)  
- Unique Constraint (email_id, model, scope)  
- Index: passend zur Vektorsuche

#### `folders`
- `id` UUID PK  
- `pst_id` FK (auf pst_files) oder String-Key  
- `parent_id` self-FK  
- `name` TEXT  
- `path` TEXT (materialized path)  
- Indexstrategie für Tree + path queries

#### `threads`
- `id` UUID PK  
- `root_message_id` TEXT  
- `subject` TEXT  
- optional: `normalized_subject`  
- Threading-Logik berücksichtigen (Message-ID / In-Reply-To / References)

#### `ollama_config`
- `id` UUID PK  
- `base_url` TEXT  
- `model_name` TEXT  
- `timeout_seconds` INT  
- `enabled` BOOLEAN  
- Statusfelder: `last_check_at`, `last_ok_at`, `last_error`, `latency_ms`, `is_reachable`

#### `pst_files`
- `id` UUID PK  
- `original_name` TEXT  
- `stored_path` TEXT  
- `uploaded_at` TIMESTAMPTZ  
- `status` TEXT (enum-like via CHECK)  
- `processed_count` INT  
- `last_error` TEXT  

### Anforderungen an Suche/Performance
- Volltextsuche über subject + body_text + summary_text (+ sender/recipients optional)
- Filter: Ordner, Kategorie, Zeitraum, Status/Analyse-Flags
- Pagination effizient (keyset pagination bevorzugen oder begründen)
- Semantische Suche über `email_embeddings`
- “Ähnliche E-Mails” Query (cosine/inner product/Euclidean je nach pgvector config)

### Datenqualität & Audit
- Zeitstempel (`created_at`, `updated_at`)
- Soft-delete optional (falls sinnvoll)
- Historisierung optional: `analysis_history` (nur wenn unbedingt nötig, sonst weglassen)

### Output-Format
- Erst DDL komplett in einem Block (SQL)
- Danach kurze Begründung der wichtigsten Designentscheidungen (max 15 Bulletpoints)
- Danach Beispielqueries (SQL)

### Zusätzliche Randbedingungen / Hinweise
- PostgreSQL Extensions: `uuid-ossp`, `pg_trgm`, `vector` (pgvector)
- ORM ist SQLAlchemy 2.0; Migrations via Alembic
- Ziel: robust, sauber normalisiert wo sinnvoll, aber pragmatisch für MVP+Skalierung
- Kein unnötiger Overengineering-Quatsch

**Starte jetzt mit dem Schema.**

---

## Kurz: 5 Stellen, wo dein Plan oft “stille Annahmen” enthält (damit du’s im Prompt direkt mit abdeckst)
Damit du nicht in typische Fallen rennst, hier die wichtigsten Skeptiker-Punkte:

1) **`message_id` ist nicht immer vorhanden/unique.**  
   Manche Exporte/EMLs haben kaputte oder fehlende Message-IDs. Du brauchst eine Fallback-Dedupe-Strategie (Hash über normalized fields).

2) **Recipients als TEXT ist bequem, aber später teuer.**  
   Wenn du je “alle Mails an X” sauber und schnell willst, ist `email_participants` (relation) oft besser als JSONB. (Der Prompt lässt beides zu, aber zwingt zur Begründung.)

3) **Threading ist tricky.**  
   `root_message_id` + `subject` reicht nicht, wenn References/In-Reply-To fehlen oder Betreff driftet. Du willst mindestens: `in_reply_to`, `references` speichern + `normalized_subject`.

4) **Embeddings müssen versionierbar sein.**  
   Modelname + dim + scope + (optional) “chunking_strategy”/“preprocess_version”, sonst mischst du später Äpfel mit Birnen.

5) **Folder Tree**: `parent_id` reicht für Hierarchie, aber `path` (materialized) macht UI/Filter massiv schneller.  
   Dafür brauchst du konsistente Updates (Trigger oder App-Level).

---

Wenn du willst, kann ich dir als nächsten Schritt auch einen **zweiten Prompt** bauen, der aus dem Schema direkt **SQLAlchemy 2.0 Models + Alembic Migration + CRUD-Repos** generieren lässt (und dabei sauber in deine `app/models/` Struktur passt).

### 3. Benutzer

ja

### 4. Assistent

Alles klar — hier ist der **zweite Prompt**, der ein Modell dazu bringt, dir **SQLAlchemy-2.0 ORM-Modelle + Alembic-Migration + DB-Init + minimalen CRUD/Repository-Layer** exakt passend zu deiner Projektstruktur zu erzeugen.

Damit’s nicht weichgespült wird, zwingt der Prompt das Modell auch, **kritische Annahmen offenzulegen** (Recipients-Struktur, Deduping, Threading, Embedding-Versionierung) und sich **für** eine Option zu entscheiden.

---

## Prompt: SQLAlchemy 2.0 + Alembic für E-Mail Wissensdatenbank (aus DDL)

**Rolle/Modus:** Du bist ein Staff Backend Engineer (Python/FastAPI) mit starker PostgreSQL/SQLAlchemy 2.0/Alembic Expertise. Du schreibst produktionsreifen Code, sauber typisiert, nachvollziehbar, testbar.

**Kontext:** Ich baue eine E-Mail Wissensdatenbank (FastAPI) mit Postgres Extensions (`uuid-ossp`, `pg_trgm`, `vector`). Die Projektstruktur ist:

- `main.py` Einstieg
- `app/db/` → `database.py`, `base.py`, `init_db.py`, `migrations/`
- `app/models/` → `email.py`, `category.py`, `embedding.py`, `provider.py`, `analysis_history.py`, `jobs.py`
- `app/schemas/` → Pydantic Schemas
- `app/services/` → Import/Analyse/Suche
- Frontend Jinja2, Volltext + Embeddings Search, “Ähnliche E-Mails”
- Alembic wird genutzt

**Input:** Unten steht mein gewünschtes DB-Schema (DDL). Du sollst daraus SQLAlchemy-Modelle und die Migration erzeugen.

### Aufgabe
Erzeuge folgende Artefakte:

1) **SQLAlchemy 2.0 Modelle** (Mapped/Declarative, typed) in passenden Dateien:
   - `app/models/email.py` (Email, Folder, Thread, EmailCategory relation, Participant falls nötig)
   - `app/models/category.py` (Category)
   - `app/models/embedding.py` (EmailEmbedding)
   - `app/models/provider.py` (OllamaConfig)
   - `app/models/jobs.py` (PstFile + optional Job-Status falls im Schema)
   - Optional: `analysis_history.py` nur wenn im Schema vorgesehen, sonst weglassen

2) **Alembic Migration**:
   - `app/db/migrations/versions/<timestamp>_init_schema.py`
   - Enthält `upgrade()` und `downgrade()`
   - Erst Extensions (falls möglich/erlaubt), dann Tabellen, Constraints, Indizes.
   - Falls Extensions nicht in Alembic laufen sollen: klar markieren + Alternative (manuelles Setup in `init_db.py`).

3) **DB-Setup Code**:
   - `app/db/base.py` (Base/metadata)
   - `app/db/database.py` (engine/sessionmaker async oder sync → entscheide anhand FastAPI, begründe kurz)
   - `app/db/init_db.py` (create extensions if missing, run basic checks)

4) **Repository/CRUD Layer minimal**:
   - `app/services/email_repo.py` oder `app/services/repositories/email_repository.py`
   - Funktionen:
     - `create_email(...)`
     - `get_email(email_id)`
     - `list_emails(filters..., page...)` (Pagination effizient)
     - `search_fulltext(query, filters...)`
     - `search_semantic(vector, filters...)`
     - `similar_emails(email_id, top_k, filters...)`
     - `assign_categories(email_id, categories_with_confidence)`
     - `upsert_embedding(email_id, model, scope, vector)`
   - Verwende SQLAlchemy Core/ORM sinnvoll (kein Spaghetti)

5) **Pydantic Schemas (minimal)**:
   - `app/schemas/email_data.py` (EmailRead, EmailListItem, EmailCreate)
   - `app/schemas/search.py` (SearchRequest, SearchResponse)
   - Nur das, was für API & Templates nötig ist.

### Harte Anforderungen
- SQLAlchemy 2.0 style (`Mapped[...]`, `mapped_column`, `relationship`)
- UUID PKs
- Constraints und Indizes aus dem DDL müssen in ORM/Migration abgebildet werden
- Fulltext: `search_vector` wird korrekt gesetzt (Trigger oder generated column). Wenn Trigger: liefere Trigger-Definition in Migration.
- pgvector: `vector` column korrekt typisiert (nutze pgvector SQLAlchemy type, oder fallback via `sqlalchemy.dialects.postgresql` + `TypeDecorator`)
- `email_categories.confidence` CHECK 0..1
- Dedupe: Unique auf `message_id` **nur wenn** du mit fehlenden/kaputten IDs umgehen kannst → ansonsten alternative Dedupe-Strategie implementieren (z.B. `content_hash` + partial unique index). Entscheide und erkläre.
- Threading: speichere `in_reply_to` und `references` in Emails (References als TEXT[] oder JSONB). Entscheide und begründe.
- Recipients: entscheide zwischen
  A) JSONB in `emails.recipients` oder
  B) normalisierte Tabelle `email_participants`
  Nutze die Option, die langfristig bessere Filter/Performance bietet, und erkläre.
- Folder tree: `folders.parent_id` plus `folders.path` (materialized). Erzeuge Indizes für schnelle path queries.
- Statusfelder: `pst_files.status` und `ollama_config` Statusfelder mit sinnvollen defaults.
- Zeitstempel: `created_at`, `updated_at` (server_default + onupdate)

### Output-Format
- Liefere Code **dateiweise**, jeweils mit einem klaren Header:
  - `# app/models/email.py`
  - `# app/db/migrations/versions/...py`
  - usw.
- Kein Platzhalter-Geblabber — vollständig ausführbarer Code.
- Kurze “Design Notes” am Ende (max 12 Bulletpoints).

### Mein DDL (Quelle der Wahrheit)
[HIER DDL EINFÜGEN — falls nicht vorhanden, generiere es selbst sauber passend zum Masterplan, aber markiere das klar.]

**Starte jetzt.**

---

## Mini-Sparring: ein wichtiger Punkt, bevor du den Prompt nutzt
Du schreibst “DDL ist Quelle der Wahrheit”, aber im selben Prompt erlaubst du “generiere DDL selbst”. Das ist eine klassische Lücke: Das Modell erfindet dann gern Dinge.

**Besser:** Wenn du das DDL schon hast, **immer einfügen**. Wenn nicht, dann sag explizit: “Erzeuge zuerst DDL und warte auf mein OK” — *aber* du willst ja keine Rückfragen/Iterationen.

Pragmatischer Weg: Lass es **DDL + Code in einem Rutsch** generieren (wie dein 1. Prompt) und nimm es als Draft.

---

Wenn du willst, kann ich dir noch eine **“Super-Prompt”-Variante** machen, die:
- direkt zu deiner bestehenden Struktur passt (async/sync, Jinja2 Listen/Detail, Filterfelder),
- und zusätzlich **2–3 Alembic-Revisions** splitten lässt (extensions → core tables → search/vector indexes), was im Alltag deutlich angenehmer ist.

### 5. Benutzer

ja

### 6. Assistent

Nice — dann bekommst du jetzt die **Super-Prompt-Variante** (ein Prompt, der *alles* in einem Rutsch erzeugt: **DDL + Alembic-Revisions + SQLAlchemy 2.0 Modelle + Repos + Pydantic Schemas + 3–5 Beispielqueries**, sauber auf deine Struktur gemappt).

Ich baue ihn so, dass das Modell **nicht ausweicht**: es muss Entscheidungen treffen (Recipients normalisiert vs JSONB, Deduping, Threading, Embedding-Versionierung) und die Entscheidungen kurz begründen. Außerdem: **3 Alembic-Revisions** (Extensions → Core → Search/Vector Indexes), weil das in der Praxis weniger Schmerz ist.

---

## Super-Prompt: End-to-End DB + ORM + Migration + Repo + Schemas (E-Mail Wissensdatenbank)

**Rolle/Modus:** Du bist ein Staff Backend Engineer + Postgres Architect. Du lieferst produktionsreife Lösungen, keine Skizzen.

**Ziel:** Implementiere die komplette Datenbank-Schicht für eine E-Mail-Wissensdatenbank (MVP→Prod) passend zur folgenden Projektstruktur:

- `app/db/` → `database.py`, `base.py`, `init_db.py`, `migrations/`
- `app/models/` → `email.py`, `category.py`, `embedding.py`, `provider.py`, `jobs.py` (optional `analysis_history.py`)
- `app/schemas/` → `email_data.py`, `search.py`, `provider.py`
- `app/services/` → Repositories (z.B. `email_repo.py`, `search_repo.py`, `admin_repo.py`)
- FastAPI + Jinja2 Templates, Filter/Pagination, Volltext- & Semantik-Suche, “Ähnliche E-Mails”

**Technik/DB:**
- PostgreSQL
- Extensions: `uuid-ossp`, `pg_trgm`, `vector` (pgvector)
- ORM: SQLAlchemy 2.0
- Migrations: Alembic

---

# 1) Anforderungen (Quelle der Wahrheit)

## Tabellen (müssen existieren)
- `emails`
- `categories`
- `email_categories`
- `email_embeddings`
- `folders`
- `threads`
- `ollama_config`
- `pst_files`

## Pflicht-Features
- Dedupe / Duplikaterkennung robust auch ohne `message_id`
- Fulltextsuche (subject + body_text + summary_text + sender/recipients sinnvoll)
- Trigram-Index für fuzzy search (pg_trgm) auf subject/sender
- Semantische Suche via pgvector (Index + Query)
- “Ähnliche E-Mails”
- Folder-Hierarchie (parent_id + path/materialized path)
- Threading (in_reply_to + references + normalized_subject)
- Statusfelder & Zeitstempel (created_at, updated_at)
- Alembic: 3 Revisions (Extensions → Core Tables → Search/Vector Indexes)

---

# 2) Kritische Design-Entscheidungen (du MUSST wählen)

## A) Recipients Modellierung (wähle GENAU eine Option)
1) **Normalisiert:** Tabelle `email_participants` (recommended für Filter/Performance)
2) **JSONB/Array:** `emails.recipients` als JSONB oder TEXT[]

**Du musst dich entscheiden, begründen (3–5 Sätze), und den Code entsprechend bauen.**

## B) Dedupe-Strategie (Pflicht)
- `message_id` kann fehlen oder kaputt sein.
- Implementiere:
  - `message_id` optional + **partial unique index** wo sinnvoll
  - zusätzlich `content_hash` (SHA256 o.ä.) auf normalisierten Feldern (subject/sender/recipients/sent_date/body_text gekürzt)  
  - **Unique Constraint/Index** auf `content_hash` (evtl. mit Partial/Scope)

**Du musst Dedupe so bauen, dass PST/EML Import stabil ist.**

## C) Embeddings Versionierung (Pflicht)
- In `email_embeddings`: `model`, `dim`, `scope` (subject/body/summary), plus optional `preprocess_version` oder `chunk_strategy`.
- Unique: `(email_id, model, scope, preprocess_version)`.

---

# 3) Was du ausgeben sollst (Output)

Du lieferst **vollständigen Code**, dateiweise, ohne Platzhalter.

## 3.1 DDL (SQL)
- `CREATE EXTENSION IF NOT EXISTS ...`
- `CREATE TABLE ...`
- Constraints, Indizes (inkl. GIN/TSVECTOR, trigram, vector index)
- Fulltext Setup:
  - entweder generated column oder Trigger (empfohlen, weil multi-language + concatenation flexibler)
- Materialized path: `folders.path` + Index (btree oder gin mit trigram, je nach Ansatz)

## 3.2 Alembic Migrations (3 Revisions)
1) `xxxx_001_enable_extensions.py`
2) `xxxx_002_create_core_tables.py`
3) `xxxx_003_create_search_and_vector_indexes.py`

Jede Revision mit sauberem `upgrade()` / `downgrade()`.

## 3.3 SQLAlchemy 2.0 Modelle
Dateien:
- `app/models/email.py` (Email, Folder, Thread, EmailCategory, + ggf Participants)
- `app/models/category.py`
- `app/models/embedding.py`
- `app/models/provider.py` (OllamaConfig)
- `app/models/jobs.py` (PstFile)

## 3.4 DB Setup
- `app/db/base.py`
- `app/db/database.py` (entscheide async/sync und begründe kurz – FastAPI + BackgroundTasks)
- `app/db/init_db.py` (basic checks + extension creation if needed)

## 3.5 Repositories (minimal, aber brauchbar)
- `app/services/email_repo.py`
- `app/services/search_repo.py`

Funktionen:
- `create_email(...)` (inkl. dedupe)
- `get_email(email_id)`
- `list_emails(filters, pagination)` (bevorzugt keyset pagination; wenn offset, begründe)
- `search_fulltext(query, filters, pagination)`
- `search_semantic(query_vector, filters, top_k)`
- `similar_emails(email_id, top_k, filters)`
- `assign_categories(email_id, categories_with_confidence)`
- `upsert_embedding(email_id, model, scope, preprocess_version, vector)`

## 3.6 Pydantic Schemas (minimal)
- `app/schemas/email_data.py`: EmailRead, EmailListItem, EmailCreate, CategoryBadge, FolderRef, ThreadRef
- `app/schemas/search.py`: SearchRequest, SearchHit, SearchResponse

## 3.7 Beispielqueries (SQL)
- Volltextsuche mit Filters
- Semantische Suche (vector distance)
- Ähnliche E-Mails
- Folder path query
- Thread query

## 3.8 Design Notes
Max 12 Bulletpoints.

---

# 4) Stil & Qualität
- Python 3.11+ kompatibel
- Typing überall
- Kein “TODO”, keine Platzhalter
- Keine unnötigen Frameworks
- Indizes und Constraints müssen realistisch & konsistent sein
- Vermeide overengineering, aber keine MVP-Schlamperei

---

# 5) Start
Erzeuge zuerst das DDL, danach die 3 Alembic-Revisions, danach Models, dann DB-Setup, dann Repos, dann Schemas, dann Queries, dann Design Notes.

**Los geht’s.**

---

## Noch ein kurzer Sparring-Hinweis (damit du nicht in eine Falle tappst)
Du hast aktuell im Masterplan “Volltextsuche mit PostgreSQL Full-Text-Search” und “pg_trgm” und “Embeddings”. Eine typische Fehlannahme ist: *“Ich mache einfach alles gleichzeitig und es wird automatisch gut.”*  
In der Realität brauchst du **klare Prioritäten**, sonst bekommst du drei Suchsysteme, die sich widersprechen.

Wenn du das vermeiden willst, ergänze am Ende des Prompts noch 1 Satz:

> “Definiere eine klare Ranking-Strategie: FTS als Basis, trigram für Tippfehler, vector für semantische Erweiterung — und gib eine empfohlene Kombi-Strategie (z.B. RRF oder staged retrieval).”

Wenn du willst, formuliere ich dir genau diesen Zusatz noch “bulletproof”, passend zu deinem UI (Filter+Pagination) und deinen Endpoints.
