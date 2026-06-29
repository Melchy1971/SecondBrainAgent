---
title: "Dateistruktur optimieren und erstellen"
type: chatgpt_conversation
source: chatgpt
source_id: "69f33bd2-5bec-838f-a2b5-0e8db537df45"
created: 2026-04-30
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


# Dateistruktur optimieren und erstellen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69f33bd2-5bec-838f-a2b5-0e8db537df45`
- Nachrichten: 13

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

starte mit der erstellung der dateistruktur verwende für die umsetzung die struktur in der zip. optimire und erstelle eine neue zip datei bevor wir mit den prompts starten

### 2. Assistent

Ich prüfe die vorhandene ZIP-Struktur, gleiche sie gegen den Masterplan ab und erzeuge daraus eine optimierte Startstruktur als neue ZIP. Fokus: M0/M1-fähige Repo-Basis ohne Implementierungs-Prompts.

### 3. Assistent

Erstellt: neue optimierte Startstruktur als ZIP.

Basis: Masterplan + vorhandene ZIP-Struktur. fileciteturn0file0

Download: [wissensbasis_v1_startstruktur.zip](sandbox:/mnt/data/wissensbasis_v1_startstruktur.zip)

### 4. Assistent

## Paket 1: M0 Projektgrundlage

### Prompt 1.1: Repo-Struktur prüfen und fixieren

```text
Ziel:
Prüfe die vorhandene Projektstruktur und stelle sicher, dass sie als V1-Startstruktur für die Wissensbasis geeignet ist.

Kontext:
- Projekt basiert auf FastAPI Backend, React/Vite Frontend, PostgreSQL remote, Alembic Migrationen.
- V1 ist Single-User ohne Auth.
- Datenmodell muss Workspace/User-Felder vorbereiten.
- Originaldateien werden nicht gespeichert.
- Markdown ist kanonische Textquelle.

Nicht ändern:
- Keine Authentifizierung implementieren.
- Keine Vektorsuche implementieren.
- Keine Docker-Compose-Abhängigkeit einführen.
- Keine fachlichen Scope-Erweiterungen.

Aufgaben:
1. Prüfe Ordnerstruktur für:
   - backend
   - frontend
   - docs
   - scripts
   - tests
   - migrations
2. Ergänze fehlende Platzhalterdateien, falls notwendig.
3. Stelle sicher, dass Backend und Frontend klar getrennt sind.
4. Lege README-Dateien an, wenn Verzeichnisse sonst leer oder unklar sind.
5. Dokumentiere kurz die Zweckbestimmung jedes Hauptordners.

Akzeptanzkriterien:
- Struktur ist verständlich und entwicklungsfähig.
- Alembic liegt im Backend-Kontext.
- Docs enthalten Platz für ADRs, Task-Kontrakte und Betriebsdokumentation.
- Keine Implementierung von Fachlogik.
- Keine unnötigen Frameworks oder Abhängigkeiten.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Begründung je Änderung.
- Offene Risiken.
```

### Prompt 1.2: Architektur-ADR erstellen

```text
Ziel:
Erstelle eine ADR für die technische Grundentscheidung der V1-Wissensbasis.

Kontext:
- Backend: FastAPI
- Frontend: React/Vite
- DB: PostgreSQL remote
- Migrationen: Alembic
- KI: lokaler Ollama-Provider über austauschbares Provider-Interface
- OCR: lokal
- Auth: nicht in V1
- Betrieb V1: GUI lokal, DB remote

Nicht ändern:
- Keine Implementierung.
- Keine Erweiterung des V1-Scopes.
- Keine Auth-Entscheidung vorziehen.

Aufgaben:
1. Erstelle `docs/adr/0001-tech-stack-v1.md`.
2. Dokumentiere:
   - Status
   - Kontext
   - Entscheidung
   - Alternativen
   - Konsequenzen
   - Risiken
   - Nicht-Ziele
3. Formuliere präzise und prüfbar.

Akzeptanzkriterien:
- Entscheidung ist nachvollziehbar.
- Trade-offs sind explizit.
- V1-Grenzen sind klar.
- Spätere Remote-Fähigkeit bleibt vorbereitet.

Outputformat:
- Kurze Analyse.
- Neue Datei.
- Kurze Zusammenfassung der Entscheidung.
```

### Prompt 1.3: V1-Scope-ADR erstellen

```text
Ziel:
Erstelle eine ADR für V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfähigkeit.

Kontext:
- V1 ist Single-User.
- Auth wird nicht implementiert.
- Datenmodell enthält workspace_id und owner_user_id.
- Dokumente werden versioniert.
- Chat darf allgemein antworten, muss Wissensbasisbezug kennzeichnen.
- Quellenpflicht bei dokumentbasierten Antworten.

Nicht ändern:
- Keine aktive Rollenlogik.
- Keine Rechteprüfung.
- Keine Originaldateispeicherung.
- Keine Vektorsuche als Pflichtbestandteil.

Aufgaben:
1. Erstelle `docs/adr/0002-v1-scope-and-boundaries.md`.
2. Dokumentiere:
   - Muss in V1
   - Nicht in V1
   - vorbereitete spätere Fähigkeiten
   - Scope-Risiken
   - Entscheidungskriterien für spätere Erweiterungen
3. Nutze klare Muss-/Darf-nicht-Formulierungen.

Akzeptanzkriterien:
- Keine Ambiguität bei Auth, Rollen, Originaldateien, Vektorsuche.
- Datenmodell-Vorbereitung ist begründet.
- Scope-Creep-Risiken sind benannt.

Outputformat:
- Kurze Analyse.
- Neue Datei.
- Offene Entscheidungen, falls vorhanden.
```

## Dokumentation aktualisieren nach Paket 1

