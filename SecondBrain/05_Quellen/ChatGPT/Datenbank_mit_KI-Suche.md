---
title: "Datenbank mit KI-Suche"
type: chatgpt_conversation
source: chatgpt
source_id: "69ca227e-1104-838f-97ae-acbc19186c46"
created: 2026-03-30
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
---


# Datenbank mit KI-Suche

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69ca227e-1104-838f-97ae-acbc19186c46`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

erstelle mir einen entwicklungsprompt. ich möchte eine datenbank aufbeuen in welche ich dokumente aus einem ordner einlese. beim einlesen werde ich durch ki unterstützt und inhalt zum gleichen thema zusammen geführt oder stukturiert eingelesen um später über eine ki suche nach schlagwörtern anzuzeigen. das soll der ausgangspunkt sein

### 2. Assistent

Hier ist ein belastbarer **Entwicklungsprompt** als Ausgangspunkt für ein KI-gestütztes System zur Dokumentaufnahme, thematischen Zusammenführung, Strukturierung und späteren semantischen Suche.

---

## Entwicklungsprompt

Du bist ein erfahrener Software-Architekt, AI-Engineer und Backend-Entwickler. Entwirf und implementiere ein System mit folgendem Ziel:

### Zielbild
Es soll eine Datenbank aufgebaut werden, in die Dokumente aus einem definierten Ordner automatisiert eingelesen werden. Während des Einlesens unterstützt KI bei der Analyse, Strukturierung, Klassifikation und thematischen Zusammenführung von Inhalten. Dokumente mit ähnlichem oder identischem Thema sollen logisch gruppiert, konsolidiert oder semantisch verknüpft werden. Später soll eine KI-gestützte Suche über Schlagwörter, Themen, semantische Ähnlichkeit und inhaltliche Fragen möglich sein, sodass relevante Inhalte schnell gefunden und angezeigt werden.

### Kernanforderungen
1. Implementiere einen Importprozess, der Dokumente aus einem lokalen oder definierten Verzeichnis einliest.
2. Unterstütze mindestens diese Dateitypen:
   - PDF
   - DOCX
   - TXT
   - optional: XLSX, E-Mail-Dateien, Markdown
3. Extrahiere aus jedem Dokument:
   - Dateiname
   - Pfad
   - Erstellungsdatum / Änderungsdatum
   - Volltext
   - erkannte Sprache
   - Titel
   - mögliche Schlagwörter
   - Themenbereich
   - Zusammenfassung
4. Nutze KI, um Inhalte semantisch zu analysieren und:
   - ähnliche Dokumente zu erkennen
   - gleiche Themen zusammenzuführen
   - Dokumente in thematische Cluster einzuordnen
   - strukturierte Metadaten zu erzeugen
5. Speichere die Daten so, dass sowohl klassische Filterung als auch semantische Suche möglich sind.
6. Ermögliche eine spätere Suche über:
   - Schlagwörter
   - Volltext
   - semantische Ähnlichkeit
   - natürlichsprachliche Suchanfragen
7. Gib Suchergebnisse mit nachvollziehbarer Relevanz zurück, inklusive:
   - Dokumenttitel
   - Kurzbeschreibung
   - Themencluster
   - relevante Textausschnitte
   - Herkunftsdatei

### Fachliche Logik
Das System soll nicht nur Dateien speichern, sondern Wissen strukturieren. Dafür gelten folgende Regeln:

#### 1. Dokumentaufnahme
- Dokumente werden aus einem Quellordner rekursiv eingelesen.
- Jede Datei erhält eine eindeutige interne ID.
- Doppelte Dateien sollen erkannt werden, z. B. per Hashwert.
- Bereits importierte Dateien sollen nicht unnötig erneut verarbeitet werden.

#### 2. Inhaltsverarbeitung
- Extrahiere den lesbaren Text.
- Zerlege große Dokumente in sinnvolle Textabschnitte oder Chunks.
- Erzeuge pro Chunk Embeddings für semantische Suche.
- Erzeuge pro Dokument eine Zusammenfassung und eine Themenklassifikation.
- Extrahiere Entitäten, Schlüsselbegriffe und mögliche Kategorien.

#### 3. Thematische Zusammenführung
- Dokumente mit hoher semantischer Ähnlichkeit sollen gruppiert werden.
- Falls mehrere Dokumente dasselbe Thema behandeln, verknüpfe sie in einem gemeinsamen Themenobjekt.
- Trenne strikt zwischen:
  - Originaldokument
  - extrahierten Inhalten
  - thematischem Cluster
  - KI-generierten Zusammenfassungen
- Originaldaten dürfen nie überschrieben werden.

#### 4. Suche
- Die Suche soll Hybrid Search unterstützen:
  - Keyword Search
  - Metadatenfilter
  - Vector Search
- Eine natürlichsprachliche Anfrage wie „Zeige alle Dokumente zum Thema Rechnungsfreigabe im Einkauf“ soll relevante Dokumente, Cluster und Textstellen liefern.
- Ergebnisse sollen nach Relevanz priorisiert werden.

### Technische Zielarchitektur
Entwirf das System modular. Nutze nach Möglichkeit diese Bausteine oder gleichwertige Alternativen:

#### Backend
- Python mit FastAPI oder gleichwertig
- Klare Trennung von:
  - Ingestion Service
  - Parsing Service
  - AI Enrichment Service
  - Search Service
  - API Layer

#### Datenhaltung
Kombiniere zwei Speicherlogiken:
1. **Relationale oder dokumentenbasierte Datenbank** für Metadaten, Dokumentinformationen, Cluster und Verknüpfungen
   - PostgreSQL oder MongoDB
2. **Vektor-Datenbank** für semantische Suche
   - pgvector, Qdrant, Weaviate oder Chroma

#### KI-Komponenten
- Text Extraktion
- Embedding-Erzeugung
- Dokumentklassifikation
- Clustering ähnlicher Inhalte
- Zusammenfassungen
- optionale RAG-Suche für Antwortgenerierung

### Datenmodell
Definiere ein sauberes Start-Datenmodell mit mindestens folgenden Entitäten:

#### Document
- id
- source_path
- file_name
- file_type
- file_hash
- created_at
- modified_at
- import_timestamp
- language
- title
- full_text
- summary
- status

#### DocumentChunk
- id
- document_id
- chunk_index
- chunk_text
- embedding
- token_count
- page_reference oder section_reference

#### TopicCluster
- id
- cluster_name
- cluster_summary
- keywords
- confidence_score

#### DocumentTopicMapping
- id
- document_id
- cluster_id
- relevance_score

#### SearchQueryLog
- id
- query_text
- timestamp
- result_count
- latency_ms

### Nichtfunktionale Anforderungen
1. Das System muss erweiterbar sein.
2. Der Import muss fehlertolerant sein.
3. Fehlerhafte Dateien dürfen den Gesamtprozess nicht blockieren.
4. Jeder Verarbeitungsschritt muss protokolliert werden.
5. Ergebnisse müssen nachvollziehbar sein.
6. KI-generierte Struktur darf als Vorschlag behandelt werden, nicht als unumstößliche Wahrheit.
7. Datenschutz und Vertraulichkeit müssen berücksichtigt werden, insbesondere bei sensiblen Dokumenten.

### Implementierungsreihenfolge
Setze das Projekt in Phasen um:

#### Phase 1 – Minimal Viable System
- Ordner einlesen
- Dokumenttext extrahieren
- Metadaten speichern
- Chunks erzeugen
- Embeddings generieren
- einfache semantische Suche bereitstellen

#### Phase 2 – KI-Anreicherung
- automatische Zusammenfassungen
- Schlagwortextraktion
- Themenklassifikation
- Clustering ähnlicher Dokumente

#### Phase 3 – Erweiterte Suche
- hybride Suche
- Filter nach Dokumenttyp, Datum, Thema
- Treffer mit Snippets und Relevanzbewertung

#### Phase 4 – Wissensstruktur
- thematische Oberobjekte
- Querverweise
- konsolidierte Themensichten
- optionale Chat-Oberfläche über den Datenbestand

### Erwartete Ausgabe
Liefere die Lösung in dieser Reihenfolge:

1. Systemarchitektur als Übersicht
2. Technologieentscheidung mit Begründung
3. Datenmodell
4. Verarbeitungs-Pipeline
5. Suchlogik
6. API-Endpunkte
7. MVP-Umsetzungsplan
8. Beispielcode für den Projektstart
9. Risiken, Engpässe und Skalierungsgrenzen
10. klare Annahmen und offene Punkte

### Qualitätsmaßstab
Die Lösung soll nicht generisch bleiben. Arbeite konkret, umsetzbar und entwicklungsnah. Zeige:
- Ordner-Ingestion
- Parsing-Logik
- Chunking-Strategie
- Embedding-Speicherung
- Clustering-Ansatz
- Sucharchitektur
- Beispiel für eine Suchanfrage
- Beispielantwort aus der API

### Zusätzliche Leitplanken
- Bevorzuge pragmatische Architektur statt Overengineering.
- Trenne deterministische Logik von KI-Logik.
- Halte Originaldokumente unverändert.
- Versioniere KI-Ergebnisse, falls Dokumente neu importiert werden.
- Benenne Unsicherheiten, Annahmen und technische Schulden explizit.

---

## Kompaktere Version für direkte Nutzung in einem Coding-Tool

Baue ein modulares System zur Dokumentaufnahme und KI-gestützten Suche. Dokumente sollen aus einem Ordner automatisiert eingelesen werden. Unterstütze PDF, DOCX und TXT. Extrahiere Text und Metadaten, zerlege Inhalte in Chunks, erzeuge Embeddings und speichere alles in einer Datenbank plus Vektorindex. Nutze KI zur Zusammenfassung, Schlagwortextraktion, Themenklassifikation und Erkennung ähnlicher Dokumente. Führe Dokumente mit gleichem Thema in Cluster zusammen, ohne Originaldaten zu überschreiben. Implementiere eine hybride Suche aus Keyword-, Metadaten- und semantischer Suche. Liefere Architektur, Datenmodell, Pipeline, API-Endpunkte, MVP-Plan und Startcode mit Python/FastAPI, PostgreSQL plus pgvector oder einer gleichwertigen Kombination. Berücksichtige Fehlertoleranz, Logging, Nachvollziehbarkeit und spätere Erweiterbarkeit.

---

## Ergänzung: Präzisierter Prompt für einen starken MVP

Falls du direkt ein brauchbares erstes System erzeugen lassen willst, nimm diese Variante:

**Erstelle einen MVP für ein Dokumentenmanagement- und Wissenssuchsystem mit KI-Unterstützung.**
- Quelle: ein lokaler Ordner mit Dokumenten
- Dateitypen: PDF, DOCX, TXT
- Backend: Python + FastAPI
- Datenbank: PostgreSQL
- Vektorsuche: pgvector
- Funktionen:
  - Dateien rekursiv einlesen
  - Text extrahieren
  - Dokumente in Chunks zerlegen
  - Embeddings erzeugen
  - Metadaten speichern
  - einfache thematische Klassifikation
  - semantische Suche per API
- API-Endpunkte:
  - `/import`
  - `/documents`
  - `/search`
  - `/topics`
- Ergebnis der Suche:
  - Dokumenttitel
  - Dateipfad
  - Relevanzwert
  - Snippet
  - zugeordnetes Thema
- Liefere:
  - Projektstruktur
  - Datenbankschema
  - Beispielcode
  - Docker-Setup
  - Beispiel für Import und Suche
  - Liste technischer Risiken und nächster Ausbaustufen

---

## Bewertung des Ausgangspunkts
Dein Vorhaben enthält implizit vier Systeme, die sauber getrennt werden müssen:

1. **Ingestion-System**  
   Liest Dateien ein, erkennt Änderungen, verhindert Dubletten.

2. **Wissensaufbereitung**  
   Extraktion, Chunking, Metadaten, Themen, Cluster, Zusammenfassungen.

3. **Indexierung**  
   Klassische Datenbank plus Vektorindex.

4. **Abrufsystem**  
   Suche, Ranking, Snippets, thematische Navigation, später Chat/RAG.

Der zentrale Designfehler in solchen Projekten ist meist:  
**zu früh auf Chat-Oberfläche fokussieren, bevor Datenmodell, Chunking und Indexqualität stabil sind.**

Die kritischen Qualitätshebel sind:
- Textqualität nach Extraktion
- sinnvolle Chunk-Größe
- gutes Metadatenmodell
- robuste Dubletten- und Themenlogik
- Hybrid Search statt reiner Vektorsuche

Wenn du es sauber aufbauen willst, ist der richtige Startpunkt:  
**Ingestion + Metadaten + Chunking + Embeddings + einfache Suche.**  
Erst danach Clustering, Zusammenführung und dialogische KI.

Ich kann im nächsten Schritt daraus direkt ein **technisches Lastenheft** oder einen **kompletten Cursor-/Claude-/Copilot-Prompt für die Umsetzung** formulieren.

### 3. Benutzer

einen kompletten Cursor-/Claude-/Copilot-Prompt für die Umsetzung formulieren.

### 4. Assistent

## Vollständiger Implementierungs-Prompt (für Cursor / Claude / Copilot)

Rolle: Du bist Senior Software Architect, AI Engineer und Backend Developer. Liefere eine **vollständig lauffähige, modulare Implementierung** eines KI-gestützten Dokumenten-Ingestion- und Suchsystems. Arbeite konkret, deterministisch und entwicklungsnah. Keine generischen Beschreibungen.

---

## 1. Zielsystem

Baue ein System, das:

- Dokumente aus einem lokalen Ordner rekursiv einliest
- Inhalte extrahiert und strukturiert
- Dokumente in semantische Chunks zerlegt
- Embeddings erzeugt und speichert
- Metadaten, Inhalte und Vektoren persistiert
- eine hybride Suche (Keyword + semantisch) bereitstellt
- KI zur optionalen Anreicherung nutzt (Zusammenfassung, Keywords, Klassifikation)

Keine UI. Fokus: Backend + API + Datenmodell.

---

## 2. Technologiestack (fest vorgegeben)

Backend:
- Python 3.11
- FastAPI

Datenbank:
- PostgreSQL 15+
- Extension: pgvector

Parsing:
- pdfplumber oder pymupdf (PDF)
- python-docx (DOCX)
- native (TXT)

AI:
- Embeddings: OpenAI oder kompatibel (z. B. text-embedding-3-small)
- optional: LLM für Zusammenfassungen

Infra:
- Docker + docker-compose

---

## 3. Projektstruktur (muss exakt erzeugt werden)

```
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
```

---

## 4. Datenbankschema (PostgreSQL + pgvector)

Erzeuge SQL migrations oder SQLAlchemy Models für:

### Tabelle: documents
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

### Tabelle: chunks
- id (UUID)
- document_id (FK)
- chunk_index
- chunk_text
- token_count
- embedding (vector)
- created_at

### Tabelle: topics (Phase 2 vorbereitet)
- id
- name
- description

### Tabelle: document_topics
- document_id
- topic_id
- relevance_score

### Indexe:
- vector index (ivfflat oder hnsw) auf embedding
- fulltext index auf full_text

---

## 5. Pipeline (muss implementiert werden)

### Schritt 1: File Discovery
- rekursives Einlesen eines Ordners
- Filter: pdf, docx, txt
- Hashbildung (SHA256)
- Skip bei bereits existierendem Hash

### Schritt 2: Parsing
- extrahiere reinen Text
- Fehlerhandling pro Datei (kein Abbruch des gesamten Laufs)

### Schritt 3: Chunking
- Zielgröße: 300–800 Tokens
- Overlap: 10–20%
- harte Begrenzung: max 1000 Tokens
- Chunk-ID deterministisch (document_id + index)

### Schritt 4: Embeddings
- generiere Embedding pro Chunk
- batch processing (Performance)
- Retry bei API Fehlern

### Schritt 5: Speicherung
- Dokument speichern
- Chunks speichern inkl. Embedding

---

## 6. API-Endpunkte (implementieren)

### POST /import
- Input: folder_path
- Funktion: startet Ingestion
- Output:
  - Anzahl Dateien
  - neue Dokumente
  - übersprungene Dokumente
  - Fehler

### GET /documents
- Liste aller Dokumente
- Filter:
  - file_type
  - Datum

### GET /documents/{id}
- vollständige Metadaten + Chunks

### POST /search
Input:
```
{
  "query": "Rechnungsfreigabe Prozess Einkauf",
  "top_k": 5
}
```

Funktion:
- Embedding der Query erzeugen
- Vektor-Suche (cosine similarity)
- optional Keyword Ranking kombinieren

Output:
```
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
```

---

## 7. Suchlogik (Hybrid)

Implementiere:

1. Vektorsuche:
   - cosine similarity
   - top_k retrieval

2. Keyword-Suche:
   - PostgreSQL full-text search

3. Ranking:
   - kombinierter Score:
     score = 0.7 * vector_score + 0.3 * keyword_score

4. Snippet:
   - extrahiere relevante Passage aus Chunk

---

## 8. Beispielcode (muss geliefert werden)

Erzeuge konkret:

- DB Connection (SQLAlchemy)
- Embedding Service
- Chunking Funktion
- Import Pipeline
- Search Query (SQL + vector)

Keine Pseudologik.

---

## 9. Docker Setup

docker-compose enthält:
- postgres + pgvector
- backend service

Expose:
- Port 8000

---

## 10. Nichtfunktionale Anforderungen

- idempotenter Import
- Logging auf INFO + ERROR
- Retry-Mechanismus für externe APIs
- keine Blockierung bei Einzelfehlern
- klare Trennung:
  - IO
  - AI
  - Business Logic

---

## 11. Annahmen (explizit behandeln)

- Dokumente sind textuell extrahierbar
- keine OCR im MVP
- Embedding-Modell verfügbar
- keine Rechteverwaltung im MVP

---

## 12. Erweiterungen (nur vorbereiten, nicht vollständig bauen)

- Clustering ähnlicher Dokumente
- automatische Themenbildung
- RAG-basierte Antwortgenerierung
- UI Layer

---

## 13. Erwartete Ausgabe

Liefere in exakt dieser Reihenfolge:

1. Projektstruktur (komplett)
2. requirements.txt
3. Dockerfile + docker-compose
4. Datenbankschema (SQL oder ORM)
5. Services (voll implementiert)
6. API-Routen
7. Beispiel: Importlauf
8. Beispiel: Suchanfrage + Antwort
9. bekannte Risiken und Engpässe

---

## 14. Qualitätskriterien

- Code direkt ausführbar
- keine Platzhalter
- keine TODO-Kommentare
- keine abstrahierten Beschreibungen
- klare Trennung der Verantwortlichkeiten
- deterministische Verarbeitung

---

## 15. Kritische Designregeln

- Originaldokument bleibt unverändert
- jede Transformation ist nachvollziehbar
- keine Vermischung von Chunk- und Dokumentebene
- Embeddings ausschließlich auf Chunk-Level
- keine KI-Entscheidung ohne Speicherung des Ergebnisses

---

## Kompakte Version (für schnelle Nutzung)

Baue ein Python/FastAPI Backend mit PostgreSQL + pgvector. Implementiere eine Pipeline, die Dokumente (PDF, DOCX, TXT) aus einem Ordner einliest, Text extrahiert, in Chunks zerlegt (ca. 500 Tokens), Embeddings erzeugt und speichert. Implementiere eine hybride Suche aus Vektor- und Keyword-Suche. Stelle API-Endpunkte für Import, Dokumentliste und Suche bereit. Liefere vollständigen Code inkl. Docker-Setup, Datenmodell und Beispielanfragen. Fokus: lauffähiger MVP ohne UI.

---

## Systemische Einordnung

Dieses Prompt-Design erzwingt:

- frühe Stabilisierung der Datenpipeline
- klare Trennung zwischen Speicherung und Interpretation
- Vermeidung von „LLM-first“-Fehlarchitektur
- Grundlage für spätere Wissensaggregation

Haupthebel für Qualität:
- Chunking-Strategie
- Embedding-Konsistenz
- Metadatenstruktur
- Ranking-Funktion

Haupt-Risiken:
- schlechte Textextraktion → unbrauchbare Embeddings
- zu große Chunks → schlechte Retrieval-Qualität
- fehlende Deduplikation → redundante Treffer
- reine Vektorsuche → Kontextverlust

Zielzustand nach Umsetzung:
- stabiler, erweiterbarer Wissensindex
- reproduzierbare Ingestion
- semantisch brauchbare Suche als Basis für weitere KI-Funktionalität
