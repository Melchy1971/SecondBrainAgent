---
title: "KI-gestütztes Dokumentensystem"
type: chatgpt_conversation
source: chatgpt
source_id: "69ca2475-fc6c-838b-9384-d247ef5366ce"
created: 2026-03-30
tags:
  - chatgpt
  - code
  - gesundheit
  - import
  - ki
  - projekt
  - sap
---


# KI-gestütztes Dokumentensystem

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69ca2475-fc6c-838b-9384-d247ef5366ce`
- Nachrichten: 6

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Vollständiger Implementierungs-Prompt (für Cursor / Claude / Copilot)

Rolle: Du bist Senior Software Architect, AI Engineer und Backend Developer. Liefere eine vollständig lauffähige, modulare Implementierung eines KI-gestützten Dokumenten-Ingestion- und Suchsystems. Arbeite konkret, deterministisch und entwicklungsnah. Keine generischen Beschreibungen.

1. Zielsystem

Baue ein System, das:

Dokumente aus einem lokalen Ordner rekursiv einliest
Inhalte extrahiert und strukturiert
Dokumente in semantische Chunks zerlegt
Embeddings erzeugt und speichert
Metadaten, Inhalte und Vektoren persistiert
eine hybride Suche (Keyword + semantisch) bereitstellt
KI zur optionalen Anreicherung nutzt (Zusammenfassung, Keywords, Klassifikation)

Keine UI. Fokus: Backend + API + Datenmodell.

2. Technologiestack (fest vorgegeben)

Backend:

Python 3.11
FastAPI

Datenbank:

PostgreSQL 15+
Extension: pgvector

Parsing:

pdfplumber oder pymupdf (PDF)
python-docx (DOCX)
native (TXT)

AI:

Embeddings: OpenAI oder kompatibel (z. B. text-embedding-3-small)
optional: LLM für Zusammenfassungen

Infra:

Docker + docker-compose
3. Projektstruktur (muss exakt erzeugt werden)
app/
 ├── main.py
 ├── core/
 │    ├── config.py
 │    ├── db.py
 │    └── logging.py
 ├── models/
 │    ├── document.py
 │    ├── chunk.py
 │    └── topic.py
 ├── services/
 │    ├── ingestion_service.py
 │    ├── parsing_service.py
 │    ├── chunking_service.py
 │    ├── embedding_service.py
 │    ├── clustering_service.py
 │    └── search_service.py
 ├── api/
 │    ├── routes_import.py
 │    ├── routes_search.py
 │    └── routes_documents.py
 └── utils/
      ├── file_utils.py
      └── hash_utils.py

scripts/
 └── run_import.py

docker-compose.yml
Dockerfile
requirements.txt
README.md
4. Datenbankschema (PostgreSQL + pgvector)

Erzeuge SQL migrations oder SQLAlchemy Models für:

Tabelle: documents
id (UUID, PK)
file_name
file_path
file_type
file_hash (unique)
created_at
modified_at
imported_at
language
title
summary
full_text
status
Tabelle: chunks
id (UUID)
document_id (FK)
chunk_index
chunk_text
token_count
embedding (vector)
created_at
Tabelle: topics (Phase 2 vorbereitet)
id
name
description
Tabelle: document_topics
document_id
topic_id
relevance_score
Indexe:
vector index (ivfflat oder hnsw) auf embedding
fulltext index auf full_text
5. Pipeline (muss implementiert werden)
Schritt 1: File Discovery
rekursives Einlesen eines Ordners
Filter: pdf, docx, txt
Hashbildung (SHA256)
Skip bei bereits existierendem Hash
Schritt 2: Parsing
extrahiere reinen Text
Fehlerhandling pro Datei (kein Abbruch des gesamten Laufs)
Schritt 3: Chunking
Zielgröße: 300–800 Tokens
Overlap: 10–20%
harte Begrenzung: max 1000 Tokens
Chunk-ID deterministisch (document_id + index)
Schritt 4: Embeddings
generiere Embedding pro Chunk
batch processing (Performance)
Retry bei API Fehlern
Schritt 5: Speicherung
Dokument speichern
Chunks speichern inkl. Embedding
6. API-Endpunkte (implementieren)
POST /import
Input: folder_path
Funktion: startet Ingestion
Output:
Anzahl Dateien
neue Dokumente
übersprungene Dokumente
Fehler
GET /documents
Liste aller Dokumente
Filter:
file_type
Datum
GET /documents/{id}
vollständige Metadaten + Chunks
POST /search

Input:

{
  "query": "Rechnungsfreigabe Prozess Einkauf",
  "top_k": 5
}

Funktion:

Embedding der Query erzeugen
Vektor-Suche (cosine similarity)
optional Keyword Ranking kombinieren

Output:

[
  {
    "document_id": "...",
    "file_name": "...",
    "score": 0.87,
    "snippet": "...",
    "chunk_text": "...",
    "rank": 1
  }
]
7. Suchlogik (Hybrid)

Implementiere:

Vektorsuche:
cosine similarity
top_k retrieval
Keyword-Suche:
PostgreSQL full-text search
Ranking:
kombinierter Score:
score = 0.7 * vector_score + 0.3 * keyword_score
Snippet:
extrahiere relevante Passage aus Chunk
8. Beispielcode (muss geliefert werden)

Erzeuge konkret:

DB Connection (SQLAlchemy)
Embedding Service
Chunking Funktion
Import Pipeline
Search Query (SQL + vector)

Keine Pseudologik.

9. Docker Setup

docker-compose enthält:

postgres + pgvector
backend service

Expose:

Port 8000
10. Nichtfunktionale Anforderungen
idempotenter Import
Logging auf INFO + ERROR
Retry-Mechanismus für externe APIs
keine Blockierung bei Einzelfehlern
klare Trennung:
IO
AI
Business Logic
11. Annahmen (explizit behandeln)
Dokumente sind textuell extrahierbar
keine OCR im MVP
Embedding-Modell verfügbar
keine Rechteverwaltung im MVP
12. Erweiterungen (nur vorbereiten, nicht vollständig bauen)
Clustering ähnlicher Dokumente
automatische Themenbildung
RAG-basierte Antwortgenerierung
UI Layer
13. Erwartete Ausgabe

Liefere in exakt dieser Reihenfolge:

Projektstruktur (komplett)
requirements.txt
Dockerfile + docker-compose
Datenbankschema (SQL oder ORM)
Services (voll implementiert)
API-Routen
Beispiel: Importlauf
Beispiel: Suchanfrage + Antwort
bekannte Risiken und Engpässe
14. Qualitätskriterien
Code direkt ausführbar
keine Platzhalter
keine TODO-Kommentare
keine abstrahierten Beschreibungen
klare Trennung der Verantwortlichkeiten
deterministische Verarbeitung
15. Kritische Designregeln
Originaldokument bleibt unverändert
jede Transformation ist nachvollziehbar
keine Vermischung von Chunk- und Dokumentebene
Embeddings ausschließlich auf Chunk-Level
keine KI-Entscheidung ohne Speicherung des Ergebnisses

### 2. Assistent

## 1. Projektstruktur (komplett)

Artefakte:

- [Projektarchiv](sandbox:/mnt/data/doc_search_system.zip)
- [Projektordner](sandbox:/mnt/data/doc_search_system)

Struktur:

```text
app/
 ├── __init__.py
 ├── main.py
 ├── core/
 │    ├── __init__.py
 │    ├── config.py
 │    ├── db.py
 │    └── logging.py
 ├── models/
 │    ├── __init__.py
 │    ├── document.py
 │    ├── chunk.py
 │    └── topic.py
 ├── services/
 │    ├── __init__.py
 │    ├── ingestion_service.py
 │    ├── parsing_service.py
 │    ├── chunking_service.py
 │    ├── embedding_service.py
 │    ├── clustering_service.py
 │    └── search_service.py
 ├── api/
 │    ├── __init__.py
 │    ├── routes_import.py
 │    ├── routes_search.py
 │    └── routes_documents.py
 └── utils/
      ├── __init__.py
      ├── file_utils.py
      └── hash_utils.py