```text
Ziel:
Aktualisiere die Projektdokumentation nach Abschluss von Paket 1.

Kontext:
Paket 1 umfasst:
- Repo-Struktur geprüft/fixiert
- Tech-Stack-ADR erstellt
- V1-Scope-ADR erstellt

Aufgaben:
1. Aktualisiere `README.md` mit:
   - Projektziel
   - Hauptstruktur
   - Startpunkt für Entwickler
   - Verweis auf ADRs
2. Aktualisiere oder erstelle `docs/status.md` mit:
   - abgeschlossenem Paket
   - geänderten Dateien
   - offenen Risiken
   - nächstem Paket
3. Prüfe, ob ADRs korrekt verlinkt sind.

Akzeptanzkriterien:
- Neue Entwickler verstehen Projektziel und Struktur.
- ADRs sind auffindbar.
- Status zeigt klar: Paket 1 abgeschlossen, Paket 2 bereit.
- Keine Implementierungsdetails vortäuschen, die noch nicht existieren.

Outputformat:
- Geänderte Dateien.
- Kurze Zusammenfassung.
- Nächster empfohlener Schritt.
```

### 5. Benutzer

starte nun mit der entwicklung und liefere mir die prompts schritt für schritt immer in deutsch. und nach jedempacket einen prompt zum aktualisieren der dokumentation

### 6. Benutzer

weiter

### 7. Assistent

## Paket 2: Backend-Grundlage und Alembic

### Prompt 2.1: Backend-Grundgerüst prüfen und vervollständigen

```text
Ziel:
Erstelle oder vervollständige das Backend-Grundgerüst für FastAPI ohne Fachlogik.

Kontext:
- Backend: FastAPI
- Datenbank: PostgreSQL remote
- Migrationen: Alembic
- V1 ohne Auth
- SQL-direkter Datenzugriff ist erlaubt
- Fachlogik folgt erst in späteren Paketen

Nicht ändern:
- Keine Importpipeline implementieren.
- Keine Dokumentlogik implementieren.
- Keine Chatlogik implementieren.
- Keine Authentifizierung implementieren.
- Keine Docker-Compose-Pflicht einführen.

Aufgaben:
1. Prüfe `backend/`.
2. Erstelle oder ergänze:
   - `backend/app/main.py`
   - `backend/app/core/config.py`
   - `backend/app/core/database.py`
   - `backend/app/api/health.py`
   - `backend/requirements.txt`
   - `backend/README.md`
3. Implementiere minimalen FastAPI-App-Start.
4. Implementiere Konfiguration über Umgebungsvariablen.
5. Implementiere DB-Verbindungsprüfung als Healthcheck.
6. Stelle sicher, dass fehlende DB-Konfiguration sauber als Fehler erkennbar ist.

Akzeptanzkriterien:
- Backend startet lokal.
- `/health` funktioniert ohne DB.
- `/health/db` prüft PostgreSQL-Verbindung.
- Keine Fachlogik vorhanden.
- Konfiguration ist remote-DB-fähig.
- Fehlerausgaben enthalten keine Secrets.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Startbefehl.
- Risiken.
```

### Prompt 2.2: Alembic initialisieren

```text
Ziel:
Initialisiere Alembic im Backend-Kontext und bereite Migrationen für PostgreSQL vor.

Kontext:
- Migrationstool: Alembic
- Ablage im Backend-Kontext
- Ziel-DB: PostgreSQL
- Schemaänderungen müssen versioniert sein
- SQL-nahe Migrationen sind erlaubt

Nicht ändern:
- Keine Fachschema-Migrationen erstellen.
- Keine ORM-Pflicht einführen.
- Keine node-pg-migrate-Struktur übernehmen.
- Keine Auth-Tabellenlogik implementieren.

Aufgaben:
1. Erstelle oder ergänze:
   - `backend/alembic.ini`
   - `backend/migrations/env.py`
   - `backend/migrations/script.py.mako`
   - `backend/migrations/versions/.gitkeep`
2. Nutze dieselbe DB-Konfiguration wie das Backend.
3. Dokumentiere Alembic-Befehle in `backend/README.md`.
4. Stelle sicher, dass Migrationen gegen remote PostgreSQL ausführbar sind.
5. Vermeide Autogeneration als zwingende Voraussetzung.

Akzeptanzkriterien:
- `alembic current` ist ausführbar.
- `alembic upgrade head` ist ausführbar, auch wenn noch keine Migration existiert.
- DB-URL kommt aus Umgebungsvariablen.
- Alembic liegt klar im Backend.
- Keine Fachschema-Migration vorhanden.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Alembic-Befehle.
- Annahmen.
```

### Prompt 2.3: Backend-Testbasis einrichten

```text
Ziel:
Richte eine minimale Testbasis für das Backend ein.

Kontext:
- FastAPI Backend
- pytest
- Healthchecks als erste testbare Schnittstellen
- DB-Test darf ohne echte DB sauber übersprungen oder kontrolliert fehlschlagen

Nicht ändern:
- Keine Fachlogik testen.
- Keine Auth-Tests erstellen.
- Keine externen Services erzwingen.
- Keine echte Remote-DB als Pflicht für lokale Tests.

Aufgaben:
1. Ergänze Testabhängigkeiten.
2. Erstelle:
   - `backend/tests/conftest.py`
   - `backend/tests/test_health.py`
3. Teste:
   - App importierbar
   - `/health` liefert OK
   - `/health/db` verhält sich kontrolliert bei fehlender DB-Konfiguration
4. Dokumentiere Testausführung.

Akzeptanzkriterien:
- Tests laufen lokal ohne PostgreSQL.
- DB-abhängiger Test ist robust.
- Keine Secrets notwendig.
- Teststruktur ist erweiterbar.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Testbefehl.
- Bekannte Grenzen.
```

## Dokumentation aktualisieren nach Paket 2

```text
Ziel:
Aktualisiere die Projektdokumentation nach Abschluss von Paket 2.

Kontext:
Paket 2 umfasst:
- FastAPI Backend-Grundgerüst
- Konfiguration über Umgebungsvariablen
- Healthchecks
- Alembic initialisiert
- Backend-Testbasis

Aufgaben:
1. Aktualisiere `README.md`:
   - Backend-Setup
   - benötigte Umgebungsvariablen
   - Startbefehl
   - Testbefehl
2. Aktualisiere `backend/README.md`:
   - lokale Installation
   - FastAPI-Start
   - Alembic-Befehle
   - Testausführung
3. Aktualisiere `docs/status.md`:
   - Paket 2 abgeschlossen
   - neue/geänderte Dateien
   - offene Risiken
   - nächstes Paket: M1 Datenmodell-Migrationen

Akzeptanzkriterien:
- Backend ist reproduzierbar startbar.
- Alembic-Nutzung ist dokumentiert.
- Tests sind dokumentiert.
- Status trennt erledigt/offen sauber.

Outputformat:
- Geänderte Dateien.
- Zusammenfassung.
- Nächster Schritt.
```

### 8. Benutzer

weiter

### 9. Assistent

## Paket 3: M1 Datenmodell und initiale Migrationen

### Prompt 3.1: Initiale Schema-Migration für Basisentitäten

```text
Ziel:
Erstelle die initiale Alembic-Migration für vorbereitete Mehrbenutzerfähigkeit und Dokumentbasis.

Kontext:
- V1 ist Single-User ohne Auth.
- Datenmodell muss spätere Workspaces und Users vorbereiten.
- Auth-Logik wird nicht implementiert.
- PostgreSQL ist Zielsystem.
- Migrationen liegen unter `backend/migrations/`.

Nicht ändern:
- Keine Login-, Passwort- oder Session-Auth-Logik.
- Keine Rollen-/Rechteprüfung.
- Keine Importpipeline.
- Keine Chatlogik.

Aufgaben:
1. Erstelle eine Alembic-Revision für:
   - `workspaces`
   - `users`
   - `documents`
   - `document_versions`
2. Lege Default-Datensätze an:
   - Default-Workspace
   - Default-User
3. Modellierung:
   - `documents.workspace_id`
   - `documents.owner_user_id`
   - `documents.current_version_id`
   - `documents.title`
   - `documents.source_type`
   - `documents.mime_type`
   - `documents.content_hash`
   - `documents.created_at`
   - `documents.updated_at`
4. Modellierung:
   - `document_versions.document_id`
   - `document_versions.version_number`
   - `document_versions.normalized_markdown`
   - `document_versions.markdown_hash`
   - `document_versions.parser_version`
   - `document_versions.ocr_used`
   - `document_versions.ki_provider`
   - `document_versions.ki_model`
   - `document_versions.metadata`
   - `document_versions.created_at`
5. Ergänze sinnvolle Constraints und Indizes.
6. Stelle Downgrade-Fähigkeit sicher.

Akzeptanzkriterien:
- Migration läuft auf PostgreSQL.
- Default-Workspace und Default-User existieren.
- Dokumente referenzieren Workspace und Owner.
- Jede Dokumentversion gehört zu genau einem Dokument.
- `current_version_id` kann gesetzt werden.
- Keine aktive Auth-Logik.
- Downgrade entfernt Tabellen kontrolliert.

Outputformat:
- Kurze Analyse.
- Neue Migration.
- Tabellenübersicht.
- Constraints/Indizes.
- Risiken.
```

### Prompt 3.2: Migration für Chunks und Quellenanker

```text
Ziel:
Erstelle die Migration für Dokument-Chunks mit zitierfähigen Quellenankern.

Kontext:
- Chunks entstehen aus `document_versions.normalized_markdown`.
- Tabellen sollen möglichst nicht zerlegt werden.
- Quellenanker müssen spätere Chat-Zitate ermöglichen.
- Suche läuft später über Chunks.

Nicht ändern:
- Keine Chunking-Implementierung.
- Keine Suchlogik.
- Keine Chatlogik.
- Keine Vektorsuche als Pflichtbestandteil.

Aufgaben:
1. Erstelle Alembic-Revision für `document_chunks`.
2. Felder:
   - `id`
   - `document_id`
   - `document_version_id`
   - `chunk_index`
   - `heading_path`
   - `anchor`
   - `content`
   - `content_hash`
   - `token_estimate`
   - `metadata`
   - `created_at`
3. Constraints:
   - Chunk gehört zu Dokument und Version.
   - `(document_version_id, chunk_index)` eindeutig.
   - `anchor` pro Version eindeutig.
4. Indizes:
   - `document_id`
   - `document_version_id`
   - `content_hash`
   - optional GIN/Fulltext-Vorbereitung, falls sinnvoll ohne Suchservice.
5. Downgrade sauber implementieren.

Akzeptanzkriterien:
- Chunks sind versioniert.
- Quellenanker sind eindeutig zitierbar.
- Schema unterstützt Tabellen-Metadaten.
- Migration ist unabhängig von Importlogik.
- Downgrade funktioniert.

Outputformat:
- Kurze Analyse.
- Neue Migration.
- Tabellenübersicht.
- Begründung für Anchor-Modell.
- Risiken.
```

### Prompt 3.3: Migration für Kategorien, Tags und Dokument-Tag-Verknüpfung

```text
Ziel:
Erstelle die Migration für Kategorien, Tags und additive Tag-Zuordnung.

Kontext:
- Kategorien und Tags werden getrennt modelliert.
- KI-Tags und manuelle Tags werden additiv geführt.
- Manuelle Tags dürfen KI-Tags nicht automatisch überschreiben.
- V1 ohne Benutzerlogik, aber owner_user_id ist vorbereitet.

Nicht ändern:
- Keine UI.
- Keine Tagging-KI.
- Keine Importpipeline.
- Keine Rechteprüfung.

Aufgaben:
1. Erstelle Alembic-Revision für:
   - `categories`
   - `tags`
   - `document_tags`
2. Kategorien:
   - `id`
   - `workspace_id`
   - `name`
   - `description`
   - `created_at`
   - `updated_at`
3. Tags:
   - `id`
   - `workspace_id`
   - `name`
   - `normalized_name`
   - `created_at`
   - `updated_at`
4. DocumentTags:
   - `document_id`
   - `tag_id`
   - `source`
   - `confidence`
   - `created_by_user_id`
   - `created_at`
5. `source` als kontrollierte Werte modellieren:
   - `manual`
   - `ki`
   - `import`
6. Ergänze Constraints:
   - Tag-Namen pro Workspace eindeutig.
   - Kategorie-Namen pro Workspace eindeutig.
   - Dokument-Tag-Kombination mit Source eindeutig, falls fachlich sinnvoll.
7. Downgrade sauber implementieren.

Akzeptanzkriterien:
- KI- und manuelle Tags können parallel existieren.
- Tags sind workspace-fähig.
- Keine Auth-Logik nötig.
- Eindeutigkeit verhindert Dubletten.
- Downgrade funktioniert.

Outputformat:
- Kurze Analyse.
- Neue Migration.
- Tabellenübersicht.
- Constraints.
- Risiken.
```