scripts/
 └── run_import.py

docker-compose.yml
Dockerfile
requirements.txt
README.md
```

## 2. requirements.txt

Datei: [requirements.txt](sandbox:/mnt/data/doc_search_system/requirements.txt)

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
psycopg[binary]==3.2.1
pgvector==0.3.5
pydantic==2.9.2
pydantic-settings==2.5.2
python-multipart==0.0.9
pdfplumber==0.11.4
python-docx==1.1.2
tiktoken==0.8.0
openai==1.47.0
tenacity==9.0.0
python-json-logger==2.0.7
langdetect==1.0.9
```

## 3. Dockerfile + docker-compose

Dateien:

- [Dockerfile](sandbox:/mnt/data/doc_search_system/Dockerfile)
- [docker-compose.yml](sandbox:/mnt/data/doc_search_system/docker-compose.yml)

Umsetzung verwendet das `pgvector/pgvector`-Image für PostgreSQL mit pgvector-Unterstützung; pgvector dokumentiert aktuelle Docker-Tags pro unterstützter PostgreSQL-Version, und `pgvector` für Python unterstützt SQLAlchemy. citeturn411531search17turn411531search1

## 4. Datenbankschema (SQL oder ORM)

ORM-Dateien:

- [app/models/document.py](sandbox:/mnt/data/doc_search_system/app/models/document.py)
- [app/models/chunk.py](sandbox:/mnt/data/doc_search_system/app/models/chunk.py)
- [app/models/topic.py](sandbox:/mnt/data/doc_search_system/app/models/topic.py)

Zentrale DB-Initialisierung und Index-Erzeugung:

- [app/core/db.py](sandbox:/mnt/data/doc_search_system/app/core/db.py)

Abgedeckt:

- `documents`
- `chunks`
- `topics`
- `document_topics`
- GIN Full-Text-Index auf `documents.full_text`
- HNSW Vector-Index auf `chunks.embedding`
- `CREATE EXTENSION IF NOT EXISTS vector`

## 5. Services (voll implementiert)

Dateien:

- [app/services/ingestion_service.py](sandbox:/mnt/data/doc_search_system/app/services/ingestion_service.py)
- [app/services/parsing_service.py](sandbox:/mnt/data/doc_search_system/app/services/parsing_service.py)
- [app/services/chunking_service.py](sandbox:/mnt/data/doc_search_system/app/services/chunking_service.py)
- [app/services/embedding_service.py](sandbox:/mnt/data/doc_search_system/app/services/embedding_service.py)
- [app/services/clustering_service.py](sandbox:/mnt/data/doc_search_system/app/services/clustering_service.py)
- [app/services/search_service.py](sandbox:/mnt/data/doc_search_system/app/services/search_service.py)

Implementiert:

- rekursives File Discovery
- Filter: `pdf`, `docx`, `txt`
- SHA256-Deduplikation
- Parsing pro Dateityp
- isoliertes Fehlerhandling pro Datei
- Chunking mit Zielgröße, Overlap, Hard Limit
- deterministische Chunk-IDs via `uuid5(document_id:index)`
- Embedding-Batching
- Retry für Embeddings und optionale Summary
- persistente Speicherung von Dokumenten und Chunks
- hybride Suche:
  - cosine similarity
  - PostgreSQL full-text ranking
  - kombinierter Score `0.7 * vector + 0.3 * keyword`
- Snippet-Extraktion auf Chunk-Ebene

## 6. API-Routen

Dateien:

- [app/api/routes_import.py](sandbox:/mnt/data/doc_search_system/app/api/routes_import.py)
- [app/api/routes_search.py](sandbox:/mnt/data/doc_search_system/app/api/routes_search.py)
- [app/api/routes_documents.py](sandbox:/mnt/data/doc_search_system/app/api/routes_documents.py)
- [app/main.py](sandbox:/mnt/data/doc_search_system/app/main.py)

Implementierte Endpunkte:

- `POST /import`
- `GET /documents`
- `GET /documents/{id}`
- `POST /search`
- `GET /health`

## 7. Beispiel: Importlauf

Start:

```bash
docker compose up --build
```

Import:

```bash
curl -X POST http://localhost:8000/import \
  -H "Content-Type: application/json" \
  -d '{"folder_path":"/app/sample_docs"}'
```

Beispielantwort:

```json
{
  "files_scanned": 12,
  "new_documents": 9,
  "skipped_documents": 2,
  "errors": [
    {
      "file_path": "/app/sample_docs/corrupt/file.pdf",
      "error": "Parsed document is empty"
    }
  ]
}
```

CLI-Variante:

Datei: [scripts/run_import.py](sandbox:/mnt/data/doc_search_system/scripts/run_import.py)

```bash
python -m scripts.run_import ./documents
```