### Prompt 3.4: Migration für Chat- und Analyse-Grundtabellen

```text
Ziel:
Erstelle die Grundtabellen für spätere Chat- und Analysefunktionen.

Kontext:
- Chat V1 ist Pflicht, Umsetzung später.
- Analyse, Merge, Refine und Commit folgen später.
- Tabellen sollen nur Persistenz vorbereiten, keine Logik implementieren.
- Quellenbezüge müssen nachvollziehbar bleiben.

Nicht ändern:
- Keine Chat-Service-Implementierung.
- Keine Analyse-Service-Implementierung.
- Keine KI-Provider-Logik.
- Keine UI.

Aufgaben:
1. Erstelle Alembic-Revision für:
   - `chat_sessions`
   - `chat_messages`
   - `analysis_groups`
   - `analysis_group_documents`
   - `analysis_results`
   - `analysis_result_sources`
2. Chat Sessions:
   - Workspace/User vorbereitet
   - Titel
   - Zeitstempel
3. Chat Messages:
   - Session-Bezug
   - Rolle
   - Inhalt
   - Kennzeichnung `basis_type`: `knowledge_base`, `general`, `mixed`, `unknown`
   - Quellen-Metadaten
4. Analysis Groups:
   - Workspace/User vorbereitet
   - Titel
   - Status
5. Analysis Results:
   - Typ: `merge`, `compare`, `refine`
   - Status
   - Ergebnis-Markdown
   - Commit-Bezug optional
6. Sources:
   - Bezug auf Dokument, Version, Chunk optional aber modellierbar
7. Ergänze Constraints und Indizes.
8. Downgrade sauber implementieren.

Akzeptanzkriterien:
- Chat-Sessions und Messages sind speicherbar.
- Allgemeine Antworten können von Wissensbasis-Antworten unterschieden werden.
- Analyseergebnisse können vor Commit gespeichert werden.
- Quellenbezug bleibt modellierbar.
- Keine Fachlogik implementiert.
- Downgrade funktioniert.

Outputformat:
- Kurze Analyse.
- Neue Migration.
- Tabellenübersicht.
- Status-/Typwerte.
- Risiken.
```

### Prompt 3.5: Migrationstests für M1-Schema

```text
Ziel:
Erstelle Tests für die M1-Migrationen und grundlegende Schemaannahmen.

Kontext:
- Alembic-Migrationen sollen stabil sein.
- Lokale Tests dürfen keine echte Remote-DB erzwingen.
- Tests können eine konfigurierte PostgreSQL-Testdatenbank nutzen.
- Ohne Test-DB müssen DB-Tests kontrolliert übersprungen werden.

Nicht ändern:
- Keine Fachservice-Tests.
- Keine Importtests.
- Keine UI-Tests.
- Keine Auth-Tests.

Aufgaben:
1. Ergänze Teststruktur für Migrationen.
2. Prüfe:
   - Alembic-Konfiguration importierbar.
   - Migrationen haben eindeutige Revisionen.
   - Upgrade/Downgrade gegen Test-DB, falls `TEST_DATABASE_URL` gesetzt ist.
   - Default-Workspace und Default-User existieren nach Upgrade.
   - Kernconstraints verhindern offensichtliche Dubletten.
3. Dokumentiere Testvoraussetzungen.

Akzeptanzkriterien:
- Tests laufen ohne DB und überspringen DB-abhängige Fälle sauber.
- Mit `TEST_DATABASE_URL` werden Migrationen real geprüft.
- Fehler sind nachvollziehbar.
- Kein Secret wird geloggt.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Testbefehl.
- Übersprunglogik.
- Risiken.
```

## Dokumentation aktualisieren nach Paket 3

```text
Ziel:
Aktualisiere die Projektdokumentation nach Abschluss von Paket 3.

Kontext:
Paket 3 umfasst:
- Initiale M1-Datenbankmigrationen
- Workspaces/Users vorbereitet
- Documents/DocumentVersions
- Chunks mit Quellenankern
- Kategorien/Tags/DocumentTags
- Chat- und Analyse-Grundtabellen
- Migrationstests

Aufgaben:
1. Aktualisiere `docs/status.md`:
   - Paket 3 abgeschlossen
   - neue Migrationen
   - offene Risiken
   - nächstes Paket
2. Erstelle oder aktualisiere `docs/data-model.md`:
   - Tabellenübersicht
   - wichtigste Beziehungen
   - Versionierungsprinzip
   - Chunk-/Quellenankerprinzip
   - Tag-Prinzip
   - Chat-/Analyse-Vorbereitung
3. Aktualisiere `backend/README.md`:
   - Migration ausführen
   - Migration testen
   - relevante Umgebungsvariablen
4. Stelle klar:
   - Auth ist nicht implementiert.
   - Mehrbenutzerfähigkeit ist nur vorbereitet.
   - Originaldateien werden nicht gespeichert.

Akzeptanzkriterien:
- Datenmodell ist ohne Codelektüre verständlich.
- V1-Grenzen bleiben sichtbar.
- Migrationen sind reproduzierbar dokumentiert.
- Paket 4 ist als nächster Schritt erkennbar.

Outputformat:
- Geänderte Dateien.
- Zusammenfassung.
- Offene Risiken.
```