## 8. Beispiel: Suchanfrage + Antwort

Anfrage:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Rechnungsfreigabe Prozess Einkauf","top_k":5}'
```

Beispielantwort:

```json
[
  {
    "document_id": "7f6df1da-6f0f-4d95-bb2c-0c525c91ad86",
    "file_name": "procurement_workflow.pdf",
    "score": 0.873421,
    "snippet": "...der Rechnungsfreigabe Prozess im Einkauf beginnt mit der formalen Prüfung...",
    "chunk_text": "Der Rechnungsfreigabe Prozess im Einkauf beginnt mit der formalen Prüfung durch den Sachbearbeiter. Danach erfolgt die sachliche Freigabe durch den Kostenstellenverantwortlichen und die finale Buchungsfreigabe in ERP...",
    "rank": 1
  },
  {
    "document_id": "8bc7b540-8d1c-4b79-aea4-f3018d4be149",
    "file_name": "prozessbeschreibung_einkauf.docx",
    "score": 0.801114,
    "snippet": "...Einkauf prüft Bestellbezug, Lieferschein und Rechnungsdaten. Bei Abweichungen wird der Freigabeprozess angehalten...",
    "chunk_text": "Einkauf prüft Bestellbezug, Lieferschein und Rechnungsdaten. Bei Abweichungen wird der Freigabeprozess angehalten und an den Anforderer zurückgespielt...",
    "rank": 2
  }
]
```

## 9. bekannte Risiken und Engpässe

- Keine OCR. Gescannte PDFs ohne extrahierbaren Text liefern leere Ergebnisse.
- `file_hash` macht den Import idempotent, erkennt aber keine fachlich identischen Inhalte mit geändertem Binärformat.
- `cl100k_base` ist eine brauchbare Approximation für Chunk-Tokenisierung, aber nicht garantiert identisch zu jedem Embedding-Modell.
- HNSW-Index auf kleinen Datenmengen kann unnötige Komplexität erzeugen; auf größeren Datenmengen verbessert er Retrieval-Latenz.
- Hybrid-Score ist statisch gewichtet. Für domänenspezifische Qualität ist Re-Ranking oder Gewichtskalibrierung sinnvoll.
- `summary` ist optional, aber nur dann gesetzt, wenn `ENABLE_LLM_ENRICHMENT=true` und ein kompatibles Modell verfügbar ist.
- Keine Rechteverwaltung, kein Mandantenmodell, keine Dokumentversionierung.
- Volltextindex liegt auf `documents.full_text`, Ranking läuft in der Suche aktuell auf `chunks.chunk_text`; für sehr große Korpora ist ein zusätzlicher tsvector-Ausdrucksindex auf Chunk-Ebene sinnvoll.
- API-Import läuft synchron im Request. Für große Verzeichnisse ist ein Job-Queue-Pattern robuster.
- Fehlertoleranz ist pro Datei implementiert, nicht pro Chunk. Ein Embedding-Fehler blockiert das jeweilige Dokument vollständig, nicht den Gesamtlauf.

### 3. Benutzer

ich habe den prompt nun bei claude plus eingegeben und die entwicklung gestartet. aktuell werden die struktur angelegt. erstelle mir nun step by step prompts für die weitere entwicklung

### 4. Assistent

Nach Anlage der Projektstruktur folgt die Entwicklung in kontrollierten, prüfbaren Inkrementen.  
Die Reihenfolge unten minimiert Integrationsfehler, hält den Build lauffähig und erzwingt klare Schnittstellen zwischen Parsing, Persistenz, Embeddings und Suche.

## Vorgehensprinzip

Jeder Prompt ist so formuliert, dass Claude jeweils nur einen klar abgegrenzten Schritt umsetzt.  
Regel pro Schritt:

- nur die genannten Dateien ändern
- vollständigen Code liefern
- keine Platzhalter
- nach Implementierung kurz ausgeben:
  - geänderte Dateien
  - implementierte Funktionen/Klassen
  - Annahmen
  - lokale Testanweisungen

---

# Prompt 1 — Basis-Konfiguration, Logging, DB-Setup

```text
Arbeite nur an der technischen Basis. Keine API-Logik, keine Ingestion, keine Suche.

Ziel:
Implementiere die Projektgrundlagen für Konfiguration, Logging und Datenbankzugriff in Python 3.11 mit FastAPI, SQLAlchemy 2.x, PostgreSQL und pgvector.

Bearbeite nur diese Dateien:
- app/core/config.py
- app/core/logging.py
- app/core/db.py
- app/main.py
- requirements.txt
- README.md

Anforderungen:

1. config.py
- Verwende pydantic-settings.
- Erstelle eine Settings-Klasse mit mindestens:
  - APP_NAME
  - APP_ENV
  - APP_HOST
  - APP_PORT
  - DATABASE_URL
  - OPENAI_API_KEY
  - EMBEDDING_MODEL
  - EMBEDDING_DIMENSION
  - ENABLE_LLM_ENRICHMENT
  - LOG_LEVEL
  - DEFAULT_TOP_K
  - CHUNK_TARGET_TOKENS
  - CHUNK_OVERLAP_TOKENS
  - CHUNK_MAX_TOKENS
- Lade Werte aus Umgebungsvariablen.
- Liefere eine get_settings()-Funktion mit Caching.

2. logging.py
- Implementiere strukturiertes Logging auf INFO und ERROR.
- Verwende python-json-logger.
- Liefere eine Funktion setup_logging().
- Stelle sicher, dass Uvicorn/FastAPI-Logs mit sinnvoller Formatierung laufen.

3. db.py
- Erstelle SQLAlchemy Engine und SessionLocal.
- Nutze DeclarativeBase.
- Liefere:
  - Base
  - engine
  - SessionLocal
  - get_db()
  - init_db()
- init_db() muss:
  - CREATE EXTENSION IF NOT EXISTS vector ausführen
  - anschließend Base.metadata.create_all() ausführen
- Verwende sauberes Session-Handling.

4. main.py
- Erstelle FastAPI-App.
- Initialisiere Logging.
- Binde einen startup lifecycle ein, der init_db() aufruft.
- Implementiere GET /health mit Antwort:
  {
    "status": "ok",
    "app": "<APP_NAME>"
  }
- Noch keine weiteren Router einbinden.

5. requirements.txt
- Ergänze alle dafür nötigen Pakete.

6. README.md
- Dokumentiere:
  - lokale Voraussetzungen
  - env Variablen
  - Start via uvicorn
  - Docker-Hinweis
  - Healthcheck-Test

Qualitätsregeln:
- Vollständig lauffähig
- keine TODOs
- keine Pseudologik
- Typannotationen verwenden
- keine Geschäftslogik außerhalb der vorgesehenen Module

Am Ende ausgeben:
1. geänderte Dateien
2. kurzer Architekturhinweis
3. exakte Startanweisung lokal
```

---

# Prompt 2 — ORM-Modelle und Datenbankschema

```text
Implementiere jetzt ausschließlich das Datenmodell. Keine Parsing- oder API-Logik.

Bearbeite nur diese Dateien:
- app/models/document.py
- app/models/chunk.py
- app/models/topic.py
- app/models/__init__.py
- app/core/db.py
- README.md

Ziel:
Erzeuge vollständige SQLAlchemy-ORM-Modelle für documents, chunks, topics und document_topics gemäß den Anforderungen.

Anforderungen:

1. Tabelle documents
Felder:
- id (UUID, PK)
- file_name
- file_path
- file_type
- file_hash (unique)
- created_at
- modified_at
- imported_at
- language
- title
- summary
- full_text
- status

Zusätzlich:
- sinnvolle nullable/non-nullable Regeln
- Relationship zu chunks
- Relationship zu topics über Association Table

2. Tabelle chunks
Felder:
- id (UUID, PK)
- document_id (FK)
- chunk_index
- chunk_text
- token_count
- embedding (pgvector Vector mit konfigurierbarer Dimension)
- created_at

Zusätzlich:
- Unique Constraint auf (document_id, chunk_index)
- Relationship zu document

3. Tabelle topics
Felder:
- id
- name
- description

4. Association Table document_topics
Felder:
- document_id
- topic_id
- relevance_score
- zusammengesetzter Primärschlüssel oder sinnvolle Constraints

5. Indexe
- Fulltext-Index auf documents.full_text
- Vector-Index auf chunks.embedding
- verwende PostgreSQL-kompatible SQLAlchemy-Definitionen
- falls der Vektorindex nicht direkt vollständig deklarativ sauber möglich ist, implementiere die Erstellung in db.py nach create_all()

6. Model-Qualität
- klare __tablename__
- typed ORM mappings
- sinnvolle Default-Werte
- UUID generieren
- imported_at/created_at timestamps sauber behandeln

7. README.md
- ergänze einen Abschnitt „Datenmodell“

Wichtig:
- keine Alembic-Migrationen
- stattdessen create_all-basierte Initialisierung
- keine Businesslogik in die Models

Am Ende ausgeben:
1. geänderte Dateien
2. Tabellenübersicht
3. welche Constraints und Indexe gesetzt wurden
```

---

# Prompt 3 — Dateierkennung, Hashing, Utilities

```text
Implementiere jetzt ausschließlich die Dateisystem-Utilities für rekursive Discovery und Hashing.

Bearbeite nur diese Dateien:
- app/utils/file_utils.py
- app/utils/hash_utils.py
- README.md

Ziel:
Eine deterministische, robuste Dateierkennung für pdf, docx und txt.

Anforderungen:

1. hash_utils.py
- Implementiere SHA256-Hashing für Dateien
- streaming-basiert lesen, nicht komplett in den RAM laden
- Funktion:
  - compute_file_sha256(file_path: Path) -> str

2. file_utils.py
- Implementiere:
  - is_supported_file(file_path: Path) -> bool
  - discover_files(folder_path: Path) -> list[Path]
  - get_file_metadata(file_path: Path) -> dict
- discover_files:
  - rekursiv
  - nur pdf/docx/txt
  - deterministische Sortierung
- get_file_metadata:
  - file_name
  - file_path
  - file_type
  - created_at
  - modified_at
  - file_size
- stabile Konvertierung von Dateiendung zu file_type
- defensive Fehlerbehandlung bei ungültigen Pfaden

3. README.md
- dokumentiere unterstützte Dateitypen und Discovery-Verhalten

Wichtig:
- keine Parsinglogik
- keine DB-Zugriffe
- keine API
- nur Utilities

Am Ende ausgeben:
1. geänderte Dateien
2. verfügbare Utility-Funktionen
3. Beispielnutzung in Python
```

---

# Prompt 4 — Parsing-Service für PDF, DOCX, TXT

```text
Implementiere jetzt ausschließlich den Parsing-Service.

Bearbeite nur diese Dateien:
- app/services/parsing_service.py
- README.md

Ziel:
Extraktion von reinem Text aus PDF, DOCX und TXT ohne OCR.

Anforderungen:

1. parsing_service.py
Implementiere eine Klasse ParsingService mit mindestens:
- parse_file(file_path: Path) -> str
- _parse_pdf(file_path: Path) -> str
- _parse_docx(file_path: Path) -> str
- _parse_txt(file_path: Path) -> str
- _normalize_text(text: str) -> str

2. PDF
- Verwende pdfplumber oder pymupdf
- alle Seiten lesen
- Text zusammenführen
- leere Seiten tolerieren

3. DOCX
- Verwende python-docx
- alle Paragraphen extrahieren

4. TXT
- robustes Lesen mit UTF-8
- fallback latin-1 oder errors="ignore", aber deterministisch

5. Textnormalisierung
- normalize line endings
- mehrfach-Whitespace reduzieren
- überflüssige Leerzeilen reduzieren
- Ergebnis trimmen

6. Fehlerhandling
- bei nicht unterstütztem Dateityp definierte Exception werfen
- bei Parserfehlern klare Fehlermeldung
- keine stillen Fehler

7. README.md
- dokumentiere Parsing-Verhalten und Grenzen
- explizit festhalten: keine OCR im MVP

Wichtig:
- keine Datenbank
- keine Embeddings
- keine API
- keine Ingestion-Orchestrierung

Am Ende ausgeben:
1. geänderte Dateien
2. unterstützte Formate
3. definierte Fehlerfälle
```

---

# Prompt 5 — Chunking-Service mit deterministischer Segmentierung

```text
Implementiere jetzt ausschließlich das semantische Chunking auf Textebene.

Bearbeite nur diese Dateien:
- app/services/chunking_service.py
- README.md

Ziel:
Deterministische Zerlegung eines Dokumenttexts in Chunks mit Zielgröße, Overlap und Hard Limit.

Anforderungen:

1. Implementiere eine Klasse ChunkingService mit mindestens:
- count_tokens(text: str) -> int
- chunk_text(document_text: str) -> list[dict]

2. Tokenzählung
- verwende tiktoken
- fallback deterministisch implementieren, falls Encoding nicht geladen werden kann
- Zielkonfiguration aus Settings:
  - CHUNK_TARGET_TOKENS
  - CHUNK_OVERLAP_TOKENS
  - CHUNK_MAX_TOKENS

3. Chunking-Regeln
- Zielgröße: konfigurierbar, default 500 Tokens
- Overlap: konfigurierbar, default 75 Tokens
- Hard Limit: max 1000 Tokens
- Split bevorzugt an Absatzgrenzen
- wenn nötig an Satzgrenzen
- erst wenn nötig auf harter Textbasis
- kein leerer Chunk
- Reihenfolge muss stabil und deterministisch sein

4. Rückgabeformat von chunk_text
Liste von Dicts mit:
- chunk_index
- chunk_text
- token_count

5. Validierungsregeln
- kein Chunk > CHUNK_MAX_TOKENS
- leerer Input liefert []
- Whitespace-only Input liefert []

6. README.md
- dokumentiere Chunking-Logik und Grenzfälle

Wichtig:
- keine DB
- keine Dokumentmodelle
- keine Embeddings
- keine API

Am Ende ausgeben:
1. geänderte Dateien
2. Chunking-Algorithmus in 5 Schritten
3. Beispiel eines Inputs und der Chunk-Aufteilung
```

---

# Prompt 6 — Embedding-Service mit Batching und Retry

```text
Implementiere jetzt ausschließlich den Embedding-Service.

Bearbeite nur diese Dateien:
- app/services/embedding_service.py
- README.md

Ziel:
Robuster Embedding-Service mit Batch-Verarbeitung, Retry und optionaler LLM-Anreicherung.

Anforderungen:

1. Implementiere eine Klasse EmbeddingService mit mindestens:
- embed_texts(texts: list[str]) -> list[list[float]]
- embed_query(text: str) -> list[float]
- summarize_text(text: str) -> str | None
- extract_keywords(text: str) -> list[str] | None
- classify_document(text: str) -> str | None

2. Embeddings
- nutze OpenAI Python SDK oder kompatiblen Client
- Modell aus Settings
- Batch-Verarbeitung implementieren
- leere Strings defensiv behandeln
- Rückgabe muss in gleicher Reihenfolge wie Input sein

3. Retry
- tenacity verwenden
- Retry bei transienten API-Fehlern
- exponentielles Backoff
- bei endgültigem Fehler klare Exception

4. Zusammenfassung/Keywords/Klassifikation
- nur ausführen, wenn ENABLE_LLM_ENRICHMENT=true
- wenn deaktiviert: None bzw. leere Rückgaben
- Ergebnisse deterministisch formatieren
- keine freien ungeprüften Datenstrukturen

5. Validierung
- prüfe Embedding-Dimension gegen Settings
- Fehlermeldung bei Abweichung

6. README.md
- dokumentiere benötigte ENV-Variablen
- dokumentiere Verhalten bei deaktivierter LLM-Anreicherung

Wichtig:
- keine DB
- keine API
- keine Ingestion-Orchestrierung
- keine Platzhaltermethoden

Am Ende ausgeben:
1. geänderte Dateien
2. öffentliche Methoden des Services
3. Fehler- und Retry-Verhalten
```

---

# Prompt 7 — Ingestion-Service als Orchestrierung

```text
Implementiere jetzt die vollständige Ingestion-Pipeline als Business-Orchestrierung.

Bearbeite nur diese Dateien:
- app/services/ingestion_service.py
- app/models/document.py
- app/models/chunk.py
- README.md

Ziel:
Rekursiver Import eines lokalen Ordners mit idempotenter Speicherung von Dokumenten und Chunks.

Anforderungen:

1. Implementiere eine Klasse IngestionService mit mindestens:
- import_folder(folder_path: str) -> dict
- _process_file(file_path: Path, db: Session) -> dict
- _build_document_record(...)
- _build_chunk_records(...)

2. Ablauf pro Datei
- Datei entdecken
- SHA256 berechnen
- bei bereits vorhandenem file_hash: überspringen
- Text parsen
- bei leerem Text: Fehler für diese Datei protokollieren, Restlauf geht weiter
- Sprache erkennen
- optional Titel aus Dateiname oder Text ableiten
- optional Summary/Keywords/Klassifikation über EmbeddingService
- Text in Chunks zerlegen
- Embeddings pro Chunk erzeugen
- Dokument speichern
- Chunks speichern
- Commit pro Dokument
- Rollback nur für betroffenes Dokument bei Fehler

3. Idempotenz
- dedupliziere ausschließlich über file_hash
- bei erneutem Import gleicher Datei kein Update, sondern Skip

4. Deterministische Chunk-IDs
- bilde Chunk-ID deterministisch aus document_id + chunk_index

5. Dokumentstatus
- verwende mindestens:
  - imported
  - skipped
  - failed
- speichere imported in DB für erfolgreiche Dokumente

6. Rückgabe von import_folder
Struktur:
{
  "files_scanned": int,
  "new_documents": int,
  "skipped_documents": int,
  "errors": [
    {"file_path": "...", "error": "..."}
  ]
}

7. README.md
- dokumentiere den Importablauf Schritt für Schritt

Wichtig:
- Einzelfehler dürfen den Gesamtlauf nicht abbrechen
- Commit-Grenze pro Dokument
- klare Trennung zwischen Utility-, Parsing-, Chunking- und Embedding-Logik

Am Ende ausgeben:
1. geänderte Dateien
2. Ablaufdiagramm in Textform
3. welche Fehler isoliert abgefangen werden
```

---

# Prompt 8 — Dokumenten-API

```text
Implementiere jetzt ausschließlich die Dokumenten-Endpunkte.

Bearbeite nur diese Dateien:
- app/api/routes_documents.py
- app/main.py
- README.md

Ziel:
Abruf aller Dokumente und eines einzelnen Dokuments mit Chunks.

Anforderungen:

1. routes_documents.py
Implementiere einen APIRouter mit:
- GET /documents
- GET /documents/{id}

2. GET /documents
- Liste aller Dokumente
- Filter optional:
  - file_type
  - date_from
  - date_to
- sortiere standardmäßig imported_at DESC
- liefere sinnvolle Response-Modelle