### 10. Benutzer

weiter

### 11. Assistent

## Paket 4: M2 Importpipeline-Grundlage

### Prompt 4.1: Import-Service-Schnittstellen definieren

```text
Ziel:
Definiere die Backend-Schnittstellen für die Importpipeline ohne vollständige Parser-Implementierung.

Kontext:
- Import unterstützt später DOC, DOCX, TXT, MD und PDF.
- Scan-PDF und Text-PDF laufen über denselben Importpfad.
- Originaldateien werden nicht gespeichert.
- Persistiert wird normalisiertes Markdown plus Metadaten.
- OCR läuft lokal.
- KI-Normalisierung läuft über austauschbares Provider-Interface.

Nicht ändern:
- Keine vollständige OCR-Implementierung.
- Keine vollständige PDF-/DOCX-Implementierung.
- Keine Chatlogik.
- Keine UI.
- Keine Speicherung von Originaldateien.

Aufgaben:
1. Erstelle Backend-Module:
   - `backend/app/services/import_service.py`
   - `backend/app/services/parser_service.py`
   - `backend/app/services/ocr_service.py`
   - `backend/app/services/markdown_normalizer.py`
   - `backend/app/services/ki_provider.py`
   - `backend/app/models/import_models.py`
2. Definiere Interfaces/Protokolle für:
   - Parser
   - OCR
   - KI-Provider
   - Normalizer
3. Definiere Datenklassen oder Pydantic-Modelle für:
   - ImportRequest
   - ExtractedContent
   - NormalizedDocument
   - ImportResult
   - ImportError
4. Stelle sicher:
   - Dateiname und MIME-Type dürfen als Metadaten gespeichert werden.
   - Originaldatei-Inhalt wird nicht persistiert.
   - Hashing ist vorbereitet.
   - Fallbacks bei Parser-/KI-Fehlern sind modelliert.

Akzeptanzkriterien:
- Importpipeline ist als klarer Ablauf modelliert.
- Provider und Parser sind austauschbar.
- Keine Fachpersistenz wird hart verdrahtet.
- Fehlerfälle sind explizit modelliert.
- Kein Originaldateispeicher entsteht.

Outputformat:
- Kurze Analyse.
- Neue/geänderte Dateien.
- Schnittstellenübersicht.
- Risiken.
```

### Prompt 4.2: TXT- und MD-Parser implementieren

```text
Ziel:
Implementiere die ersten produktionsnahen Parser für TXT und Markdown.

Kontext:
- TXT/MD sind der minimale vertikale Importpfad.
- Markdown bleibt kanonische Textquelle.
- Tabellen in Markdown müssen erhalten bleiben.
- Parser liefern extrahierten Text/Markdown und Metadaten.
- Persistenz erfolgt noch nicht in diesem Task, außer vorhandene Service-Grenzen erfordern es ausdrücklich.

Nicht ändern:
- Keine DOCX-Implementierung.
- Keine PDF-Implementierung.
- Keine OCR-Implementierung.
- Keine KI-Normalisierung erzwingen.
- Keine UI.

Aufgaben:
1. Implementiere TXT-Parser.
2. Implementiere MD-Parser.
3. Erkenne Encoding robust:
   - UTF-8 bevorzugt
   - kontrollierter Fallback
4. Erzeuge Content-Hash.
5. Erzeuge Parser-Metadaten:
   - parser_name
   - parser_version
   - mime_type
   - source_filename
   - byte_size
6. Bewahre Markdown-Tabellen unverändert.
7. Ergänze Unit-Tests.

Akzeptanzkriterien:
- TXT-Dateien werden zu Markdown-kompatiblem Text.
- MD-Dateien werden möglichst unverändert übernommen.
- Hashes sind stabil.
- Fehlerhafte Encodings führen zu kontrolliertem Fehler oder Fallback.
- Tests decken TXT, MD, leere Datei, Sonderzeichen und Tabellen ab.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Testbefehl.
- Bekannte Grenzen.
```

### Prompt 4.3: Markdown-Normalizer V1 implementieren

```text
Ziel:
Implementiere einen deterministischen Markdown-Normalizer ohne inhaltliche Interpretation.

Kontext:
- KI-Normalisierung kommt später ergänzend.
- Normalizer darf strukturieren, aber Inhalte nicht fachlich verändern.
- Tabellen sollen möglichst verlustfrei erhalten bleiben.
- Fehlerhafter KI-Output darf Import nicht blockieren.
- Dieser Task fokussiert deterministische Normalisierung.

Nicht ändern:
- Keine KI-Umschreibung.
- Keine Zusammenfassung.
- Keine semantische Interpretation.
- Keine Chatlogik.
- Keine UI.

Aufgaben:
1. Implementiere `MarkdownNormalizer`.
2. Normalisiere:
   - Zeilenenden
   - führende/trailing Leerzeichen
   - mehrere Leerzeilen
   - fehlende Abschluss-Newline
3. Erhalte:
   - Markdown-Tabellen
   - Codeblöcke
   - Überschriften
   - Listen
4. Erzeuge:
   - normalized_markdown
   - markdown_hash
   - normalization_metadata
5. Ergänze Tests für:
   - Tabellen
   - Codeblöcke
   - Listen
   - Windows-Zeilenenden
   - Leerzeilen
   - leere Inhalte

Akzeptanzkriterien:
- Normalisierung ist deterministisch.
- Inhalte werden nicht umgedeutet.
- Tabellen bleiben strukturell erhalten.
- Hash bleibt bei identischem Normalisierungsergebnis stabil.
- Tests dokumentieren Grenzen.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Testbefehl.
- Risiken.
```

### Prompt 4.4: Chunking-Service V1 implementieren