3. GET /documents/{id}
- vollständige Metadaten
- vollständige Chunkliste sortiert nach chunk_index
- 404 wenn Dokument nicht existiert

4. Response-Struktur
- klare Pydantic-Modelle
- UUIDs, Timestamps sauber serialisieren

5. main.py
- Router registrieren

6. README.md
- dokumentiere beide Endpunkte mit Beispiel-Requests und Responses

Wichtig:
- keine Suchlogik
- kein Import-Endpunkt
- keine ungefilterten Roh-SQL-Strings wenn ORM sauber reicht

Am Ende ausgeben:
1. geänderte Dateien
2. Response-Modelle
3. Beispielaufrufe
```

---

# Prompt 9 — Import-API

```text
Implementiere jetzt ausschließlich den Import-Endpunkt.

Bearbeite nur diese Dateien:
- app/api/routes_import.py
- app/main.py
- scripts/run_import.py
- README.md

Ziel:
Start der Ingestion über API und über ein CLI-Script.

Anforderungen:

1. routes_import.py
- POST /import
- Request-Body:
  {
    "folder_path": "..."
  }
- validiere Pfad
- rufe IngestionService auf
- Response gemäß Spezifikation

2. scripts/run_import.py
- CLI-Script für direkten Import
- Aufruf:
  python -m scripts.run_import <folder_path>
- Ausgabe strukturiert auf stdout
- Exit-Code != 0 bei fatalem Startfehler, nicht bei Einzelfehlern im Import

3. main.py
- Router registrieren

4. README.md
- dokumentiere API-Import und CLI-Import

Wichtig:
- synchroner Lauf
- kein Background-Worker
- saubere Fehlerantworten bei ungültigem Verzeichnis

Am Ende ausgeben:
1. geänderte Dateien
2. Request/Response-Struktur
3. CLI-Beispiel
```

---

# Prompt 10 — Search-Service: Vektor + Keyword + Score-Fusion

```text
Implementiere jetzt ausschließlich die Suchlogik als Service.

Bearbeite nur diese Dateien:
- app/services/search_service.py
- README.md

Ziel:
Hybride Suche über Chunk-Ebene mit Embedding-Retrieval, PostgreSQL Fulltext und kombinierter Bewertung.

Anforderungen:

1. Implementiere eine Klasse SearchService mit mindestens:
- search(query: str, top_k: int) -> list[dict]
- _vector_search(...)
- _keyword_search(...)
- _merge_results(...)
- _build_snippet(...)

2. Vektorsuche
- Embedding für Query erzeugen
- cosine similarity gegen chunks.embedding
- top_k Retrieval

3. Keyword-Suche
- PostgreSQL full-text search auf chunk_text oder dokumentbezogen mit nachvollziehbarer Begründung
- ranking via ts_rank oder ts_rank_cd
- top_k Retrieval

4. Score-Fusion
- kombinierter Score:
  score = 0.7 * vector_score + 0.3 * keyword_score
- normalisiere Teilscores sinnvoll
- falls Treffer nur aus einem Kanal kommen, muss Ergebnis dennoch bewertet werden

5. Ergebnisformat
Liste von Dicts mit:
- document_id
- file_name
- score
- snippet
- chunk_text
- rank

6. Snippet
- extrahiere relevante Passage aus dem Chunk
- Query-Begriffe bevorzugt
- fallback auf gekürzten Chunk-Anfang

7. README.md
- dokumentiere Suchlogik, Score-Fusion und Rückgabeformat

Wichtig:
- Suche auf Chunk-Level
- keine Vermischung mit Dokument-Embeddings
- keine API in diesem Schritt
- keine Pseudologik

Am Ende ausgeben:
1. geänderte Dateien
2. Suchablauf in Reihenfolge
3. genaue Score-Formel und Normalisierung
```

---

# Prompt 11 — Search-API

```text
Implementiere jetzt ausschließlich die Search-API.

Bearbeite nur diese Dateien:
- app/api/routes_search.py
- app/main.py
- README.md

Ziel:
POST /search mit sauberem Request/Response-Modell.

Anforderungen:

1. routes_search.py
- POST /search
- Request:
  {
    "query": "Rechnungsfreigabe Prozess Einkauf",
    "top_k": 5
  }
- Validierung:
  - query darf nicht leer sein
  - top_k > 0
  - top_k mit sinnvollem Maximalwert begrenzen

2. Response
- Liste rankierter Treffer gemäß Service-Spezifikation
- Pydantic-Modelle verwenden

3. main.py
- Search-Router registrieren

4. README.md
- dokumentiere Beispielrequest und Beispielresponse

Wichtig:
- keine neue Suchlogik in Route
- Route darf nur validieren, Service aufrufen, Ergebnis zurückgeben

Am Ende ausgeben:
1. geänderte Dateien
2. Request/Response-Modelle
3. Beispielaufruf per curl
```

---

# Prompt 12 — Robuste Fehlerbehandlung und Logging-Härtung

```text
Härte jetzt das System gegen Laufzeitfehler. Keine neuen Features.

Bearbeite nur diese Dateien:
- app/core/logging.py
- app/main.py
- app/services/ingestion_service.py
- app/services/parsing_service.py
- app/services/embedding_service.py
- app/services/search_service.py
- README.md

Ziel:
Einheitliche Fehlerbilder, sauberes Logging, keine stillen Fehlzustände.

Anforderungen:

1. Logging
- wichtige Events auf INFO:
  - Import gestartet
  - Datei erkannt
  - Datei übersprungen
  - Dokument importiert
  - Suche gestartet
- Fehler auf ERROR mit Kontext:
  - file_path
  - document_id falls vorhanden
  - operation
- keine sensiblen Keys loggen

2. Fehlerklassen
- definiere sinnvolle Custom Exceptions dort, wo notwendig
- klare Trennung zwischen:
  - Validation Error
  - Parsing Error
  - Embedding Error
  - Search Error

3. API Error Handling
- FastAPI Exception Handler für definierte Fehler
- konsistente JSON-Fehlerstruktur

4. README.md
- dokumentiere Error Handling und Logging-Verhalten

Wichtig:
- kein Feature-Ausbau
- keine Hintergrundjobs
- Fokus Stabilität und Nachvollziehbarkeit

Am Ende ausgeben:
1. geänderte Dateien
2. Error-Typen
3. Beispiel einer Fehlerantwort
```

---

# Prompt 13 — Docker-Härtung und ausführbare Umgebung

```text
Finalisiere jetzt die Container-Laufumgebung. Keine Feature-Erweiterung.