```text
Ziel:
Implementiere einen ersten Chunking-Service für normalisiertes Markdown mit Quellenankern.

Kontext:
- Chunks entstehen aus `normalized_markdown`.
- Tabellen sollen nicht zerteilt werden, wenn technisch vermeidbar.
- Jeder Chunk bekommt Quellenanker.
- Quellenanker müssen spätere Chat-Zitate ermöglichen.
- Persistenz kann vorbereitet, aber nicht zwingend vollständig integriert werden.

Nicht ändern:
- Keine Vektorsuche.
- Keine Chatlogik.
- Keine Rankinglogik.
- Keine UI.
- Keine KI-Interpretation.

Aufgaben:
1. Erstelle `backend/app/services/chunking_service.py`.
2. Definiere Chunk-Modell:
   - chunk_index
   - heading_path
   - anchor
   - content
   - content_hash
   - token_estimate
   - metadata
3. Chunking-Regeln:
   - primär nach Überschriften
   - sekundär nach Absatzgrenzen
   - Tabellenblöcke zusammenhalten
   - Codeblöcke zusammenhalten
4. Quellenanker-Format:
   - stabil pro Dokumentversion
   - maschinenlesbar
   - eindeutig innerhalb einer Version
5. Ergänze Tests:
   - Überschriften
   - lange Absätze
   - Tabellen
   - Codeblöcke
   - leere Inhalte
   - doppelte Überschriften

Akzeptanzkriterien:
- Jeder Chunk hat eindeutigen Anchor.
- Tabellen werden nicht unnötig zerteilt.
- Chunks sind deterministisch.
- Token-Schätzung ist nachvollziehbar.
- Tests decken Edge Cases ab.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Testbefehl.
- Risiken.
```

### Prompt 4.5: Minimalen Import-Endpunkt für TXT/MD bauen

```text
Ziel:
Baue einen minimalen Import-Endpunkt für TXT und Markdown inklusive Persistenz als Dokumentversion und Chunks.

Kontext:
- DB-Schema aus M1 existiert.
- TXT/MD-Parser existieren.
- Markdown-Normalizer existiert.
- Chunking-Service existiert.
- Originaldateien werden nicht gespeichert.
- V1 nutzt Default-Workspace und Default-User.

Nicht ändern:
- Keine DOCX/PDF/OCR-Implementierung.
- Keine KI-Tags erzwingen.
- Keine Auth.
- Keine UI.
- Keine Speicherung der Originaldatei.

Aufgaben:
1. Erstelle API-Route:
   - `POST /documents/import`
2. Akzeptiere Uploads für:
   - `.txt`
   - `.md`
3. Ablauf:
   - Datei temporär lesen
   - Content-Hash berechnen
   - Parser auswählen
   - Markdown normalisieren
   - Dokument anlegen
   - Dokumentversion 1 anlegen
   - current_version_id setzen
   - Chunks erzeugen und speichern
   - Originalinhalt verwerfen
4. Duplikaterkennung:
   - gleicher `content_hash` soll kontrolliert behandelt werden
   - keine stillen Dubletten
5. Antwort enthält:
   - document_id
   - version_id
   - title
   - chunk_count
   - duplicate_status
6. Ergänze Integrationstests mit optionaler Test-DB.

Akzeptanzkriterien:
- TXT/MD können importiert werden.
- Keine Originaldatei wird gespeichert.
- Dokumentversion und Chunks entstehen.
- Duplicate-Handling ist transparent.
- Tests ohne DB werden sauber übersprungen.
- Fehlerhafte Dateitypen liefern klare Fehler.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- API-Beispiel.
- Testbefehl.
- Risiken.
```

## Dokumentation aktualisieren nach Paket 4

```text
Ziel:
Aktualisiere die Projektdokumentation nach Abschluss von Paket 4.

Kontext:
Paket 4 umfasst:
- Import-Service-Schnittstellen
- TXT/MD-Parser
- deterministischen Markdown-Normalizer
- Chunking-Service mit Quellenankern
- minimalen Import-Endpunkt für TXT/MD

Aufgaben:
1. Aktualisiere `docs/status.md`:
   - Paket 4 abgeschlossen
   - neue/geänderte Module
   - bekannte Grenzen
   - nächstes Paket
2. Erstelle oder aktualisiere `docs/import-pipeline.md`:
   - Importablauf
   - Parser-Grenzen
   - Normalisierungsregeln
   - Chunking-Regeln
   - Duplicate-Handling
   - Speicherentscheidung: keine Originaldateien
3. Aktualisiere `backend/README.md`:
   - Import-Endpunkt
   - Beispiel mit curl
   - unterstützte Dateitypen
   - Testvoraussetzungen
4. Aktualisiere `docs/data-model.md` falls konkrete Persistenzdetails ergänzt wurden.

Akzeptanzkriterien:
- Importpipeline ist nachvollziehbar dokumentiert.
- Speichergrenzen sind eindeutig.
- Bekannte Einschränkungen sind sichtbar.
- Paket 5 ist klar vorbereitet.

Outputformat:
- Geänderte Dateien.
- Zusammenfassung.
- Offene Risiken.
```

### 12. Benutzer

weiter

### 13. Assistent

## Paket 5: M2 DOCX/PDF/OCR und KI-Provider

### Prompt 5.1: DOCX-Parser implementieren

```text
Ziel:
Implementiere den DOCX-Parser für die Importpipeline.

Kontext:
- Importpipeline aus Paket 4 existiert.
- Originaldateien werden nicht gespeichert.
- Persistiert wird normalisiertes Markdown.
- Tabellen sollen möglichst verlustfrei erhalten bleiben.
- DOCX ist Pflichtbestandteil von V1.
- DOC-Altdokumente werden separat behandelt.

Nicht ändern:
- Keine OCR-Logik.
- Keine PDF-Logik.
- Keine Chatlogik.
- Keine UI.
- Keine Speicherung der Originaldatei.

Aufgaben:
1. Implementiere `DocxParser`.
2. Extrahiere:
   - Absätze
   - Überschriften, soweit erkennbar
   - Listen, soweit erkennbar
   - Tabellen als Markdown-Tabellen
3. Erfasse Metadaten:
   - parser_name
   - parser_version
   - mime_type
   - source_filename
   - byte_size
   - table_count
   - paragraph_count
4. Integriere Parser-Auswahl für `.docx`.
5. Ergänze Tests für:
   - einfaches DOCX
   - DOCX mit Tabelle
   - DOCX mit Überschriften
   - leeres oder beschädigtes DOCX
6. Fehler müssen kontrolliert als Importfehler modelliert werden.

Akzeptanzkriterien:
- DOCX-Dateien werden in Markdown überführt.
- Tabellen bleiben als Markdown-Tabellen erhalten.
- Beschädigte Dateien führen zu kontrolliertem Fehler.
- Keine Originaldatei wird persistiert.
- Parser ist austauschbar und isoliert testbar.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Testbefehl.
- Bekannte Grenzen.
```