Bearbeite nur diese Dateien:
- Dockerfile
- docker-compose.yml
- README.md

Ziel:
Vollständig lauffähige lokale Entwicklungsumgebung mit PostgreSQL + pgvector + Backend.

Anforderungen:

1. Dockerfile
- Python 3.11
- saubere Layer-Struktur
- requirements zuerst kopieren für Build-Cache
- App-Code kopieren
- Uvicorn Startkommando
- sinnvoller Workdir
- Port 8000 expose

2. docker-compose.yml
- Service postgres mit pgvector
- Service backend
- ENV-Variablen für Backend
- Port-Mapping 8000:8000
- Volume für persistente Postgres-Daten
- depends_on korrekt
- healthcheck für Postgres wenn sinnvoll

3. README.md
- exakte Startschritte
- exakte Stop-Schritte
- Beispiel für API-Test
- Hinweise auf benötigte .env Variablen

Wichtig:
- keine unbestimmten Platzhalter
- lauffähige docker compose Konfiguration

Am Ende ausgeben:
1. geänderte Dateien
2. Startbefehle
3. Prüfschritte nach dem Start
```

---

# Prompt 14 — End-to-End Validierung und README-Konsolidierung

```text
Konsolidiere jetzt das Projekt auf Produktreife des MVP. Keine neuen Features, nur Validierung und Dokumentation.

Bearbeite alle notwendigen Dateien, aber nur wenn tatsächlich erforderlich.

Ziel:
Sicherstellen, dass das Gesamtsystem konsistent, startbar und dokumentiert ist.

Aufgaben:

1. Prüfe:
- Imports korrekt
- Router registriert
- Config vollständig
- DB-Init funktioniert
- Model-Referenzen korrekt
- Services instanziierbar
- keine zyklischen Imports
- keine toten Platzhalter
- keine TODO-Kommentare

2. README.md vollständig finalisieren
Es muss enthalten:
- Architekturüberblick
- Projektstruktur
- Setup lokal
- Setup Docker
- ENV-Variablen
- Importablauf
- Suchablauf
- API-Endpunkte
- Beispiel Import
- Beispiel Suche
- bekannte Risiken und Engpässe
- Annahmen des MVP
- vorbereitete Erweiterungen

3. Gib zusätzlich aus:
- finale Liste aller Projektdateien
- exakten lokalen Startbefehl
- exakten Docker-Startbefehl
- eine empfohlene manuelle Testsequenz in 10 Schritten

Wichtig:
- keine Funktionserweiterung
- keine kosmetischen Umbauten ohne Zweck
- nur Konsistenz, Korrektheit, Dokumentation

Am Ende ausgeben:
1. geänderte Dateien
2. Konsistenzprüfungen
3. finale Testsequenz
```

---

## Empfohlene Ausführungslogik

Reihenfolge strikt einhalten:

1. Basis
2. ORM
3. Utilities
4. Parsing
5. Chunking
6. Embeddings
7. Ingestion
8. Dokumenten-API
9. Import-API
10. Search-Service
11. Search-API
12. Fehlerbehandlung
13. Docker
14. Konsolidierung

## Kontrollpunkte nach jedem Schritt

Nach jedem Prompt in Claude prüfen:

- wurden nur die erlaubten Dateien verändert
- ist der Schritt isoliert vollständig
- wurden keine Folgefeatures vorgezogen
- ist der Code direkt ausführbar
- stimmen Methodensignaturen mit den späteren Schritten überein

## Eskalationsprompts bei schlechter Ausgabe

Falls Claude abstrahiert statt implementiert:

```text
Abbruch der aktuellen Antwort. Liefere ausschließlich produktionsnahen Code für die genannten Dateien. Keine Beschreibungen, keine Pseudologik, keine Platzhalter, keine TODOs. Halte dich exakt an die geforderten Dateigrenzen und Methodensignaturen.
```

Falls Claude zu viele Dateien ändert:

```text
Verwerfe die letzte Änderung. Bearbeite ausschließlich die explizit freigegebenen Dateien. Keine Nebeneffekte in anderen Modulen.
```

Falls Claude Architekturregeln verletzt:

```text
Korrigiere die Implementierung unter Einhaltung dieser Regeln:
- keine Geschäftslogik in Routen
- keine DB-Logik in Utilities
- keine Embeddings auf Dokumentebene
- Chunk- und Dokumentebene strikt getrennt
- jede KI-Anreicherung muss persistent speicherbar sein
```

Falls du willst, erstelle ich dir im nächsten Schritt noch eine zweite Serie: **Review-Prompts pro Phase**, mit denen du Claudes Output systematisch auf Architekturfehler, Leaks, idempotenzprobleme und Suchqualitätsfehler prüfen kannst.

### 5. Benutzer

promt zum erstellen der gui

### 6. Assistent

```text
Rolle:
Du bist Senior Frontend Engineer, UX Architect und Full-Stack Integrator. Erweitere das bestehende Backend-Projekt um eine vollständig lauffähige GUI für das Dokumenten-Ingestion- und Suchsystem. Arbeite konkret, deterministisch und entwicklungsnah. Keine generischen Beschreibungen, keine Platzhalter, keine TODOs.

Ziel:
Baue eine produktionsnahe Web-GUI für das vorhandene FastAPI-Backend. Die GUI muss Dokumentimport, Dokumentübersicht, Dokumentdetailansicht und hybride Suche abbilden. Fokus: robuste, klare, funktionale Oberfläche für interne Nutzung. Kein Auth-System. Kein Design-Overengineering. Keine Mock-Daten.

Technologiestack:
Frontend:
- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui oder funktional gleichwertige komponentenbasierte Struktur
- fetch API oder axios

Backend-Integration:
- bestehendes FastAPI-Backend unter http://localhost:8000
- keine neuen Backend-Features erfinden
- nur existierende Endpunkte nutzen:
  - GET /health
  - POST /import
  - GET /documents
  - GET /documents/{id}
  - POST /search

Wichtige Regeln:
- Kein neues zweites Backend
- Keine Mock-Responses
- Keine Platzhalterdaten
- GUI direkt startbar
- saubere Fehlerbehandlung
- saubere Ladezustände
- klare Komponentenstruktur
- TypeScript strikt typisieren
- keine Businesslogik in UI-Komponenten, sondern in API-Client/Hooks/Services kapseln
- Styling schlicht, funktional, professionell
- responsive, aber primär Desktop-optimiert
- keine globale State-Overengineering-Library, solange nicht nötig
- keine WebSockets
- kein Login
- keine Drag-and-Drop-Uploads, da Import auf lokalen Serverpfad basiert

Erzeuge exakt diese Frontend-Struktur:
frontend/
 ├── index.html
 ├── package.json
 ├── tsconfig.json
 ├── vite.config.ts
 ├── postcss.config.js
 ├── tailwind.config.ts
 ├── src/
 │    ├── main.tsx
 │    ├── App.tsx
 │    ├── lib/
 │    │    ├── api.ts
 │    │    ├── types.ts
 │    │    └── utils.ts
 │    ├── components/
 │    │    ├── layout/
 │    │    │    ├── AppShell.tsx
 │    │    │    ├── Header.tsx
 │    │    │    └── Sidebar.tsx
 │    │    ├── common/
 │    │    │    ├── PageContainer.tsx
 │    │    │    ├── LoadingState.tsx
 │    │    │    ├── ErrorState.tsx
 │    │    │    ├── EmptyState.tsx
 │    │    │    └── StatusBadge.tsx
 │    │    ├── import/
 │    │    │    └── ImportForm.tsx
 │    │    ├── documents/
 │    │    │    ├── DocumentTable.tsx
 │    │    │    ├── DocumentFilters.tsx
 │    │    │    ├── DocumentDetail.tsx
 │    │    │    └── ChunkList.tsx
 │    │    └── search/
 │    │         ├── SearchForm.tsx
 │    │         └── SearchResults.tsx
 │    ├── pages/
 │    │    ├── DashboardPage.tsx
 │    │    ├── ImportPage.tsx
 │    │    ├── DocumentsPage.tsx
 │    │    ├── DocumentDetailPage.tsx
 │    │    └── SearchPage.tsx
 │    └── styles/
 │         └── index.css

Funktionale Anforderungen:

1. App-Struktur
- Implementiere eine Sidebar-Navigation mit folgenden Bereichen:
  - Dashboard
  - Import
  - Dokumente
  - Suche
- Header mit Systemstatus
- Healthcheck gegen /health beim Laden der App
- Anzeige Backend erreichbar / nicht erreichbar

2. Dashboard
- Zeige kompakte Systemübersicht:
  - Backend-Status
  - Anzahl geladener Dokumente
  - letzte Dokumente
- Daten aus GET /documents laden
- keine zusätzlichen Backend-Endpunkte annehmen

3. Import-Seite
- Formular mit Eingabefeld für folder_path
- Button „Import starten“
- Request an POST /import
- Response anzeigen:
  - files_scanned
  - new_documents
  - skipped_documents
  - errors
- Ladezustand und Fehlerzustand sauber anzeigen
- Importhistorie nicht erfinden; nur Ergebnis des letzten Laufs lokal im UI anzeigen

4. Dokumentübersicht
- GET /documents verwenden
- Tabellarische Übersicht mit Spalten:
  - file_name
  - file_type
  - language
  - imported_at
  - status
- Filter:
  - file_type
  - date_from
  - date_to
- Filter über Query-Parameter des bestehenden Endpunkts oder clientseitig, falls Backend dies exakt so liefert
- Klick auf Zeile öffnet Dokumentdetailseite

5. Dokumentdetailseite
- GET /documents/{id}
- Zeige:
  - Metadaten
  - title
  - summary
  - full_text
  - chunks sortiert nach chunk_index
- ChunkList-Komponente:
  - chunk_index
  - token_count
  - chunk_text
- full_text in scrollbarem Container
- lange Inhalte performant und lesbar darstellen

6. Suchseite
- Formular:
  - query
  - top_k
- POST /search
- Ergebnisse darstellen mit:
  - rank
  - file_name
  - score
  - snippet
  - chunk_text
- Klick auf Suchtreffer öffnet zugehörige Dokumentdetailseite
- Score formatiert mit begrenzter Nachkommastellenanzahl

7. API-Layer
- zentrale API-Datei in src/lib/api.ts
- typisierte Methoden:
  - getHealth()
  - importFolder()
  - getDocuments()
  - getDocumentById()
  - searchDocuments()
- zentralisiertes Fehlerhandling
- definierte TypeScript-Interfaces in src/lib/types.ts

8. Routing
- React Router verwenden
- Routen:
  - /
  - /import
  - /documents
  - /documents/:id
  - /search

9. UX-Regeln
- jede Seite hat:
  - LoadingState
  - ErrorState
  - EmptyState falls sinnvoll
- Buttons während Requests deaktivieren
- keine stillen Fehler
- Fehlermeldungen konkret anzeigen
- Datumswerte lesbar formatieren
- Status visuell kenntlich machen

10. Styling
- Tailwind sauber konfigurieren
- nüchternes Layout
- gute Tabellenlesbarkeit
- sinnvolle Abstände
- keine dekorativen Elemente ohne Funktion
- Desktop first, aber responsive genug für kleinere Breiten

11. Entwicklungsintegration
- package.json mit allen nötigen Scripts:
  - dev
  - build
  - preview
- Vite-Setup funktionsfähig
- falls sinnvoll Vite-Proxy auf Backend konfigurieren
- README-Abschnitt im Frontend ergänzen oder frontend/README erzeugen:
  - Setup
  - Start
  - Build
  - API-Anbindung

12. Qualitätsregeln
- keine ungenutzten Komponenten
- keine toten Imports
- keine any-Typen ohne zwingenden Grund
- keine Businesslogik in Presentational Components
- wiederverwendbare Komponenten klar trennen
- deterministische Lade- und Fehlerzustände
- direkt kompilierbar

Erwartete Ausgabe:
Liefere in exakt dieser Reihenfolge:
1. vollständige Frontend-Projektstruktur
2. package.json
3. Vite- und Tailwind-Konfiguration
4. zentrale Types und API-Layer
5. Layout-Komponenten
6. Seiten-Komponenten
7. Startanweisung lokal
8. bekannte Risiken und Integrationspunkte

Zusatz:
Wenn Backend-Response-Felder leicht variieren könnten, implementiere defensive Typisierung und klare Mapping-Logik, ohne neue Backend-Contracts zu erfinden.

Wichtig:
Nicht beschreiben, sondern implementieren. Vollständiger Code. Keine Pseudologik.
```