### Prompt 5.2: DOC-Altdokumente behandeln

```text
Ziel:
Definiere und implementiere die V1-Behandlung für alte `.doc`-Dateien.

Kontext:
- V1 fordert Import für DOC.
- `.doc` ist technisch riskanter als `.docx`.
- Lösung muss lokal laufen.
- Originaldateien werden nicht gespeichert.
- Fehler müssen transparent sein.

Nicht ändern:
- Keine Cloud-Konvertierung.
- Keine Speicherung der Originaldatei.
- Keine stillen Fallbacks ohne Status.
- Keine UI.

Aufgaben:
1. Prüfe vorhandene Abhängigkeiten und entscheide einen lokalen Ansatz:
   - bevorzugt über LibreOffice Headless, falls im Projekt akzeptiert
   - alternativ kontrollierter „nicht unterstützt ohne Converter“-Status
2. Implementiere `DocParser` als klar gekapselten Adapter.
3. Falls LibreOffice genutzt wird:
   - `.doc` temporär nach `.docx` oder Text konvertieren
   - temporäre Dateien nach Verarbeitung löschen
   - anschließend bestehenden Parserpfad verwenden
4. Falls kein Converter verfügbar:
   - klarer Importfehler mit Handlungshinweis
5. Ergänze Tests:
   - Converter nicht verfügbar
   - ungültige `.doc`
   - temporäre Datei wird gelöscht
6. Dokumentiere Systemabhängigkeit.

Akzeptanzkriterien:
- `.doc` wird nicht still ignoriert.
- Verhalten ist deterministisch.
- Keine Originaldatei bleibt gespeichert.
- Systemabhängigkeit ist explizit.
- Fehlerstatus ist für Nutzer verständlich.

Outputformat:
- Kurze Analyse.
- Entscheidung.
- Geänderte Dateien.
- Testbefehl.
- Risiken.
```

### Prompt 5.3: PDF-Parser mit Text-PDF-Pfad implementieren

```text
Ziel:
Implementiere den PDF-Parser für direkt extrahierbare Text-PDFs.

Kontext:
- Scan-PDF und Text-PDF laufen über denselben Importpfad.
- OCR-Fallback kommt im nächsten Task.
- Originaldateien werden nicht gespeichert.
- Persistiert wird normalisiertes Markdown.
- Quellenanker müssen später Seitenbezug ermöglichen.

Nicht ändern:
- Noch keine OCR-Fallback-Implementierung.
- Keine Chatlogik.
- Keine UI.
- Keine Vektorsuche.
- Keine Speicherung der Originaldatei.

Aufgaben:
1. Implementiere `PdfParser`.
2. Extrahiere Text pro Seite.
3. Erzeuge Markdown mit Seitenmarkern, z. B.:
   - `<!-- page:1 -->`
   - `## Seite 1`
4. Erfasse Metadaten:
   - page_count
   - extraction_method = text
   - parser_name
   - parser_version
   - mime_type
   - source_filename
   - byte_size
5. Entscheide transparent, wann Textmenge nicht ausreichend ist und OCR nötig wäre.
6. Integriere Parser-Auswahl für `.pdf`.
7. Ergänze Tests:
   - Text-PDF
   - leere PDF
   - beschädigte PDF
   - PDF mit sehr wenig extrahierbarem Text

Akzeptanzkriterien:
- Text-PDFs werden importfähig extrahiert.
- Seitenbezug bleibt im Markdown erhalten.
- OCR-Bedarf wird erkannt, aber noch nicht ausgeführt.
- Beschädigte PDFs liefern kontrollierte Fehler.
- Keine Originaldatei wird persistiert.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Testbefehl.
- OCR-Grenzwert.
- Risiken.
```

### Prompt 5.4: Lokalen OCR-Service integrieren

```text
Ziel:
Integriere einen lokalen OCR-Service als Fallback für nicht direkt extrahierbare PDFs.

Kontext:
- OCR muss lokal laufen.
- Scan-PDF und Text-PDF laufen über denselben Importpfad.
- OCR-Confidence soll gespeichert oder in Metadaten geführt werden.
- Fehlerhafte OCR darf Import kontrolliert abbrechen oder validierbaren Fallback liefern.
- Originaldateien werden nicht gespeichert.

Nicht ändern:
- Keine Cloud-OCR.
- Keine Chatlogik.
- Keine UI.
- Keine Speicherung der Originaldatei.

Aufgaben:
1. Implementiere `LocalOcrService`.
2. Nutze eine lokal ausführbare OCR-Strategie:
   - Tesseract oder vergleichbare lokale Abhängigkeit
   - PDF-Seiten werden temporär gerendert
3. Extrahiere OCR-Text pro Seite.
4. Erfasse:
   - ocr_used = true
   - ocr_engine
   - ocr_language
   - confidence, falls verfügbar
   - pages_processed
   - failed_pages
5. Integriere OCR-Fallback in `PdfParser`.
6. Temporäre Bild-/PDF-Dateien sicher löschen.
7. Ergänze Tests:
   - OCR-Service nicht installiert
   - OCR-Fallback wird angefordert
   - temporäre Dateien werden gelöscht
   - Fehler pro Seite wird sauber modelliert

Akzeptanzkriterien:
- OCR läuft lokal oder liefert klaren Konfigurationsfehler.
- OCR-Fallback ist im PDF-Importpfad integriert.
- Metadaten zeigen OCR-Nutzung.
- Keine temporären Originaldaten bleiben liegen.
- Importfehler sind kontrolliert.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Systemabhängigkeiten.
- Testbefehl.
- Risiken.
```

### Prompt 5.5: Ollama-Provider-Interface und Fallback-Normalisierung

```text
Ziel:
Implementiere das KI-Provider-Interface mit lokalem Ollama-Provider und sicherem Fallback.

Kontext:
- KI-Normalisierung läuft lokal via Ollama.
- Provider muss später austauschbar sein.
- KI darf Inhalte strukturieren, aber nicht unkontrolliert verändern.
- Fehlerhafter KI-Output darf Import nicht zwingend blockieren.
- Deterministischer Normalizer aus Paket 4 bleibt Fallback.

Nicht ändern:
- Keine Cloud-KI.
- Keine Chatlogik.
- Keine UI.
- Keine semantische Zusammenfassung im Import.
- Keine Überschreibung ohne Validierung.

Aufgaben:
1. Definiere KI-Provider-Protokoll final.
2. Implementiere `OllamaProvider`.
3. Konfiguration über Umgebungsvariablen:
   - OLLAMA_BASE_URL
   - OLLAMA_MODEL
   - KI_NORMALIZATION_ENABLED
4. Implementiere Normalisierungsablauf:
   - deterministische Normalisierung zuerst
   - optional KI-Strukturierung
   - Validierung des KI-Ergebnisses
   - Fallback auf deterministische Version bei Fehlern
5. Validierung:
   - nicht leer
   - Mindestähnlichkeit oder Längenverhältnis plausibel
   - Tabellenmarker nicht offensichtlich zerstört
6. Metadaten speichern:
   - ki_provider
   - ki_model
   - ki_used
   - ki_fallback_used
   - validation_warnings
7. Ergänze Tests mit gemocktem Provider.

Akzeptanzkriterien:
- Import funktioniert ohne Ollama.
- Ollama kann optional genutzt werden.
- Fehlerhafter KI-Output blockiert nicht zwingend.
- Provider ist austauschbar.
- Metadaten machen KI-Nutzung transparent.
- Tests brauchen keinen echten Ollama-Server.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- Konfigurationsvariablen.
- Testbefehl.
- Risiken.
```

### Prompt 5.6: Import-Endpunkt auf DOCX/DOC/PDF erweitern

```text
Ziel:
Erweitere den bestehenden Import-Endpunkt auf alle V1-Dateitypen.

Kontext:
- Bestehender Import-Endpunkt unterstützt TXT/MD.
- Neue Parser für DOCX, DOC und PDF existieren.
- OCR-Fallback existiert.
- KI-Provider ist optional integriert.
- Originaldateien werden nicht gespeichert.

Nicht ändern:
- Keine UI.
- Keine Chatlogik.
- Keine Suche.
- Keine Vektorsuche.
- Keine Auth.

Aufgaben:
1. Erweitere `POST /documents/import` für:
   - `.txt`
   - `.md`
   - `.doc`
   - `.docx`
   - `.pdf`
2. Vereinheitliche Fehlerantworten:
   - unsupported_file_type
   - parser_failed
   - ocr_required_but_unavailable
   - ki_validation_failed_fallback_used
   - duplicate_detected
3. Stelle sicher:
   - temporäre Dateien werden gelöscht
   - Originaldatei wird nicht persistiert
   - Dokumentversion und Chunks entstehen
   - OCR- und KI-Metadaten werden gespeichert
4. Ergänze Integrationstests:
   - TXT
   - MD
   - DOCX
   - PDF Text
   - PDF OCR nicht verfügbar
   - unsupported file
   - duplicate content

Akzeptanzkriterien:
- Alle V1-Dateitypen haben einen definierten Importpfad.
- Fehler sind maschinenlesbar.
- OCR/KI-Fallbacks sind transparent.
- Keine Originaldateien bleiben gespeichert.
- Tests sind ohne externe OCR/Ollama robust.

Outputformat:
- Kurze Analyse.
- Geänderte Dateien.
- API-Beispiele.
- Testbefehl.
- Risiken.
```

## Dokumentation aktualisieren nach Paket 5

```text
Ziel:
Aktualisiere die Projektdokumentation nach Abschluss von Paket 5.

Kontext:
Paket 5 umfasst:
- DOCX-Parser
- DOC-Behandlung
- PDF-Textparser
- lokaler OCR-Fallback
- Ollama-Provider mit Fallback-Normalisierung
- Import-Endpunkt für alle V1-Dateitypen

Aufgaben:
1. Aktualisiere `docs/status.md`:
   - Paket 5 abgeschlossen
   - neue Parser
   - Systemabhängigkeiten
   - bekannte Grenzen
   - nächstes Paket
2. Aktualisiere `docs/import-pipeline.md`:
   - unterstützte Dateitypen
   - DOC-Strategie
   - PDF-Textpfad
   - OCR-Fallback
   - KI-Normalisierung
   - Validierung und Fallback
   - temporäre Dateien
3. Aktualisiere `backend/README.md`:
   - zusätzliche Systemabhängigkeiten
   - OCR-Konfiguration
   - Ollama-Konfiguration
   - Import-Beispiele
4. Aktualisiere `docs/data-model.md`:
   - relevante Parser-/OCR-/KI-Metadaten
5. Ergänze Betriebsrisiken:
   - OCR-Qualität
   - LibreOffice/Tesseract-Verfügbarkeit
   - Ollama-Ausfall
   - Importdauer bei großen Dateien

Akzeptanzkriterien:
- Importfähigkeit ist vollständig dokumentiert.
- Externe lokale Systemabhängigkeiten sind explizit.
- Fallback-Verhalten ist verständlich.
- Keine nicht implementierten Funktionen werden als fertig dargestellt.

Outputformat:
- Geänderte Dateien.
- Zusammenfassung.
- Offene Risiken.
```
