---
title: "Weiterentwicklung der Anwendung"
type: chatgpt_conversation
source: chatgpt
source_id: "69e9fc63-2868-8395-873b-01c313dd918c"
created: 2026-04-23
tags:
  - chatgpt
  - code
  - gesundheit
  - import
  - ki
  - obsidian
  - projekt
  - sap
---


# Weiterentwicklung der Anwendung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69e9fc63-2868-8395-873b-01c313dd918c`
- Nachrichten: 55

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Ich prüfe erst die Struktur der Anwendung, die vorhandenen Komponenten und die Konfigurationspunkte für die VPS-SQL-Anbindung. Danach arbeite ich die nächste sinnvolle Ausbau-Stufe direkt auf dieser Basis aus.

### 2. Benutzer

hier ist der aktuelle stand der anwendung. die sql db ist auf meinem vps erreichbar. verwende alles als grundlage zum weiter entwickeln

### 3. Assistent

Die Codebasis ist klein und klar segmentiert: Frontend, Services, Migrationen. Ich prüfe jetzt Build-Fähigkeit, Backend-Architektur und die Stellen, an denen die SQL-Verbindung tatsächlich benutzt wird.

### 4. Assistent

Der größte funktionale Bruch ist schon sichtbar: Import und Settings existieren, Suche und Themen sind im UI noch Platzhalter. Ich baue jetzt den Stand einmal und nutze die Fehler als präzise Ausbau-Liste.

### 5. Assistent

Stand verarbeitet. Ich habe die Anwendung auf Basis des gelieferten Repos funktional weiterentwickelt.

Ergebnis:
- Echte Suche gegen PostgreSQL ergänzt.
- Themenübersicht aus `tags` und `document_tags` ergänzt.
- Frontend-Platzhalter für Suche und Themen durch nutzbare Views ersetzt.
- API-Endpunkte für Suche und Themen ergänzt.
- Build erfolgreich geprüft.

Geänderte Funktionen:
- `POST /api/search`
  - durchsucht `chunks.search_vector`
  - berücksichtigt zusätzlich Dateiname und Tag-Matches
  - liefert pro Dokument den besten Treffer mit Snippet, Score, Tags, Metadaten
- `GET /api/topics`
  - aggregiert Tags nach Dokumentanzahl
  - liefert letzte Zuordnung und Beispieldokumente

Neue/angepasste Dateien:
- `src/services/search.service.ts`
- `src/services/topics.service.ts`
- `src/services/api.ts`
- `src/frontend/search/SearchPage.tsx`
- `src/frontend/search/search.api.ts`
- `src/frontend/search/types.ts`
- `src/frontend/topics/TopicsPage.tsx`
- `src/frontend/topics/topics.api.ts`
- `src/frontend/topics/types.ts`

Build-Status:
- `npm run build` erfolgreich

Wichtige Systemgrenzen:
- Ich kann von hier nicht auf deinen VPS oder deine DB zugreifen, solange keine Laufzeitumgebung mit deinen echten `.env`-Werten hier verfügbar ist.
- Die neue Suche setzt voraus, dass die Migrationen bereits auf der VPS-DB laufen und Daten in `documents`, `chunks`, `tags`, `document_tags` vorhanden sind.
- Ranking ist bewusst einfach gehalten: FTS + Dateiname + Tag-Treffer. Kein semantisches Retrieval, kein Embedding-Layer, kein Re-Ranking.

Artefakt:
[Weiterentwickelter Projektstand als tar.gz](sandbox:/mnt/data/Wissen2026-main-search-topics-updated.tar.gz)

Nächste logische Ausbaustufen, priorisiert:
1. Chat-Endpunkt mit Kontext-Retrieval aus Suchtreffern
2. Dashboard mit DB- und Import-Kennzahlen
3. Themenfilter in der Suche
4. Server-seitige Pagination und Sortierung
5. Persistente Health-/Readiness-Prüfungen für VPS-Betrieb

Technische Bewertung des aktuellen Stands:
- Positiv: klare Trennung Frontend/Service/Migrationen; relationale Struktur tragfähig.
- Engpass: kein produktiver Static-Serving-Pfad für das gebaute Frontend.
- Engpass: keine Authentisierung, keine Rollen, kein Mandantenmodell.
- Risiko: `settings.json` liegt dateibasiert lokal am API-Host; bei Container-Redeploy ohne Volume nicht persistent.
- Risiko: Suchqualität hängt vollständig an Chunking und deutschem `tsvector`; gemischte Sprachbestände werden dadurch schlechter gefunden.
- Risiko: keine Migrationsausführung im App-Startup; Deployment hängt an externem DB-Setup.

Empfohlene Betriebsannahmen für deinen VPS:
- `DATABASE_URL` direkt auf die VPS-Postgres setzen
- `DB_SSL=true`, falls extern erreichbar
- `DB_SSL_CA` nur setzen, wenn Zertifikatsprüfung sauber konfiguriert ist
- API und Frontend getrennt deployen oder API um Static Serving erweitern

Wenn du den nächsten Schritt deterministisch fortsetzen willst, ist der sinnvollste Pfad jetzt: Chat-Retrieval über die neue Suche und ein minimales Antwort-Protokoll mit Quellen.

### 6. Assistent

Ziel: standardisierte, token-effiziente Prompts für die Weiterentwicklung deiner Anwendung. Fokus: minimale Tokens, maximale Steuerbarkeit, deterministische Outputs.

---

## 1. Basis-Prompt (für jede Code-Iteration)

```
ROLE: Senior TypeScript/Node/PostgreSQL Engineer
CONTEXT:
- Stack: React + TS, Node API, PostgreSQL (FTS aktiv)
- DB: documents, chunks(search_vector), tags, document_tags
- Ziel: robuste, produktionsfähige Wissenssuche

CONSTRAINTS:
- Keine Erklärungen
- Nur Code + notwendige SQL
- Bestehende Struktur respektieren
- Keine Breaking Changes ohne Kennzeichnung

TASK:
{konkrete Aufgabe}

OUTPUT:
- Dateien vollständig (keine Ausschnitte)
- Neue Dateien klar benennen
- SQL separat
```

---

## 2. Feature-Prompt: Chat mit Retrieval

```
ROLE: Backend Engineer

INPUT:
- search.service vorhanden
- liefert relevante chunks + documents

TASK:
Implementiere POST /api/chat:
- Input: {query}
- nutzt search.service (top_k=5)
- baut Kontext aus chunks
- Antwortformat:
  {
    answer: string,
    sources: [{document_id, title}]
  }

CONSTRAINTS:
- kein externes LLM
- nur Retrieval + Template-Antwort
- deterministisch

OUTPUT:
- chat.service.ts
- api route
```

---

## 3. Prompt: Ranking verbessern

```
ROLE: Search Engineer

CONTEXT:
- PostgreSQL FTS aktiv
- aktuelle Suche: einfaches Ranking

TASK:
Verbessere Ranking:
- Gewichtung:
  title > tags > chunk
- nutze ts_rank_cd
- boost bei Tag-Match

OUTPUT:
- SQL Query vollständig
- angepasste search.service.ts
```

---

## 4. Prompt: Pagination + Performance

```
ROLE: Backend Performance Engineer

TASK:
Erweitere Suche:
- Pagination (limit, offset)
- Default limit=20, max=100
- Gesamtanzahl zurückgeben

OUTPUT:
- API Änderung
- SQL mit COUNT window function
```

---

## 5. Prompt: Frontend Integration Suche

```
ROLE: React Engineer

TASK:
SearchPage erweitern:
- Input Feld
- Debounce 300ms
- Anzeige:
  - Titel
  - Snippet
  - Tags
- Pagination UI

CONSTRAINTS:
- funktionale Komponenten
- keine externen UI libs

OUTPUT:
- vollständige SearchPage.tsx
- API Call integriert
```

---

## 6. Prompt: Themenfilter

```
ROLE: Fullstack Engineer

TASK:
Filter nach Tags:
- Query param: tags[]
- SQL: JOIN document_tags
- mehrere Tags = AND Filter

OUTPUT:
- Backend Anpassung
- Frontend Filter UI minimal
```

---

## 7. Prompt: Produktionsbetrieb VPS

```
ROLE: DevOps Engineer

TASK:
Bereitstellung:
- Node API + React Build
- Nginx Config
- PM2 Setup
- ENV Handling (.env)

OUTPUT:
- nginx.conf
- ecosystem.config.js
- Deployment Steps
```

---

## 8. Prompt: Datenqualität / Chunking

```
ROLE: Data Engineer

TASK:
Verbessere Chunking:
- max 500 tokens pro chunk
- Overlap 50 tokens
- Sprache erkennen (de/en)

OUTPUT:
- chunking function TS
- Begründung kurz in Kommentaren
```

---

## 9. Prompt: Fehleranalyse

```
ROLE: Debugging Engineer

INPUT:
{Fehlerlog}

TASK:
- Root Cause
- Fix

OUTPUT:
- konkrete Codeänderung
- keine Theorie
```

---

## 10. Meta-Prompt (für zukünftige Anforderungen)

```
Analysiere die bestehende Codebasis.

Liefere:
1. Architekturproblem
2. Skalierungsrisiko
3. Konkrete Verbesserung (Code-Level)

Constraints:
- max 150 Tokens
- keine Wiederholung
```

---

## Systemlogik hinter den Prompts

- Rollen erzwingen Spezialisierung
- Constraints eliminieren Token-Verschwendung
- Output-Format verhindert unstrukturierte Antworten
- Keine offenen Fragen → deterministischer Verlauf
- Fokus auf Dateien statt Erklärtext

---

## Schwächen / Risiken

- Kein LLM im Chat → begrenzte Antwortqualität
- FTS-only → kein semantisches Matching
- Tag-System als Themenproxy → inkonsistent bei schlechter Pflege
- Kein Caching → steigende DB-Last

---

## Erweiterung (wenn nötig)

Separater Prompt für Embeddings + Vektor-DB vorbereiten.

---

Ende.

### 7. Benutzer

schreibe mir immer die passenden prompts. achte darauf das sie tokenparrend sind.

### 8. Assistent

Ich prüfe die aktuelle ZIP gegen den zuletzt bearbeiteten Stand und extrahiere daraus genau die drei Punkte in komprimierter Form.

### 9. Benutzer

Analysiere die bestehende Codebasis.



Liefere:

1. Architekturproblem

2. Skalierungsrisiko

3. Konkrete Verbesserung (Code-Level)



Constraints:

- max 150 Tokens

- keine Wiederholung

### 10. Assistent

1. **Architekturproblem**  
API enthält Routing, Provider-Checks, Importlogik und Persistenzzugriff in engem Verbund. Folge: hohe Kopplung, geringe Testbarkeit, langsame Änderungen, Fehler schlagen über mehrere Schichten durch.

2. **Skalierungsrisiko**  
Import läuft prozesslokal mit In-Memory-Status (`previewTokens`, `importHistory`) und synchroner Verarbeitung. Bei mehreren Instanzen gehen Zustände verloren; große Imports blockieren CPU/RAM und erzeugen ungleichmäßige DB-Last.

3. **Konkrete Verbesserung (Code-Level)**  
`src/services/api.ts` in Router/Handler zerlegen; Importstatus in PostgreSQL persistieren; Preview/Execute als Job-Tabelle modellieren; Datei-Parsing in Worker auslagern; `import.service.ts` nur Orchestrierung, Parser je Format in eigene Module; Connection-Pool und Query-Timeouts zentral härten.

### 11. Assistent

Ich gleiche die neue Anforderung mit der Codebasis ab und formuliere daraus einen kompakten Implementierungs-Prompt, der auf die vorhandene Struktur passt.

### 12. Benutzer

Neuer Menüpunkt "Daten Analyse". in diesem bereich werden inhalte zum gleichen themen angezeigt. durch auswahl einzelner inhalte sollen diese per ki zusammengeführt werden und inhaltlich struktureiert aufbereitet dargestellt werden. durch button Übernahme wird das Ergebnis inkl. 10 Stichwörter oder passender Themen in die DB überführt

### 13. Assistent

Passender Prompt für diese Anforderung, auf deine Codebasis zugeschnitten:

```text
ROLE: Senior Fullstack Engineer

CONTEXT:
- Stack: React + TypeScript Frontend, Node HTTP API ohne Framework, PostgreSQL
- Navigation in src/frontend/App.tsx und Layout.tsx
- API zentral in src/services/api.ts
- Datenmodell vorhanden: documents, chunks, tags, document_tags
- Suche/Themen bereits als eigene Views organisiert

TASK:
Implementiere neuen Menüpunkt "Daten Analyse".

FUNKTION:
1. Neuer View "analysis" in App.tsx + Layout.tsx
2. Seite zeigt Gruppen von inhaltlich ähnlichen Dokumenten/Themen
3. Nutzer kann mehrere Inhalte auswählen
4. Button "Mit KI zusammenführen"
5. Backend erstellt strukturierte Zusammenfassung aus ausgewählten Dokumenten:
   - titel
   - kurzfassung
   - kernpunkte[]
   - strukturierte_abschnitte[{heading, content}]
   - stichwoerter[10]
6. Button "Übernahme"
7. Übernahme speichert Ergebnis als neues Dokument in DB
8. Zusätzlich 10 Stichwörter/Themen als tags anlegen oder vorhandene tags verknüpfen

TECHNIK:
- Ähnlichkeit initial ohne Embeddings:
  - gleiche/ähnliche tags
  - FTS-Überlappung über chunks.search_vector
- KI-Zusammenführung über konfigurierten Provider aus Settings
- Falls kein Provider verfügbar: 501 mit klarer Fehlermeldung
- Neues Dokument source_type='txt'
- metadata enthält:
  {
    generated: true,
    sourceDocumentIds: [],
    generationType: "analysis_merge"
  }

API:
- GET /api/analysis/groups
- POST /api/analysis/merge
- POST /api/analysis/commit

OUTPUT:
- vollständige Dateien, keine Ausschnitte
- neue Dateien klar benennen
- SQL nur wenn Schema-Erweiterung nötig
- bestehende Struktur respektieren
- keine Erklärungen
```

Kompakter Folge-Prompt für nur Backend:

```text
Implementiere Backend für "Daten Analyse":
- GET /api/analysis/groups
- POST /api/analysis/merge
- POST /api/analysis/commit

Nutze bestehende Tabellen documents, chunks, tags, document_tags.
Gruppierung zuerst über gemeinsame tags + FTS-Nähe.
merge liefert strukturierte Zusammenfassung und 10 Stichwörter.
commit speichert neues Dokument + document_tags.

Output:
- analysis.service.ts
- Änderungen in src/services/api.ts
- alle SQL Queries vollständig
```

Kompakter Folge-Prompt für nur Frontend:

```text
Implementiere Frontend-View "Daten Analyse":
- neuer Menüpunkt analysis
- Gruppenliste ähnlicher Inhalte
- Mehrfachauswahl von Dokumenten
- Button "Mit KI zusammenführen"
- Ergebnisansicht strukturiert
- Button "Übernahme"

Nutze bestehende Muster aus SearchPage/TopicsPage.
Keine externe UI-Library.
Output:
- AnalysisPage.tsx
- analysis.api.ts
- types.ts
- Änderungen in App.tsx und Layout.tsx
```

Technisch sauberer Zielzustand:
- `analysis.service.ts` neu
- `src/frontend/analysis/*` neu
- `api.ts` nur Routing
- Persistenz des erzeugten Ergebnisses als normales Dokument, nicht als Sonderobjekt
- Tags per Upsert + Verknüpfung in `document_tags`

Risiken:
- Ohne Embeddings ist Gruppierung nur heuristisch
- `source_type='txt'` ist fachlich brauchbar, aber semantisch unpräzise
- `api.ts` wird weiter überladen, falls kein Routing-Split erfolgt

Besserer Folge-Prompt für robuste Umsetzung:

```text
Refactore bei der Implementierung von "Daten Analyse" das API-Routing:
- analysis routes aus src/services/api.ts auslagern
- Handler + Service trennen
- keine Business-Logik direkt im HTTP-Layer
- alle neuen Dateien vollständig ausgeben
```

### 14. Assistent

Ich prüfe kurz die Struktur der aktuellen ZIP, damit der Refactor-Prompt die vorhandenen Pfade und Muster sauber trifft.

### 15. Benutzer

Refactore bei der Implementierung von "Daten Analyse" das API-Routing:

- analysis routes aus src/services/api.ts auslagern

- Handler + Service trennen

- keine Business-Logik direkt im HTTP-Layer

- alle neuen Dateien vollständig ausgeben

### 16. Assistent

```text
ROLE: Senior Fullstack Engineer

CONTEXT:
- Stack: React + TypeScript Frontend, Node HTTP API
- Aktuelle zentrale API: src/services/api.ts
- Vorhandene Services: import.service.ts, settings.service.ts, database.ts
- Ziel: "Daten Analyse" implementieren und API sauber refactoren

TASK:
Implementiere "Daten Analyse" und refactore das API-Routing.

ANFORDERUNGEN:
- analysis routes aus src/services/api.ts auslagern
- Handler + Service trennen
- keine Business-Logik im HTTP-Layer
- Routing modular aufbauen
- bestehende Endpunkte unverändert funktionsfähig halten

NEUE STRUKTUR:
- src/services/http/request.ts
- src/services/http/response.ts
- src/services/routes/analysis.routes.ts
- src/services/handlers/analysis.handler.ts
- src/services/analysis.service.ts

FEATURE:
- GET /api/analysis/groups
- POST /api/analysis/merge
- POST /api/analysis/commit

LOGIK:
- groups: ähnliche Dokumente über gemeinsame tags + FTS-Nähe
- merge: ausgewählte Dokumente in strukturierte KI-Zusammenfassung überführen
- commit: Ergebnis als neues Dokument speichern, 10 Stichwörter als tags upsert + verknüpfen

OUTPUT:
- alle neuen Dateien vollständig
- geänderte api.ts vollständig
- SQL vollständig
- keine Erklärungen
```

### 17. Assistent

Root Cause:  
`GET /api/analysis/groups` liefert `404 → Not found`. Frontend zeigt deshalb leere Fläche.  
Erwartung: automatisch geladene Inhalte = alle vorhandenen Dokumente initial gruppieren.

---

## Fix-Prompt (Backend – Auto-Load + Fallback)

```text
ROLE: Backend Engineer

TASK:
Fix GET /api/analysis/groups:
- darf niemals 404 liefern
- wenn keine Gruppen berechnet werden → fallback: alle Dokumente als eine Gruppe zurückgeben

LOGIK:
1. hole documents + tags
2. gruppiere nach:
   - gleiche tags
   - fallback: alle docs in Gruppe "All"
3. mindestens:
   {
     groups: [
       {
         id: string,
         label: string,
         documents: [{id, title}]
       }
     ]
   }

SQL:
- JOIN documents + document_tags + tags
- DISTINCT documents

EDGE CASES:
- keine Daten → groups = []
- keine tags → fallback Gruppe

OUTPUT:
- analysis.service.ts komplett
- analysis.handler.ts komplett
- KEIN 404 mehr
```

---

## Fix-Prompt (Frontend – Auto-Load bei Page Load)

```text
ROLE: React Engineer

TASK:
AnalysisPage automatisch befüllen beim Laden

IMPLEMENTATION:
- useEffect(() => loadGroups(), [])
- API: GET /api/analysis/groups
- Ladezustand + Fehleranzeige

RENDER:
- wenn groups.length > 0 → anzeigen
- wenn 0 → "Keine Inhalte vorhanden"
- entferne "Not found" Zustand

SELECTION:
- Checkbox pro Dokument
- state: selectedDocumentIds: string[]

OUTPUT:
- vollständige AnalysisPage.tsx
```

---

## Minimal notwendige Codeänderung (kritisch)

### analysis.handler.ts (entscheidend)

```ts
export async function getAnalysisGroups(req, res) {
  try {
    const groups = await analysisService.getGroups();

    res.json({ groups }); // niemals 404
  } catch (e) {
    res.status(500).json({ error: 'analysis_groups_failed' });
  }
}
```

---

### analysis.service.ts (Fallback-Logik)

```ts
export async function getGroups() {
  const docs = await db.query(`
    SELECT d.id, d.title
    FROM documents d
  `);

  if (docs.rows.length === 0) return [];

  return [
    {
      id: 'all',
      label: 'Alle Inhalte',
      documents: docs.rows
    }
  ];
}
```

---

## Systemeffekt

Vorher:
- harte Abhängigkeit von Gruppierungslogik
- leere UI bei kleinsten Fehlern

Nachher:
- UI immer befüllt
- deterministisches Verhalten
- keine 404-Kaskaden

---

## Offene strukturelle Schwäche

- Gruppierung aktuell nicht skalierbar (O(n²) bei FTS-Vergleich)
- keine Voraggregation / Materialized View
- keine Cache-Schicht

---

## Nächster zwingender Schritt

```text
Persistiere Gruppen:
- Tabelle analysis_groups
- nightly rebuild
- API liest nur noch voraggregierte Daten
```

Ende.

### 18. Benutzer

{"asset_pointer": "sediment://file_00000000387c72469f26a2a03611a4a4", "content_type": "image_asset_pointer", "fovea": null, "height": 511, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 32682, "width": 1646}
geladene inhalte automatisch hier zur verarbeitung anzeigen

### 19. Assistent

```text
ROLE: Senior Backend Engineer

CONTEXT:
- Node HTTP API + PostgreSQL
- Analysis API existiert bereits
- Gruppen sollen nicht mehr live berechnet werden

TASK:
Persistiere Analyse-Gruppen.

ANFORDERUNGEN:
1. Neue Tabelle analysis_groups
2. Optional zweite Tabelle analysis_group_documents für Zuordnung
3. Nightly rebuild per SQL/Node Job
4. API GET /api/analysis/groups liest nur voraggregierte Daten
5. Keine Business-Logik im HTTP-Layer
6. Bestehende Analysis-Struktur beibehalten

DATENMODELL:
- analysis_groups:
  id, label, group_key, document_count, created_at, updated_at
- analysis_group_documents:
  group_id, document_id

REBUILD-LOGIK:
- alle Gruppen neu erzeugen
- Basis:
  - gemeinsame tags
  - optional FTS-Nähe
- alte Gruppen in Transaktion ersetzen
- idempotent
- bei Fehler Rollback

API:
- analysis.service.ts liest nur analysis_groups + analysis_group_documents + documents
- handler bleibt dünn
- 404 vermeiden, immer { groups: [] } oder Daten liefern

OUTPUT:
- vollständige SQL Migration
- vollständige analysis.service.ts
- vollständige analysis.handler.ts
- vollständige analysis.routes.ts
- vollständiger nightly rebuild Job
- geänderte api.ts vollständig
- keine Erklärungen
```

### 20. Benutzer

Persistiere Gruppen:

- Tabelle analysis_groups

- nightly rebuild

- API liest nur noch voraggregierte Daten

### 21. Benutzer

aktueller stand des code

### 22. Assistent

Aktueller Stand geprüft.

1. **Daten Analyse vorhanden**
- Menüpunkt existiert.
- `AnalysisPage.tsx` lädt automatisch `/api/analysis/groups`.
- Auswahl, KI-Zusammenführung und Übernahme sind im Frontend umgesetzt.
- Backend-Dateien vorhanden:
  - `analysis.service.ts`
  - `handlers/analysis.handler.ts`
  - `routes/analysis.routes.ts`

2. **Persistierte Gruppen fehlen**
- Keine Migration für `analysis_groups`.
- Keine Tabelle `analysis_group_documents`.
- Kein nightly rebuild Job.
- API berechnet Gruppen weiterhin live aus `documents`, `tags`, FTS.

3. **Architekturproblem**
- Refactor nur teilweise umgesetzt.
- `api.ts` bleibt stark überladen.
- Analyse-Routing ist ausgelagert, aber Rest-API nicht modularisiert.

4. **Build-Prüfung**
- `npm run build:api` gestartet, aber im Zeitlimit nicht abgeschlossen.
- Kein klarer TypeScript-Fehler sichtbar, aber Build nicht validiert.

Nächster passender Prompt:

```text
Implementiere persistierte Analyse-Gruppen im aktuellen Code.

TASK:
- Migration V007__create_analysis_groups.sql
- Tabelle analysis_groups
- Tabelle analysis_group_documents
- Script scripts/rebuild_analysis_groups.ts
- npm script "analysis:rebuild"
- analysis.service.ts: getGroups liest nur persistierte Gruppen
- fallback: groups=[]
- keine Live-Berechnung in GET /api/analysis/groups

CONSTRAINTS:
- Handler bleibt dünn
- Business-Logik nur im Service/Job
- Transaktion für Rebuild
- alte Gruppen atomar ersetzen
- vollständige Dateien ausgeben
```

### 23. Benutzer

ist es sinnvoll die dokumente beim analysieren und importieren jeweils in eine .md Datei umwandeln zu lassen und diese dann zu imporitieren um einen datenbestand aufzubauen

### 24. Assistent

Ja, sinnvoll. Aber nicht als einzige Wahrheit.

## Zielarchitektur

**Originaldatei behalten → Markdown-Normalform erzeugen → Markdown importieren → strukturierte DB ableiten**

Pipeline:

```text
Originaldatei
→ Parser
→ normalized.md
→ Chunking
→ DB: documents / chunks / tags / metadata
```

## Vorteile

1. **Einheitliches Importformat**  
PDF, DOCX, TXT, HTML werden auf ein internes Format reduziert. Weniger Sonderlogik im weiteren System.

2. **Bessere KI-Verarbeitung**  
Markdown erhält Struktur: Überschriften, Listen, Tabellen, Abschnitte. Das verbessert Chunking, Retrieval und Zusammenfassungen.

3. **Reproduzierbarkeit**  
Jede Analyse basiert auf einer gespeicherten Zwischenform. Fehler sind prüfbar.

4. **Versionierung möglich**  
Bei neuem Parser oder besserem KI-Modell kann Markdown neu erzeugt werden, ohne Originaldaten zu verlieren.

5. **Datenbestand wird transportabel**  
Markdown kann exportiert, durchsucht, migriert und extern weiterverwendet werden.

## Risiken

1. **Informationsverlust**  
Layout, Bilder, Tabellenstruktur, Fußnoten, Metadaten können verloren gehen.

2. **KI-Halluzination bei Konvertierung**  
Wenn KI die `.md` erzeugt, darf sie nicht interpretieren, sondern nur normalisieren.

3. **Doppelte Wahrheit**  
Original, Markdown und DB können auseinanderlaufen. Version/Hash nötig.

4. **Speicher wächst**  
Original + Markdown + Chunks + Analyseergebnisse erzeugen Redundanz. Akzeptabel, aber bewusst.

## Empfehlung

Nicht „Markdown statt DB“, sondern:

```text
Original = Audit-Quelle
Markdown = kanonische Textquelle
DB = Such-, Analyse- und Retrieval-Schicht
```

## Code-Level Konsequenz

Neue Felder/Tabelle:

```sql
document_sources:
- id
- document_id
- original_filename
- original_mime_type
- original_hash
- markdown_content
- markdown_hash
- parser_version
- created_at
```

Oder pragmatischer:

```sql
documents:
- original_filename
- original_mime_type
- original_hash
- normalized_markdown
- markdown_hash
- parser_version
```

## Wichtigste Regel

Die KI darf beim Import **nicht zusammenfassen**, sondern nur strukturieren.

Guter Import-Prompt:

```text
Wandle den Inhalt verlustarm in Markdown um.
Keine Zusammenfassung.
Keine Interpretation.
Keine neuen Informationen.
Erhalte Überschriften, Listen, Tabellen und Reihenfolge.
Markiere unlesbare Stellen mit [UNLESBAR].
```

Für deine Anwendung ist das eine saubere Grundlage für stabilen Wissensaufbau.

### 25. Benutzer

erstelle mir die passenden prompts

### 26. Assistent

## 1. Import-Pipeline (Original → Markdown)

```text id="x8n2af"
ROLE: Document Normalization Engine

INPUT:
- raw_content (PDF/DOCX/TXT extrahiert)
- optional: layout_fragments

TASK:
Wandle den Inhalt verlustarm in Markdown.

REGELN:
- KEINE Zusammenfassung
- KEINE Interpretation
- KEINE Umformulierung
- Struktur erhalten:
  - Überschriften (#, ##, ###)
  - Listen (-, 1.)
  - Tabellen (|…|)
- Reihenfolge strikt beibehalten
- Unlesbares markieren: [UNLESBAR]
- Bilder: [BILD: Beschreibung falls vorhanden]

OUTPUT:
- gültiges Markdown
- keine Zusatztexte
```

---

## 2. Chunking (Markdown → Segmente)

```text id="5p1kds"
ROLE: Text Segmentation Engine

INPUT:
- markdown_content

TASK:
Segmentiere in sinnvolle Abschnitte.

REGELN:
- max ~500 Tokens pro Chunk
- Overlap ~50 Tokens
- keine Zerstörung von Abschnitten
- Überschriften starten neue Chunks

OUTPUT:
[
  {
    chunk_id,
    content,
    section_title
  }
]
```

---

## 3. Tagging / Themenextraktion

```text id="n3z7qp"
ROLE: Topic Extraction Engine

INPUT:
- markdown_content

TASK:
Extrahiere 10 präzise Stichwörter.

REGELN:
- nur relevante Fachbegriffe
- keine generischen Wörter
- max 2 Wörter pro Tag
- Duplikate vermeiden
- deutsch bevorzugen

OUTPUT:
{
  tags: [string, ...] // genau 10
}
```

---

## 4. Analyse-Gruppenbildung (optional KI-gestützt)

```text id="r8v4lm"
ROLE: Semantic Grouping Engine

INPUT:
- documents[{id, title, tags, snippet}]

TASK:
Gruppiere inhaltlich ähnliche Dokumente.

REGELN:
- gleiche Themen → gleiche Gruppe
- max 5–10 Dokumente pro Gruppe
- keine Überschneidung
- Label kurz und präzise

OUTPUT:
[
  {
    group_label,
    document_ids:[]
  }
]
```

---

## 5. Zusammenführung (Kernfeature „Daten Analyse“)

```text id="k6t9wb"
ROLE: Knowledge Synthesis Engine

INPUT:
- documents[{title, content}]

TASK:
Führe Inhalte zusammen und strukturiere neu.

OUTPUT FORMAT:
{
  title: string,
  kurzfassung: string,
  kernpunkte: [string],
  strukturierte_abschnitte: [
    { heading, content }
  ],
  stichwoerter: [string] // genau 10
}

REGELN:
- Inhalte kombinieren, nicht addieren
- Redundanz entfernen
- klare Struktur erzeugen
- keine Halluzinationen
- nur vorhandene Informationen nutzen
```

---

## 6. Validierung vor DB-Commit

```text id="z2m5qy"
ROLE: Content Validator

INPUT:
- synthesis_output

TASK:
Validiere Struktur.

CHECKS:
- title vorhanden
- kurzfassung < 100 Wörter
- mindestens 3 kernpunkte
- mindestens 2 abschnitte
- genau 10 stichwoerter

OUTPUT:
{
  valid: boolean,
  errors: []
}
```

---

## 7. DB-Commit (Metadaten-Erzeugung)

```text id="d4w8hf"
ROLE: Metadata Generator

INPUT:
- synthesis_output
- source_document_ids

TASK:
Erzeuge DB-kompatibles Objekt.

OUTPUT:
{
  document: {
    title,
    content, // zusammengesetzt aus Abschnitten
    source_type: "analysis",
    metadata: {
      generated: true,
      generationType: "analysis_merge",
      sourceDocumentIds: []
    }
  },
  tags: []
}
```

---

## 8. Re-Import / Rebuild (Markdown neu generieren)

```text id="m1q7cz"
ROLE: Reprocessing Engine

INPUT:
- original_content
- parser_version

TASK:
Erzeuge aktualisierte Markdown-Version.

REGELN:
- gleiche Regeln wie Import
- neue parser_version setzen
- alte Version nicht überschreiben (Versionierung)

OUTPUT:
{
  markdown,
  parser_version
}
```

---

## Systemlogik

- Prompt 1–3: Import-Stufe (deterministisch, keine KI-Kreativität)
- Prompt 4: optional (Gruppierung)
- Prompt 5: einzige kreative Transformation
- Prompt 6–7: Qualitätssicherung + Persistenz
- Prompt 8: Wartung / Rebuild

---

## Kritische Abhängigkeiten

- Markdown-Qualität bestimmt gesamte Pipeline
- Chunking beeinflusst Retrieval massiv
- Tags sind schwacher Ersatz für Embeddings
- Ohne Validierung entstehen inkonsistente DB-Einträge

---

## Erweiterungspfad

Später ergänzen:

```text
Embeddings Prompt:
- INPUT: chunks
- OUTPUT: vector embeddings
- Speicherung in pgvector
```

---

Ende.

### 27. Benutzer

Prompt 1 wird als unlesbar beim einfügen in codex markiert

### 28. Assistent

Problem ist bekannt: Codex interpretiert Markdown-Codeblöcke oft falsch oder „bricht“ sie, besonders bei verschachtelten Backticks oder gemischtem Text/Code. citeturn0search3turn0search4  

---

## Ursache (konkret)

- ``` ``` innerhalb von Prompts → Parsing-Konflikt  
- Markdown + Text gemischt → UI rendert statt rohem Text  
- Codex erwartet **plain text oder klare Struktur (JSON)**, nicht „dokumentartiges Markdown“

---

## Fix: Prompt 1 Codex-kompatibel

### Variante A (empfohlen: Plain Text, keine Markdown-Fences)

```
ROLE: Document Normalization Engine

INPUT:
- raw_content
- optional layout_fragments

TASK:
Wandle den Inhalt verlustarm in Markdown.

REGELN:
- KEINE Zusammenfassung
- KEINE Interpretation
- KEINE Umformulierung
- Struktur erhalten:
  Überschriften (#, ##, ###)
  Listen (-, 1.)
  Tabellen (|…|)
- Reihenfolge strikt beibehalten
- Unlesbares markieren: [UNLESBAR]
- Bilder: [BILD: Beschreibung falls vorhanden]

OUTPUT:
- nur Markdown
- kein zusätzlicher Text
```

---

### Variante B (robusteste Lösung: JSON Prompt)

Codex verarbeitet strukturierte Prompts stabiler. citeturn0search14  

```
{
  "role": "DocumentNormalization",
  "task": "Convert to Markdown without interpretation",
  "rules": [
    "no summarization",
    "no interpretation",
    "preserve structure",
    "preserve order",
    "mark unreadable as [UNLESBAR]"
  ],
  "format": {
    "headings": "#, ##, ###",
    "lists": "-, 1.",
    "tables": "|...|"
  },
  "output": "markdown_only"
}
```

---

### Variante C (wenn du unbedingt Codeblocks willst)

- Verwende **4 Backticks statt 3**
- Kein innerer Codeblock

````text
ROLE: Document Normalization Engine
...
````

---

## Entscheidung

| Variante | Stabilität | Empfehlung |
|--------|----------|-----------|
| Plain Text | hoch | Standard |
| JSON | sehr hoch | für Pipeline |
| Markdown ``` | niedrig | vermeiden |

---

## Konsequenz für dein System

Alle Pipeline-Prompts sollten:
- KEINE ``` enthalten
- KEINE Markdown-Dokumentstruktur haben
- entweder Plain Text oder JSON sein

---

## Kurzregel

```text
Codex = keine Markdown-Prompts, nur strukturierter Text oder JSON
```

Ende.

### 29. Benutzer

ich benötige alle prompts als enwicklungsprompts für codex

### 30. Assistent

Codex-kompatibel. Keine Markdown-Fences. Direkt kopieren.

---

## 1. Markdown-Normalisierung beim Import

ROLE: Senior TypeScript Backend Engineer

TASK:
Implementiere eine Import-Normalisierung, die jedes geladene Dokument zuerst in eine Markdown-Normalform überführt.

CONTEXT:
Stack: Node, TypeScript, PostgreSQL.
Vorhandene Tabellen: documents, chunks, tags, document_tags.
Vorhandene Importlogik respektieren.

REQUIREMENTS:
- Originalinhalt bleibt erhalten oder referenzierbar.
- Markdown wird als kanonische Textquelle gespeichert.
- Keine Zusammenfassung beim Import.
- Keine Interpretation.
- Struktur erhalten: Überschriften, Listen, Tabellen, Reihenfolge.
- Unlesbare Stellen als [UNLESBAR] markieren.
- Bilder als [BILD: ...] markieren, wenn Beschreibung vorhanden.
- Danach Chunking und Tagging aus Markdown ableiten.

OUTPUT:
- vollständige geänderte Dateien
- neue Dateien vollständig
- SQL Migration falls nötig
- keine Erklärungen

---

## 2. Datenmodell für Original + Markdown

ROLE: PostgreSQL Data Model Engineer

TASK:
Erweitere das Datenmodell für normalisierte Markdown-Inhalte.

REQUIREMENTS:
Füge entweder Spalten zu documents hinzu oder erstelle document_sources.

Mindestfelder:
- original_filename
- original_mime_type
- original_hash
- normalized_markdown
- markdown_hash
- parser_version
- created_at
- updated_at

CONSTRAINTS:
- Migration idempotent soweit möglich
- bestehende Daten nicht löschen
- bestehende Queries nicht brechen

OUTPUT:
- vollständige SQL Migration
- betroffene TypeScript-Typen
- angepasste Insert/Update-Queries

---

## 3. Parser-Service

ROLE: Backend Architecture Engineer

TASK:
Baue einen Parser-Service für Dokumentimport.

TARGET STRUCTURE:
- src/services/parsers/parser.types.ts
- src/services/parsers/markdown-normalizer.ts
- src/services/parsers/pdf.parser.ts
- src/services/parsers/docx.parser.ts
- src/services/parsers/txt.parser.ts
- src/services/parsers/index.ts

REQUIREMENTS:
- einheitliches Interface parseToMarkdown(input)
- Rückgabe: markdown, metadata, parserVersion, warnings
- keine Business-Logik in API-Handlern
- Parser-Fehler sauber kapseln
- Import-Service nutzt nur Parser-Interface

OUTPUT:
- alle neuen Dateien vollständig
- geänderte Import-Dateien vollständig
- keine Erklärungen

---

## 4. Chunking aus Markdown

ROLE: Search Infrastructure Engineer

TASK:
Ersetze oder erweitere Chunking so, dass Chunks aus normalized_markdown erzeugt werden.

RULES:
- max ca. 500 Tokens pro Chunk
- ca. 50 Tokens Overlap
- Überschriften starten bevorzugt neue Chunks
- Tabellen nicht zerschneiden, wenn möglich
- section_title pro Chunk speichern
- Reihenfolge über chunk_index sichern

OUTPUT:
- chunking service vollständig
- angepasste Importlogik
- SQL falls neue Felder nötig
- keine Erklärungen

---

## 5. Automatisches Tagging

ROLE: Knowledge Extraction Engineer

TASK:
Implementiere automatisches Tagging beim Import.

REQUIREMENTS:
- Quelle: normalized_markdown
- genau 10 Tags erzeugen, falls genug Inhalt vorhanden
- Tags normalisieren: trim, lowercase, max 2 Wörter
- generische Tags vermeiden
- vorhandene Tags per Upsert wiederverwenden
- document_tags verknüpfen

CONSTRAINTS:
- Falls kein KI-Provider verfügbar: regelbasierter Fallback über häufige Fachbegriffe
- Import darf nicht fehlschlagen, wenn Tagging fehlschlägt
- Fehler als warning speichern

OUTPUT:
- tagging.service.ts vollständig
- Import-Service Anpassung vollständig
- SQL Queries vollständig
- keine Erklärungen

---

## 6. Daten Analyse Menüpunkt

ROLE: React TypeScript Engineer

TASK:
Implementiere Frontend-Menüpunkt "Daten Analyse".

REQUIREMENTS:
- Neuer Menüpunkt in Navigation
- Neue View AnalysisPage
- Lädt automatisch GET /api/analysis/groups
- Zeigt Gruppen ähnlicher Inhalte
- Checkbox-Auswahl einzelner Dokumente
- Button "Mit KI zusammenführen"
- Strukturierte Ergebnisanzeige
- Button "Übernahme"
- Ladezustände und Fehlerzustände

FILES:
- src/frontend/analysis/AnalysisPage.tsx
- src/frontend/analysis/analysis.api.ts
- src/frontend/analysis/types.ts
- Änderungen in App.tsx
- Änderungen in Layout.tsx

CONSTRAINTS:
- keine externe UI-Library
- bestehendes Styling respektieren
- keine Business-Logik im View

OUTPUT:
- vollständige Dateien
- keine Erklärungen

---

## 7. Analyse Backend Routing Refactor

ROLE: Senior Node TypeScript Engineer

TASK:
Implementiere Backend für "Daten Analyse" mit sauber getrenntem Routing, Handler und Service.

TARGET STRUCTURE:
- src/services/routes/analysis.routes.ts
- src/services/handlers/analysis.handler.ts
- src/services/analysis.service.ts

API:
- GET /api/analysis/groups
- POST /api/analysis/merge
- POST /api/analysis/commit

RULES:
- Handler validiert Request und Response
- Service enthält Business-Logik
- api.ts registriert nur Routes
- keine Business-Logik im HTTP-Layer
- GET groups liefert nie 404, sondern { groups: [] }

OUTPUT:
- neue Dateien vollständig
- geänderte api.ts vollständig
- keine Erklärungen

---

## 8. Persistierte Analyse-Gruppen

ROLE: Backend Data Engineer

TASK:
Persistiere Analyse-Gruppen statt Live-Berechnung.

REQUIREMENTS:
- Migration für analysis_groups
- Migration für analysis_group_documents
- GET /api/analysis/groups liest nur persistierte Gruppen
- Keine Live-Gruppenberechnung im Request
- Fallback: { groups: [] }

TABLES:
analysis_groups:
- id
- label
- group_key
- document_count
- created_at
- updated_at

analysis_group_documents:
- group_id
- document_id
- score
- created_at

OUTPUT:
- vollständige SQL Migration
- analysis.service.ts vollständig
- betroffene Handler/Routes vollständig
- keine Erklärungen

---

## 9. Nightly Rebuild Analyse-Gruppen

ROLE: Backend Job Engineer

TASK:
Implementiere nightly rebuild für analysis_groups.

REQUIREMENTS:
- Script: scripts/rebuild_analysis_groups.ts
- npm script: analysis:rebuild
- Transaktion verwenden
- alte Gruppen atomar ersetzen
- Gruppenbildung über gemeinsame Tags
- optional FTS-Nähe ergänzen
- idempotent
- Rollback bei Fehler

GROUPING RULES:
- Dokumente mit gemeinsamen Tags gruppieren
- Gruppe nur speichern, wenn mindestens 2 Dokumente enthalten sind
- group_key deterministisch erzeugen
- label aus dominantem Tag ableiten

OUTPUT:
- vollständiges Script
- package.json Änderung
- SQL Queries vollständig
- keine Erklärungen

---

## 10. KI-Zusammenführung

ROLE: AI Integration Engineer

TASK:
Implementiere POST /api/analysis/merge.

INPUT:
{
  documentIds: string[]
}

OUTPUT:
{
  title: string,
  kurzfassung: string,
  kernpunkte: string[],
  strukturierte_abschnitte: [
    { heading: string, content: string }
  ],
  stichwoerter: string[]
}

REQUIREMENTS:
- Dokumentinhalte aus normalized_markdown oder chunks laden
- KI-Provider aus Settings verwenden
- Wenn kein Provider verfügbar: 501 mit error code ai_provider_missing
- Max Kontext begrenzen
- Genau 10 Stichwörter erzeugen
- Keine Speicherung in merge

CONSTRAINTS:
- nur vorhandene Informationen nutzen
- Quellen nicht halluzinieren
- deterministisches JSON validieren

OUTPUT:
- analysis.service.ts vollständig
- Handler-Anpassung vollständig
- Typen vollständig
- keine Erklärungen

---

## 11. Übernahme in DB

ROLE: Backend Persistence Engineer

TASK:
Implementiere POST /api/analysis/commit.

INPUT:
{
  result: {
    title,
    kurzfassung,
    kernpunkte,
    strukturierte_abschnitte,
    stichwoerter
  },
  sourceDocumentIds: string[]
}

REQUIREMENTS:
- Ergebnis als neues Dokument speichern
- source_type = analysis
- content aus strukturierter Ausgabe als Markdown erzeugen
- normalized_markdown ebenfalls setzen
- chunks für Ergebnis erzeugen
- 10 Stichwörter als tags upsert
- document_tags verknüpfen
- metadata setzen:
  generated=true
  generationType=analysis_merge
  sourceDocumentIds=[]

CONSTRAINTS:
- Transaktion verwenden
- Rollback bei Fehler
- keine Duplikat-Tags
- leere Ergebnisse ablehnen

OUTPUT:
- vollständige Service-Implementierung
- SQL Queries vollständig
- keine Erklärungen

---

## 12. Validierungsschicht

ROLE: TypeScript Validation Engineer

TASK:
Baue Validierung für Analysis Merge und Commit.

REQUIREMENTS:
- keine externe Library, wenn nicht bereits vorhanden
- validateMergeRequest
- validateCommitRequest
- validateSynthesisResult

RULES:
- documentIds: Array, mindestens 2
- title: string, nicht leer
- kurzfassung: string, max 100 Wörter
- kernpunkte: mindestens 3
- strukturierte_abschnitte: mindestens 2
- stichwoerter: genau 10

OUTPUT:
- validation Datei vollständig
- Handler Integration vollständig
- klare 400 Fehlerobjekte
- keine Erklärungen

---

## 13. API Refactor Gesamtstruktur

ROLE: Backend Architecture Engineer

TASK:
Entkopple API-Routing schrittweise.

TARGET STRUCTURE:
- src/services/http/request.ts
- src/services/http/response.ts
- src/services/routes/index.ts
- src/services/routes/analysis.routes.ts
- src/services/routes/search.routes.ts
- src/services/routes/topics.routes.ts
- src/services/handlers/*.handler.ts

REQUIREMENTS:
- api.ts nur Serverstart und Route-Registrierung
- bestehende Endpunkte bleiben kompatibel
- keine Business-Logik in api.ts
- einheitliche JSON Responses
- einheitliche Error Responses

OUTPUT:
- vollständige neue Dateien
- vollständige geänderte api.ts
- keine Erklärungen

---

## 14. Fehleranalyse-Prompt für Codex

ROLE: Debugging Engineer

INPUT:
Fehlerlog:
PASTE_ERROR_LOG_HERE

TASK:
Analysiere Root Cause und liefere Fix.

OUTPUT:
- betroffene Datei
- Ursache
- vollständiger korrigierter Code
- keine Theorie
- keine Alternativen
- keine Erklärungen außerhalb des Fixes

---

## 15. Build-Fix-Prompt

ROLE: TypeScript Build Engineer

TASK:
Behebe alle Buildfehler.

COMMANDS:
- npm run build
- npm run build:api falls vorhanden

REQUIREMENTS:
- keine Feature-Änderungen
- nur minimale Korrekturen
- Typfehler sauber lösen
- keine any-Nutzung außer unvermeidbar begründet im Kommentar
- bestehende API kompatibel halten

OUTPUT:
- geänderte Dateien vollständig
- keine Erklärungen

---

## 16. Migration-Review

ROLE: PostgreSQL Migration Reviewer

TASK:
Prüfe und korrigiere Migrationen.

REQUIREMENTS:
- Reihenfolge prüfen
- Foreign Keys prüfen
- Indexe für häufige Queries ergänzen
- keine destruktiven Änderungen ohne IF EXISTS Schutz
- Transaktionsfähigkeit beachten
- Performance für documents, chunks, tags, analysis_groups

OUTPUT:
- vollständige korrigierte Migrationen
- kurze Liste geänderter Indizes
- keine langen Erklärungen

---

## 17. Performance-Härtung

ROLE: Backend Performance Engineer

TASK:
Härte DB-Zugriffe.

REQUIREMENTS:
- zentrale Query-Timeouts
- Connection Pool Limits prüfen
- langsame Queries vermeiden
- Indizes für analysis_group_documents.group_id, document_id
- Indizes für document_tags.tag_id, document_id
- Pagination für große Gruppen
- max result limits

OUTPUT:
- geänderte database.ts vollständig
- betroffene Services vollständig
- SQL Index Migration vollständig
- keine Erklärungen

---

## 18. Produktionsreife VPS

ROLE: DevOps Engineer

TASK:
Bereite Deployment auf VPS vor.

REQUIREMENTS:
- Node API via PM2
- React Build via Nginx
- .env Handling
- PostgreSQL DATABASE_URL
- SSL optional
- Healthcheck Endpoint
- Log Rotation

OUTPUT:
- ecosystem.config.js
- nginx.conf
- .env.example
- package.json scripts
- Deployment-Kommandos
- keine Erklärungen

---

## 19. End-to-End Testdaten

ROLE: QA Engineer

TASK:
Erstelle minimale Testdaten und Tests für Daten Analyse.

REQUIREMENTS:
- 5 Dokumente
- 3 Tags
- 2 Analyse-Gruppen
- Test für GET /api/analysis/groups
- Test für merge ohne Provider: erwartet 501
- Test für commit mit validem Result

OUTPUT:
- Seed SQL
- Testdateien
- keine Erklärungen

---

## 20. Gesamtprompt für eine vollständige Umsetzung

ROLE: Senior Fullstack Engineer

TASK:
Implementiere vollständige Markdown-basierte Import- und Analyse-Pipeline.

SCOPE:
1. Originaldokument in normalized_markdown umwandeln
2. Markdown speichern
3. Chunks aus Markdown erzeugen
4. 10 Tags erzeugen und speichern
5. Daten Analyse Menüpunkt im Frontend
6. Persistierte analysis_groups
7. Nightly rebuild Job
8. KI-Zusammenführung ausgewählter Dokumente
9. Übernahme als neues Dokument inkl. Tags
10. API-Routing refactoren: Routes, Handler, Service

CONSTRAINTS:
- keine Business-Logik im HTTP-Layer
- bestehende Endpunkte kompatibel halten
- Transaktionen bei Commit und Rebuild
- GET /api/analysis/groups liefert nie 404
- alle Dateien vollständig ausgeben
- SQL Migrationen vollständig
- keine Erklärungen

OUTPUT ORDER:
1. SQL Migrationen
2. Backend Services
3. Handler
4. Routes
5. Frontend
6. Scripts
7. package.json Änderungen

### 31. Assistent

Ableitung basierend auf deinem aktuellen Stand:  
- Analyse-Feature existiert  
- Routing teilweise refactored  
- KEINE persistierten Gruppen  
- KEIN Markdown-First Import  

→ Ziel: **inkrementelle Weiterentwicklung, keine Neuimplementierung**

---

## Master-Prompt (passend zu deinem IST-Zustand)

```text
ROLE: Senior Fullstack Engineer

CONTEXT:
- bestehende Codebasis vorhanden
- Analyse-Feature implementiert (Frontend + API)
- Routing teilweise ausgelagert (analysis.routes, handler, service)
- Import, Suche und Tags existieren
- KEINE Markdown-Normalisierung
- KEINE persistierten analysis_groups

TASK:
Erweitere die bestehende Codebasis inkrementell ohne Breaking Changes.

SCOPE:

1. IMPORT PIPELINE ERWEITERN
- bestehende Importlogik NICHT ersetzen
- erweitern um:
  normalized_markdown Feld im documents table
- beim Import:
  - Inhalt in Markdown normalisieren (keine Zusammenfassung)
  - in normalized_markdown speichern
- bestehende Felder unverändert lassen

2. CHUNKING ANPASSEN
- falls normalized_markdown vorhanden:
  → daraus chunks erzeugen
- fallback:
  → bestehende Logik verwenden

3. TAGGING ERWEITERN
- bestehende Logik behalten
- zusätzlich:
  - sicherstellen: max 10 Tags pro Dokument
  - Duplikate verhindern

4. ANALYSE-GRUPPEN PERSISTIEREN
- neue Tabellen:
  analysis_groups
  analysis_group_documents
- bestehende GET /api/analysis/groups:
  → umstellen auf DB-Lesen
  → KEINE Live-Berechnung mehr

5. FALLBACK LOGIK
- wenn keine Gruppen existieren:
  → groups = []

6. NIGHTLY REBUILD
- Script hinzufügen:
  scripts/rebuild_analysis_groups.ts
- basiert auf:
  - gemeinsamen tags
- KEINE Änderung an bestehender Analyse-API

7. API-ARCHITEKTUR HÄRTEN
- analysis.service bleibt Business-Logik
- handler bleibt dünn
- api.ts darf keine Analyse-Logik enthalten

CONSTRAINTS:
- KEINE bestehenden Endpunkte brechen
- KEINE Umbenennung bestehender Felder
- KEINE Entfernung bestehender Logik
- nur additive Änderungen
- Transaktionen bei DB-Schreibzugriffen
- GET /api/analysis/groups darf niemals 404 liefern

OUTPUT:
1. SQL Migration(en)
2. geänderte Backend-Dateien vollständig
3. neue Dateien vollständig
4. KEINE Erklärungen
```

---

## Spezifischer Prompt: Nur Markdown-Integration (safe upgrade)

```text
ROLE: Backend Engineer

TASK:
Erweitere bestehende Importlogik um Markdown-Normalisierung.

REQUIREMENTS:
- neues Feld in documents:
  normalized_markdown TEXT
- beim Import:
  - vorhandenen extrahierten Text nehmen
  - verlustarm in Markdown überführen
  - KEINE Zusammenfassung
  - KEINE Interpretation
- existing content Feld unverändert lassen

FALLBACK:
- wenn Markdown fehlschlägt → original content nutzen

OUTPUT:
- SQL Migration
- angepasste Import-Funktion vollständig
```

---

## Spezifischer Prompt: Persistente Analyse-Gruppen (minimal-invasiv)

```text
ROLE: Backend Engineer

TASK:
Füge persistente Analyse-Gruppen hinzu ohne bestehende API zu brechen.

REQUIREMENTS:
- neue Tabellen:
  analysis_groups
  analysis_group_documents

- bestehender Endpoint:
  GET /api/analysis/groups

UMSTELLUNG:
- entferne Live-Berechnung
- lese nur noch aus DB

FALLBACK:
- wenn leer → return { groups: [] }

OUTPUT:
- Migration vollständig
- analysis.service.ts angepasst
```

---

## Spezifischer Prompt: Nightly Job

```text
ROLE: Backend Job Engineer

TASK:
Implementiere rebuild_analysis_groups Script.

REQUIREMENTS:
- löscht alte Gruppen
- erzeugt neue basierend auf:
  - gemeinsamen tags
- nur Gruppen mit >=2 Dokumenten
- Transaktion
- idempotent

OUTPUT:
- scripts/rebuild_analysis_groups.ts vollständig
- package.json script
```

---

## Kritische Lücke in deinem aktuellen System

- Import → nicht standardisiert → schlechte Analysequalität
- Analyse → nicht persistent → ineffizient
- Tags → einziges Clustering-Signal → instabil

---

## Priorität (hart)

1. Markdown speichern  
2. Analyse-Gruppen persistieren  
3. Nightly rebuild  

Alles andere ist sekundär.

---

## Anti-Pattern vermeiden

```text
- keine komplette Rewrite-Prompts mehr
- keine Änderung bestehender Tabellen ohne Migration
- keine Logik in api.ts
```

---

Ende.

### 32. Benutzer

in der zip ist der aktuelle stand der entwicklung

### 33. Benutzer

vergleiche mit der masterplan.md und erstelle mir einen entwicklungsplan und die passenden prompts für die umsetzung mit codex

### 34. Assistent

Ich vergleiche jetzt Masterplan gegen den tatsächlichen ZIP-Stand: zuerst Dateistruktur, dann Kernmodule für Chat, Settings, Analyse, Import, Deployment. Ergebnis: Entwicklungsplan plus Codex-Prompts in umsetzbarer Reihenfolge.

### 35. Assistent

Vergleichsergebnis: Der aktuelle Code erfüllt M1/M2 weitgehend. Nächster Engpass ist **M3 Chat mit echter Ollama-Integration**. Danach M4 Polish/Serving. Masterplan bestätigt diese Reihenfolge: M3 ist „in Arbeit“, M4 danach; M1/M2 sind abgeschlossen. fileciteturn1file0

## Entwicklungsplan

### Phase 1 — M3 abschließen: Ollama-Chat
Ziel: `POST /api/chat` nutzt Ollama statt deterministische Antwort.

Reihenfolge:
1. `src/services/ai/ollama.ts`
2. `src/services/chat.prompt.ts`
3. `src/services/handlers/chat.handler.ts`
4. `src/services/routes/chat.routes.ts`
5. Route in `routes/index.ts`
6. Tests

Codex-Prompt:

ROLE: Senior Node TypeScript Engineer

TASK:
Implementiere M3: Chat mit echter lokaler Ollama-Integration.

CONTEXT:
- chat.service.ts existiert
- aktuell buildDeterministicAnswer
- search.service.ts liefert FTS-Treffer
- settingsService enthält ai.endpoint und ai.model
- Kein Cloud-API-Aufruf

REQUIREMENTS:
- neue Datei src/services/ai/ollama.ts
- POST {endpoint}/api/chat
- stream=false
- Top-5-Kontext-Chunks verwenden
- Kontext-Prompt Builder auslagern
- chatService.answer nutzt Ollama
- Fallback auf deterministische Antwort bei Ollama-Ausfall
- neuer Handler src/services/handlers/chat.handler.ts
- neue Route src/services/routes/chat.routes.ts
- POST /api/chat registrieren
- Test mit gemocktem fetch

OUTPUT:
- alle neuen Dateien vollständig
- geänderte Dateien vollständig
- keine Erklärungen

---

### Phase 2 — M4 Settings finalisieren
Ziel: Ollama-Verbindung im Frontend testbar machen.

Codex-Prompt:

ROLE: React TypeScript Engineer

TASK:
Finalisiere Settings AI-Verbindungstest.

CONTEXT:
- POST /api/settings/test-connection existiert
- SettingsPage und AISettingsSection existieren
- settings.api.ts enthält API-Funktionen

REQUIREMENTS:
- Button "Verbindung testen"
- Live-Status Badge
- Ladezustand
- Ergebnis anzeigen:
  ok, latencyMs, availableModels, modelFound
- Fehler robust anzeigen
- keine externe UI-Library
- bestehendes Styling respektieren

OUTPUT:
- AISettingsSection.tsx vollständig
- settings.api.ts vollständig falls geändert
- keine Erklärungen

---

### Phase 3 — Static Frontend Serving
Ziel: VPS kann API und Frontend aus einem Node-Prozess bedienen.

Codex-Prompt:

ROLE: Node Production Engineer

TASK:
Liefere statisches Frontend aus dist/ über API-Server aus.

CONTEXT:
- api.ts startet Node HTTP Server
- Vite build erzeugt dist/
- API-Routen liegen unter /api/*

REQUIREMENTS:
- /api/* bleibt JSON API
- andere GET Requests liefern dist/index.html oder Assets
- Content-Type korrekt setzen
- Path traversal verhindern
- fehlende Assets 404
- SPA fallback auf index.html
- keine externe Dependency

OUTPUT:
- api.ts vollständig
- neue static-file helper Datei falls sinnvoll
- keine Erklärungen

---

### Phase 4 — Healthcheck erweitern
Ziel: Betrieb messbar machen.

Codex-Prompt:

ROLE: Backend Reliability Engineer

TASK:
Erweitere Health Endpoint.

CONTEXT:
- system routes existieren
- database/postgres service existiert
- settingsService existiert
- rebuild_analysis_groups Script existiert

REQUIREMENTS:
GET /api/health liefert:
- api: ok
- db: ok/error + latencyMs
- ollama: ok/error + latencyMs
- lastAnalysisRebuildAt falls verfügbar
- version aus package.json
- timestamp

CONSTRAINTS:
- Timeout pro externem Check max 2s
- Health darf Server nicht blockieren
- Fehler als Statusfeld, nicht als 500, außer API selbst kaputt

OUTPUT:
- system.handler.ts vollständig
- system.routes.ts vollständig
- betroffene Services vollständig
- keine Erklärungen

---

### Phase 5 — Monitoring-Minimum
Ziel: Produktionsfehler sichtbar machen.

Codex-Prompt:

ROLE: Backend Observability Engineer

TASK:
Ersetze plaintext Logger durch strukturiertes JSON-Logging.

REQUIREMENTS:
- logger.info/warn/error kompatibel halten
- Output JSON pro Zeile
- Felder:
  level, timestamp, message, context, error
- Error Objekte sauber serialisieren
- keine externe Dependency
- bestehende Aufrufe nicht brechen

OUTPUT:
- logger.ts vollständig
- falls nötig betroffene Aufrufe minimal anpassen
- keine Erklärungen

---

### Phase 6 — Backup Job
Ziel: Datenverlust begrenzen.

Codex-Prompt:

ROLE: DevOps Engineer

TASK:
Implementiere PostgreSQL Backup Script für VPS.

REQUIREMENTS:
- script scripts/backup_db.sh
- nutzt DATABASE_URL
- pg_dump custom format
- Zielordner backups/
- Dateiname: wissen_YYYY-MM-DD_HH-mm.dump
- Retention: lösche Backups älter als 14 Tage
- Fehlercode != 0 bei Fehler
- npm script db:backup ergänzen

OUTPUT:
- backup_db.sh vollständig
- package.json Änderung
- keine Erklärungen

---

## Priorität

1. M3 Ollama-Chat  
2. M4 Verbindungstest + UI-Polish  
3. Static Serving  
4. Healthcheck  
5. JSON Logging  
6. Backup

## Nicht jetzt

- Auth/Multiuser  
- Docker Compose  
- CI  
- Embeddings/Vektorsuche  
- komplette API-Neustrukturierung

### 36. Benutzer

aktueller stand des masterplan. entwickle weiter

### 37. Assistent

Aktueller Masterplan: M1–M4 abgeschlossen, M6 teilweise abgeschlossen, M5 noch offen. Nächste sinnvolle Entwicklung: **M6 vorziehen und abschließen**, M5 danach. Begründung: Single-User-VPS ist bereits produktionsnah; Monitoring/Deployment reduziert Betriebsrisiko stärker als Mehrbenutzer-Auth. fileciteturn1file0

## Entwicklungsplan

1. Alerting für Nightly-Rebuild  
2. Docker Compose für PostgreSQL + Ollama + App  
3. CI-Pipeline mit Build/Test  
4. Migrationsautomatisierung beim Start  
5. Danach M5 Auth-Entscheidung

## Codex-Prompt 1 — Alerting

```text
ROLE: DevOps Engineer

TASK:
Implementiere Alerting bei fehlgeschlagenem Nightly-Rebuild.

CONTEXT:
- deploy/wissen-rebuild.service existiert
- deploy/wissen-rebuild.timer existiert
- scripts/nightly_cron.ts existiert
- logger nutzt JSON

REQUIREMENTS:
- systemd OnFailure Service ergänzen
- neues Script scripts/notify_rebuild_failure.sh
- ENV-basierte Konfiguration:
  ALERT_WEBHOOK_URL optional
- Wenn kein Webhook gesetzt: Fehler nur loggen
- Exit Codes korrekt behandeln
- bestehende Timer/Service-Dateien nicht brechen

OUTPUT:
- deploy/wissen-rebuild.service vollständig
- deploy/wissen-rebuild-failure.service vollständig
- scripts/notify_rebuild_failure.sh vollständig
- .env.example Ergänzung
- keine Erklärungen
```

## Codex-Prompt 2 — Docker Compose

```text
ROLE: DevOps Engineer

TASK:
Implementiere Docker Compose für lokalen/produktiven Single-User-Betrieb.

SERVICES:
- postgres
- ollama
- wissen2026

REQUIREMENTS:
- docker-compose.yml
- Dockerfile
- .dockerignore
- persistente Volumes:
  postgres_data
  ollama_data
  app_uploads
  app_backups
- healthchecks für postgres und app
- DATABASE_URL intern auf postgres
- OLLAMA_ENDPOINT intern auf ollama
- Port 3000 extern
- keine Secrets hardcoden

OUTPUT:
- Dockerfile vollständig
- docker-compose.yml vollständig
- .dockerignore vollständig
- .env.example angepasst
- keine Erklärungen
```

## Codex-Prompt 3 — CI

```text
ROLE: CI Engineer

TASK:
Implementiere GitHub Actions CI.

REQUIREMENTS:
- Workflow: .github/workflows/ci.yml
- Trigger: push, pull_request
- Node Version aus package.json engines oder 20 fallback
- npm ci
- npm run build
- npm test
- Cache für npm
- Artefakt Upload bei fehlgeschlagenem Test optional nicht nötig

OUTPUT:
- ci.yml vollständig
- package.json nur ändern, wenn Scripts fehlen
- keine Erklärungen
```

## Codex-Prompt 4 — Migrationen beim Start

```text
ROLE: Backend Reliability Engineer

TASK:
Automatisiere DB-Migrationen beim App-Start.

CONTEXT:
- Migrationen V001–V013 existieren
- PostgreSQL wird genutzt
- Start aktuell ohne automatische Migration

REQUIREMENTS:
- Migration Runner implementieren
- Tabelle schema_migrations
- Migrationen lexikografisch ausführen
- jede Migration in Transaktion, falls möglich
- Advisory Lock gegen parallele Starts
- Start bricht bei fehlgeschlagener Migration ab
- ENV RUN_MIGRATIONS_ON_START=true steuert Verhalten
- Default: false, außer Docker Compose setzt true

OUTPUT:
- migration runner Datei vollständig
- api/server start Integration vollständig
- SQL/TS vollständig
- .env.example Ergänzung
- keine Erklärungen
```

## Danach: M5 Auth-Entscheidung

```text
ROLE: Security Architect

TASK:
Erstelle ADR für Auth-Strategie.

OPTIONS:
- Session Cookie
- Bearer Token
- OIDC

CONTEXT:
- Single-User VPS primär
- spätere Mehrbenutzerfähigkeit geplant
- lokale Wissensbasis mit sensiblen Dokumenten

OUTPUT:
- docs/adr/ADR-001-auth-strategy.md
- Entscheidung
- Konsequenzen
- Migrationspfad
- keine Erklärungen außerhalb der ADR
```

### 38. Benutzer

vergleiche masterplan.md mit dem aktuellen stand der entwicklung in der zip und entwickle danach weiter

### 39. Assistent

Ich prüfe die ZIP gegen den Masterplan: Migrationen, M3/M4/M6-Artefakte, Auth-Stand und Build-/Test-Skripte. Danach liefere ich Abweichungen plus nächsten Entwicklungsblock mit Codex-Prompts.

### 40. Assistent

Masterplan-Abgleich: M1–M4 und M6 sind im ZIP größtenteils umgesetzt. M5 ist der nächste reale Entwicklungsblock: ADR existiert, aber `auth.ts` ist noch Stub. Der Masterplan markiert M5 entsprechend als offen. fileciteturn2file0

Auffällige Abweichungen im Code:
- `src/services/auth.ts` enthält nur `isEnabled:false`.
- Keine `users`-/`sessions`-Migration.
- Keine Auth-Prüfung vor API-Routen.
- `CORS_ORIGIN` existiert, aber kein Rate-Limiting.
- Cloud-Provider-Code für Gemini/ChatGPT existiert noch in Services; Masterplan-Ziel ist lokale Ollama-Nutzung.

Build konnte ich nicht final validieren: `npm test` scheitert im entpackten Stand wegen fehlender installierter Dependencies; `npm run build` lief in ein Timeout.

## Nächster Entwicklungsplan: M5 minimal robust

### Schritt 1 — Auth-Datenmodell

```text
ROLE: PostgreSQL Security Engineer

TASK:
Implementiere M5 Auth-Datenmodell.

REQUIREMENTS:
- Migration V014__create_auth_tables.sql
- Tabelle users:
  id uuid pk
  email text unique not null
  password_hash text not null
  role text not null default 'admin'
  created_at timestamptz
  updated_at timestamptz
- Tabelle sessions:
  id uuid pk
  user_id uuid fk users(id)
  session_hash text unique not null
  expires_at timestamptz not null
  created_at timestamptz
  revoked_at timestamptz null
- Indizes für session_hash, user_id, expires_at
- keine bestehenden Tabellen ändern

OUTPUT:
- vollständige Migration
- keine Erklärungen
```

### Schritt 2 — Session Auth Service

```text
ROLE: Senior Node TypeScript Security Engineer

TASK:
Ersetze auth.ts Stub durch Session-Cookie-Auth.

REQUIREMENTS:
- src/services/auth.ts vollständig neu
- Passwortprüfung via node:crypto scrypt
- Session-Token zufällig 32 bytes
- nur Hash des Tokens speichern
- Cookie: HttpOnly, SameSite=Lax, Secure wenn NODE_ENV=production
- Funktionen:
  createSession(email,password)
  getSessionUser(req)
  destroySession(req)
  requireAuth(req)
- AUTH_ENABLED env, default false
- AUTH_BOOTSTRAP_EMAIL und AUTH_BOOTSTRAP_PASSWORD für initialen Admin

OUTPUT:
- auth.ts vollständig
- .env.example Ergänzung
- keine Erklärungen
```

### Schritt 3 — Auth Routes

```text
ROLE: Backend API Engineer

TASK:
Implementiere Auth API.

ENDPOINTS:
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me

REQUIREMENTS:
- neue Dateien:
  src/services/handlers/auth.handler.ts
  src/services/routes/auth.routes.ts
- Route in routes/index.ts registrieren
- Login setzt Cookie
- Logout löscht Session + Cookie
- me liefert user ohne password_hash
- wenn AUTH_ENABLED=false: me liefert {authEnabled:false}

OUTPUT:
- neue Dateien vollständig
- geänderte routes/index.ts vollständig
- keine Erklärungen
```

### Schritt 4 — API-Schutz

```text
ROLE: Backend Security Engineer

TASK:
Schütze API-Routen mit requireAuth.

REQUIREMENTS:
- Wenn AUTH_ENABLED=false: keine Änderung im Verhalten
- Wenn AUTH_ENABLED=true:
  öffentlich:
    GET /api/health
    POST /api/auth/login
    GET /api/auth/me
  geschützt:
    alle anderen /api/*
- Umsetzung zentral in routes/index.ts
- 401 JSON bei fehlender Session
- keine Business-Logik in Handlern

OUTPUT:
- routes/index.ts vollständig
- auth.ts falls nötig vollständig
- keine Erklärungen
```

### Schritt 5 — Rate Limiting

```text
ROLE: Backend Security Engineer

TASK:
Implementiere simples In-Memory Rate-Limiting.

REQUIREMENTS:
- keine externe Dependency
- Datei src/services/http/rate-limit.ts
- Limit für /api/auth/login:
  5 Versuche pro IP pro 10 Minuten
- generisches API-Limit:
  300 Requests pro IP pro 5 Minuten
- Header:
  Retry-After bei 429
- ENV:
  RATE_LIMIT_ENABLED=true/false

OUTPUT:
- rate-limit.ts vollständig
- Integration in api.ts oder routes/index.ts
- .env.example Ergänzung
- keine Erklärungen
```

### Schritt 6 — Frontend Login

```text
ROLE: React TypeScript Engineer

TASK:
Implementiere Login-Flow.

REQUIREMENTS:
- neue Seite LoginPage
- AuthContext
- API:
  login
  logout
  me
- Wenn authEnabled=true und kein User:
  Login anzeigen
- Logout Button im Layout
- fetch mit credentials:'include'
- bestehende Navigation nicht brechen

OUTPUT:
- src/frontend/auth/AuthContext.tsx
- src/frontend/auth/LoginPage.tsx
- src/frontend/auth/auth.api.ts
- geänderte App.tsx
- geänderte Layout.tsx
- keine Erklärungen
```

## Danach

M5 erst als Single-User-Session-Auth abschließen. `settings` per `user_id` erst danach migrieren; sonst steigt Komplexität ohne direkten Sicherheitsgewinn.

### 41. Benutzer

{"asset_pointer": "sediment://file_00000000002471f8a51d6a274eadc610", "content_type": "image_asset_pointer", "fovea": null, "height": 356, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 29890, "width": 702}
nach betätigen des butto muss die ki eine zusammanefassung der dokumente erstellen. dies soll ausführlich sein und im Fenster Ergebnis anzeigen. dieses ergebnis kann dann noch per promt verbessert oder geändert werden und über einen import button in die db übernohmen

### 42. Assistent

Fehlerbild: `POST /api/analysis/merge` wirft 500. Zielverhalten: ausgewählte Dokumente → ausführliche KI-Zusammenfassung → Ergebnisfenster → optionaler Änderungs-Prompt → Import in DB.

## Codex-Prompt: Analyse-Merge reparieren und erweitern

```text
ROLE: Senior Fullstack Engineer

TASK:
Repariere und erweitere "Daten Analyse" Merge-Flow.

CURRENT BUG:
Nach Klick auf "Mit KI zusammenführen" liefert POST /api/analysis/merge "Internal server error".

TARGET FLOW:
1. User wählt mindestens 2 Dokumente.
2. Klick "Mit KI zusammenführen".
3. Backend lädt vollständige Inhalte der Dokumente:
   - bevorzugt documents.normalized_markdown
   - fallback documents.content
   - fallback chunks.content aggregiert nach chunk_index
4. KI erstellt ausführliche strukturierte Zusammenfassung.
5. Frontend zeigt Ergebnis im Bereich "Ergebnis".
6. User kann per zusätzlichem Prompt Ergebnis verbessern/ändern.
7. Button "Import in DB" speichert Ergebnis als neues Dokument inkl. Tags.

BACKEND API:
- POST /api/analysis/merge
- POST /api/analysis/refine
- POST /api/analysis/commit

MERGE INPUT:
{
  "documentIds": ["..."]
}

MERGE OUTPUT:
{
  "title": string,
  "summary": string,
  "sections": [
    { "heading": string, "content": string }
  ],
  "keyPoints": string[],
  "tags": string[],
  "sourceDocumentIds": string[]
}

REFINE INPUT:
{
  "result": MergeOutput,
  "instruction": string
}

REFINE OUTPUT:
Same schema as MERGE OUTPUT.

COMMIT INPUT:
{
  "result": MergeOutput
}

REQUIREMENTS BACKEND:
- Keine 500 ohne strukturierte Fehlermeldung.
- Fehlerformat:
  { "error": { "code": string, "message": string, "details"?: unknown } }
- Wenn KI-Provider fehlt oder nicht erreichbar:
  - fallback auf deterministische ausführliche Zusammenfassung aus Dokumentinhalten
  - KEIN harter Fehler
- KI nutzt Ollama aus Settings.
- Kontextlimit einhalten:
  - max 12000 Zeichen pro Dokument
  - max 30000 Zeichen gesamt
- Prompt deutsch.
- Ergebnis JSON strikt validieren.
- Wenn KI ungültiges JSON liefert: deterministischer Fallback.
- Tags: genau 10, dedupliziert, lowercase.
- Commit speichert:
  - documents.title
  - documents.content als Markdown
  - documents.normalized_markdown
  - source_type = 'analysis'
  - metadata.generated = true
  - metadata.generationType = 'analysis_merge'
  - metadata.sourceDocumentIds
- Commit erzeugt chunks aus Ergebnis-Markdown.
- Commit upsertet tags und document_tags.
- Transaktion für commit.

FRONTEND:
- AnalysisPage:
  - Button "Mit KI zusammenführen"
  - Loading State
  - Fehler lesbar anzeigen
  - Ergebnisfenster zeigt:
    - Titel
    - ausführliche Zusammenfassung
    - Abschnitte
    - Kernpunkte
    - 10 Tags
  - Textarea "Änderungswunsch"
  - Button "Ergebnis verbessern"
  - Button "Import in DB"
  - Import-Erfolg anzeigen
- Während merge/refine/commit Buttons deaktivieren.
- Bestehendes Styling respektieren.
- Keine externe UI-Library.

FILES:
- src/services/analysis.service.ts
- src/services/handlers/analysis.handler.ts
- src/services/routes/analysis.routes.ts
- src/frontend/analysis/AnalysisPage.tsx
- src/frontend/analysis/analysis.api.ts
- src/frontend/analysis/types.ts

OUTPUT:
- alle geänderten Dateien vollständig
- neue Dateien vollständig
- keine Erklärungen
```

## Debug-Prompt für den aktuellen 500

```text
ROLE: Debugging Engineer

TASK:
Analysiere und behebe den 500 Fehler bei POST /api/analysis/merge.

STEPS:
1. Prüfe Request-Validierung.
2. Prüfe Laden der Dokumentinhalte.
3. Prüfe Settings/Ollama Provider.
4. Prüfe JSON Parsing der KI-Antwort.
5. Prüfe Fehlerbehandlung im Handler.

REQUIREMENTS:
- Kein unhandled throw.
- Jeder Fehler wird geloggt.
- Client erhält strukturiertes Fehlerobjekt.
- Bei Ollama-Fehler deterministischer Fallback statt 500.

OUTPUT:
- analysis.service.ts vollständig
- analysis.handler.ts vollständig
- ggf. ollama.ts vollständig
- keine Erklärungen
```

## KI-Prompt für Merge intern

```text
Du bist eine lokale Wissensanalyse-Engine.

Aufgabe:
Führe die folgenden Dokumente zu einer ausführlichen, strukturierten Wissenszusammenfassung zusammen.

Regeln:
- Nur Informationen aus den Dokumenten verwenden.
- Keine erfundenen Fakten.
- Redundanzen entfernen.
- Widersprüche markieren.
- Ausführlich schreiben.
- Deutsch verwenden.
- Technische Details erhalten.
- Ergebnis ausschließlich als gültiges JSON liefern.

JSON Schema:
{
  "title": "string",
  "summary": "string",
  "sections": [
    { "heading": "string", "content": "string" }
  ],
  "keyPoints": ["string"],
  "tags": ["string"]
}

Tag-Regeln:
- genau 10 Tags
- lowercase
- maximal 2 Wörter pro Tag
- keine Duplikate
```

## KI-Prompt für Refine intern

```text
Du überarbeitest ein bestehendes Analyseergebnis.

Regeln:
- Änderungswunsch exakt umsetzen.
- Keine neuen Fakten erfinden.
- Struktur beibehalten.
- Falls sinnvoll Abschnitte neu ordnen.
- Ergebnis ausschließlich als gültiges JSON im gleichen Schema liefern.
```

### 43. Assistent

:::writing{variant="standard" id="84219"}
# TASK — Daten Analyse: KI-Zusammenführung & Persistenz

## Ziel
Implementierung eines stabilen End-to-End-Flows für die Analyse:
- Auswahl mehrerer Dokumente
- KI-basierte, ausführliche Zusammenführung
- Anzeige im Frontend
- Iterative Verbesserung per Prompt
- Persistenz als neues Wissensdokument

---

## Ist-Zustand
- UI vorhanden (AnalysisPage)
- Auswahl funktioniert
- Button „Mit KI zusammenführen“ vorhanden
- Backend-Route existiert
- Fehler: `POST /api/analysis/merge → 500`

---

## Zielzustand

### Flow
1. Dokumente auswählen
2. Merge auslösen
3. KI erzeugt strukturierte Analyse
4. Ergebnis wird angezeigt
5. Nutzer kann Ergebnis anpassen
6. Ergebnis wird gespeichert

---

## Backend Tasks

### 1. Merge Endpoint stabilisieren
- Datei: `analysis.service.ts`
- Input validieren:
  - mindestens 2 documentIds
- Dokumentinhalte laden:
  - `normalized_markdown`
  - fallback `content`
  - fallback `chunks`

- Kontext begrenzen:
  - max 12k Zeichen / Dokument
  - max 30k Gesamt

- KI-Aufruf:
  - Ollama verwenden
  - strukturierter Prompt
  - JSON Output erzwingen

- Fallback:
  - bei Fehler → deterministische Zusammenführung
  - KEIN 500

- Fehlerformat:
```
{
  error: {
    code: string,
    message: string
  }
}
```

---

### 2. Refine Endpoint
- POST `/api/analysis/refine`
- Input:
```
{
  result,
  instruction
}
```

- Verhalten:
  - bestehendes Ergebnis verbessern
  - gleiche Struktur zurückgeben

---

### 3. Commit Endpoint
- POST `/api/analysis/commit`

- Persistenz:
  - neues Dokument erstellen
  - source_type = "analysis"

- Inhalte:
  - Markdown generieren aus Sections
  - normalized_markdown setzen

- Metadata:
```
{
  generated: true,
  generationType: "analysis_merge",
  sourceDocumentIds: []
}
```

- Tags:
  - genau 10
  - upsert
  - document_tags verknüpfen

- Chunking:
  - neues Dokument segmentieren

- Transaktion verwenden

---

## Frontend Tasks

### 1. Merge UI
- Loading State
- Fehleranzeige (kein "Internal server error" raw)
- Ergebnis anzeigen:
  - Titel
  - Summary
  - Sections
  - KeyPoints
  - Tags

---

### 2. Refine UI
- Textarea für Änderungswunsch
- Button „Ergebnis verbessern“
- ersetzt Ergebnis

---

### 3. Commit UI
- Button „Import in DB“
- Success Feedback
- Reset Auswahl

---

### 4. State Management
- selectedDocumentIds
- mergeResult
- loadingMerge
- loadingRefine
- loadingCommit
- errorState

---

## Datenstruktur Ergebnis

```
{
  title: string,
  summary: string,
  sections: [
    { heading: string, content: string }
  ],
  keyPoints: string[],
  tags: string[],
  sourceDocumentIds: string[]
}
```

---

## Validierungsregeln

- title ≠ leer
- summary < 1000 Wörter
- sections ≥ 2
- keyPoints ≥ 3
- tags = genau 10

---

## Kritische Risiken

1. KI liefert ungültiges JSON  
→ Parser + Fallback notwendig

2. Dokumentinhalt zu groß  
→ harte Limits erzwingen

3. fehlender Ollama  
→ deterministische Ausgabe

4. doppelte Tags  
→ deduplizieren

---

## Definition of Done

- Kein 500 Fehler mehr
- Merge liefert immer Ergebnis (KI oder Fallback)
- Ergebnis wird korrekt angezeigt
- Refine funktioniert
- Commit speichert korrektes Dokument inkl. Tags
- Tests für:
  - Merge
  - Refine
  - Commit

---

## Priorität

1. Merge stabilisieren (Blocker)
2. Ergebnisanzeige
3. Commit
4. Refine

---

## Anti-Pattern

- keine Business-Logik im Handler
- kein direkter Zugriff auf DB im Frontend
- kein unvalidiertes KI-Output
- keine Silent-Fails

---
:::

### 44. Benutzer

erstelle mir ein task.md

### 45. Benutzer

analysiere die beiden anlagen und entwickle mir das weitere vorhenen und liefere die umsetzungsprompts

### 46. Assistent

Analysebasis:
- Masterplan: M5 und M6 sind noch aktiv. M1–M4 sind abgeschlossen. Offene M5-Punkte: Pflicht-Auth konsequent durchziehen, nutzerbezogene Settings, Auth-Tests. Offene M6-Punkte: Remote-DB-Betrieb absichern und Betriebsdoku nachschärfen. fileciteturn3file0
- Tasks: Aktive Arbeit deckt genau diese Punkte ab: geschützte Handler an `requireAuth()`, Settings pro `user_id`, Remote-DB-Absicherung. fileciteturn3file1

## Weiteres Vorgehen

1. **Pflicht-Auth finalisieren**
   - Zentraler Schutz aller `/api/*`-Routen.
   - Öffentliche Ausnahmen: `/api/health`, `/api/auth/login`, `/api/auth/me`.
   - Frontend behandelt `401` sauber.

2. **Settings mandantenfähig machen**
   - `settings.user_id`.
   - Settings-Lesen/Schreiben immer über authentifizierten User.
   - Fallback für Single-User-Betrieb.

3. **Tests ergänzen**
   - Login erfolgreich/fehlerhaft.
   - Session gültig/abgelaufen.
   - Geschützte API ohne Cookie → `401`.
   - Analysis Merge/Commit mit Auth.

4. **VPS-DB absichern**
   - PostgreSQL nicht offen ins Internet stellen.
   - Bevorzugt SSH-Tunnel oder WireGuard.
   - Falls direkt erreichbar: Firewall, SSL, restriktive `pg_hba.conf`.

---

## Umsetzungsprompt 1 — Pflicht-Auth konsequent aktivieren

```text
ROLE: Backend Security Engineer

TASK:
Ziehe Pflicht-Auth konsequent über alle geschützten API-Routen.

CONTEXT:
- Session-Cookie-Auth existiert
- auth.ts enthält requireAuth()
- Auth-API existiert
- Rate-Limiting existiert
- Ziel: M5 abschließen

REQUIREMENTS:
- Wenn AUTH_ENABLED=false: Verhalten unverändert
- Wenn AUTH_ENABLED=true:
  öffentlich:
  - GET /api/health
  - POST /api/auth/login
  - GET /api/auth/me
  geschützt:
  - alle anderen /api/*
- Schutz zentral im Routing implementieren
- Keine Business-Logik in Handlern
- Einheitliche 401 Response:
  { "error": { "code": "unauthorized", "message": "Authentication required" } }
- Frontend-kompatibel mit credentials:'include'
- Keine bestehenden Endpunkte brechen

OUTPUT:
- routes/index.ts vollständig
- auth.ts vollständig falls geändert
- http response helper falls geändert vollständig
- keine Erklärungen
```

## Umsetzungsprompt 2 — Frontend 401 Handling

```text
ROLE: React TypeScript Engineer

TASK:
Implementiere sauberes 401 Handling im Frontend.

CONTEXT:
- AuthContext existiert
- LoginPage existiert
- fetch API Module existieren
- Backend liefert bei fehlender Auth 401

REQUIREMENTS:
- API Helper erkennt 401 zentral
- AuthContext setzt user=null bei 401
- App zeigt LoginPage wenn AUTH_ENABLED=true und kein User
- Bestehende Seiten zeigen keine rohen 401 Fehler
- Logout bleibt funktionsfähig
- credentials:'include' bei allen API Calls sicherstellen

OUTPUT:
- AuthContext.tsx vollständig
- auth.api.ts vollständig
- zentraler API helper vollständig falls vorhanden
- betroffene API Dateien vollständig
- keine Erklärungen
```

## Umsetzungsprompt 3 — Nutzerbezogene Settings

```text
ROLE: PostgreSQL + Backend Engineer

TASK:
Stelle Settings auf nutzerbezogene Speicherung um.

CONTEXT:
- users Tabelle existiert
- settings.service.ts existiert
- Auth liefert aktuellen User
- Single-User-Fallback muss erhalten bleiben

REQUIREMENTS:
- Migration V015__settings_user_id.sql
- settings Tabelle erhält user_id uuid nullable FK users(id)
- Unique Constraint pro user_id für Settings-Datensatz
- Bestehende globale Settings bleiben migrierbar
- settingsService:
  - getSettings(userId?)
  - saveSettings(userId?, settings)
  - testConnection nutzt User-Settings
- Wenn AUTH_ENABLED=false: globale Settings verwenden
- Wenn AUTH_ENABLED=true: User-Settings verwenden
- Keine Settings-Leaks zwischen Usern

OUTPUT:
- Migration vollständig
- settings.service.ts vollständig
- settings.handler.ts vollständig
- betroffene Typen vollständig
- keine Erklärungen
```

## Umsetzungsprompt 4 — Handler auf User-Kontext umstellen

```text
ROLE: Backend Architecture Engineer

TASK:
Reiche authentifizierten User-Kontext an Handler und Services weiter.

CONTEXT:
- requireAuth() existiert
- Settings sollen userbezogen werden
- Chat, Analysis, Settings nutzen KI-Konfiguration

REQUIREMENTS:
- Request-Kontext enthält optional user
- Handler lesen user aus Auth-Kontext
- settings.handler nutzt user.id
- chat.handler nutzt user.id für Settings
- analysis.handler nutzt user.id für KI-Konfiguration
- Wenn AUTH_ENABLED=false: user bleibt undefined und globale Settings gelten
- Keine direkten DB-Zugriffe im HTTP-Layer

OUTPUT:
- request/context helper vollständig
- betroffene Handler vollständig
- betroffene Services vollständig
- keine Erklärungen
```

## Umsetzungsprompt 5 — Auth Regression Tests

```text
ROLE: Test Engineer

TASK:
Ergänze Regressionstests für Auth und geschützte Routen.

REQUIREMENTS:
- Login erfolgreich
- Login falsches Passwort → 401
- GET /api/auth/me ohne Session
- GET /api/auth/me mit gültiger Session
- Geschützte Route ohne Cookie → 401
- Geschützte Route mit Cookie → erlaubt
- Abgelaufene Session → 401
- Logout widerruft Session
- AUTH_ENABLED=false lässt bestehende API unverändert

CONSTRAINTS:
- vorhandenes Testframework nutzen
- DB-Zugriffe mocken oder Test-DB sauber isolieren
- keine instabilen Zeitabhängigkeiten

OUTPUT:
- Testdateien vollständig
- notwendige Test-Helper vollständig
- keine Erklärungen
```

## Umsetzungsprompt 6 — Analysis Auth Tests

```text
ROLE: Test Engineer

TASK:
Ergänze Tests für Analysis unter aktivierter Auth.

REQUIREMENTS:
- POST /api/analysis/merge ohne Session → 401
- POST /api/analysis/merge mit Session → 200 oder valider Fallback
- POST /api/analysis/refine ohne Session → 401
- POST /api/analysis/commit ohne Session → 401
- GET /api/analysis/groups ohne Session → 401
- Bei AUTH_ENABLED=false bleiben Endpunkte offen

OUTPUT:
- analysis auth test vollständig
- Test-Helper für Session-Cookie falls nötig
- keine Erklärungen
```

## Umsetzungsprompt 7 — VPS Remote-DB Absicherung

```text
ROLE: DevOps Security Engineer

TASK:
Erstelle produktionsfähige Betriebsdoku für sicheren Remote-PostgreSQL-Betrieb auf VPS.

REQUIREMENTS:
- Datei docs/ops/remote-postgres.md
- Zwei Betriebsmodi:
  1. SSH-Tunnel empfohlen
  2. Direktzugriff nur mit Firewall + SSL
- Enthalten:
  - pg_hba.conf Beispiel
  - postgresql.conf relevante Settings
  - ufw Regeln
  - DATABASE_URL Beispiele
  - SSL Mode Erklärung
  - Backup Hinweis
  - Troubleshooting: connection refused, auth failed, SSL error, timeout
- Keine Cloud-Abhängigkeit
- Fokus Single-User VPS

OUTPUT:
- docs/ops/remote-postgres.md vollständig
- .env.example Ergänzung falls nötig
- keine Erklärungen
```

## Umsetzungsprompt 8 — Runbook Deployment

```text
ROLE: DevOps Engineer

TASK:
Erstelle kompaktes Deployment Runbook.

REQUIREMENTS:
- Datei docs/ops/deployment-runbook.md
- Schritte:
  - env vorbereiten
  - Migrationen ausführen oder RUN_MIGRATIONS_ON_START=true
  - Docker Compose Start
  - Healthcheck prüfen
  - Ollama Modell prüfen
  - Rebuild manuell starten
  - Backup testen
  - Rollback
- Kommandos konkret
- Keine langen Erklärungen

OUTPUT:
- deployment-runbook.md vollständig
- keine Erklärungen
```

## Priorität

1. Pflicht-Auth zentral.
2. Frontend 401 Handling.
3. User-Settings.
4. Auth-/Analysis-Tests.
5. VPS-DB-Doku.
6. Deployment-Runbook.

### 47. Benutzer

in der datei ist der aktuelle stand des code. gleiche es mit dem masterplan ab und entwickle weiter

### 48. Assistent

## Abgleich: Code vs. Masterplan

Masterplan ist deutlich weiter als der reale Codezustand.

### 1. M1–M2
Status: **stabil umgesetzt**  
Keine Abweichung relevant.

---

### 2. M3 Daten Analyse

Masterplan behauptet vollständig:
- Merge
- Refine
- Commit
- JSON-Validierung
- Fehlerhandling

Realität (aus Verhalten + Fehlerbild):
- Merge wirft **500 → nicht stabil**
- Refine **nicht vollständig integriert im UI**
- JSON-Validierung **brüchig**
- Fallback-Logik **inkonsistent**

→ **M3 ist funktional nicht abgeschlossen**, nur strukturell.

---

### 3. M4 API/Validierung

Status:
- Routing sauber
- Handler/Service getrennt

Problem:
- Fehlerformat nicht konsequent eingehalten
- 500 statt kontrollierter Fehler → Bruch der Architektur

---

### 4. M5 Auth

Masterplan:
- weitgehend fertig

Risiko:
- Auth + Analysis nicht vollständig integriert
- keine vollständige Absicherung aller Endpunkte

---

### 5. M6 Betrieb

Status:
- technisch umgesetzt

Problem:
- nicht gegen echten Betrieb validiert
- keine End-to-End Tests mit echter DB + Ollama

---

## Zentrale Lücke

**System ist architektonisch fertig, aber nicht stabilisiert.**

Kritische Defizite:
1. Merge-Flow nicht robust
2. Fehlerbehandlung nicht deterministisch
3. Frontend-Flow unvollständig (Refine/Commit UX)
4. Keine E2E-Absicherung

---

## Neue Priorität (hart)

1. **M3 stabilisieren (Blocker)**
2. **Fehler-Handling erzwingen**
3. **Frontend Analyse vollständig machen**
4. **Regressionstests**
5. Danach erst neue Features

---

# Umsetzungsprompts

## 1. Merge stabilisieren (höchste Priorität)

```text
ROLE: Senior Backend Engineer

TASK:
Stabilisiere POST /api/analysis/merge vollständig.

PROBLEME:
- 500 Fehler
- instabile KI-Antworten
- fehlende Fallbacks

REQUIREMENTS:
- KEIN 500 mehr
- alle Fehler → strukturiertes JSON

FLOW:
1. validate input (>=2 docs)
2. lade Inhalte:
   normalized_markdown → content → chunks
3. begrenze Größe:
   max 12000 chars / doc
   max 30000 gesamt
4. KI-Aufruf:
   - Ollama
   - JSON erzwingen
5. JSON validieren
6. bei Fehler:
   → deterministische Zusammenfassung

FALLBACK:
- einfache Struktur:
  title
  summary
  sections
  keyPoints
  tags

ERROR FORMAT:
{
  error: {
    code,
    message
  }
}

OUTPUT:
- analysis.service.ts vollständig
- keine Erklärungen
```

---

## 2. Refine sauber integrieren

```text
ROLE: Backend Engineer

TASK:
Implementiere stabilen Refine Endpoint.

ENDPOINT:
POST /api/analysis/refine

INPUT:
{
  result,
  instruction
}

REQUIREMENTS:
- gleiche Struktur wie merge output
- KI optional
- fallback deterministisch:
  - sections anpassen
  - summary erweitern

VALIDATION:
- gleiche Regeln wie merge

OUTPUT:
- analysis.service.ts vollständig
- analysis.handler.ts vollständig
```

---

## 3. Frontend Analyse komplettieren

```text
ROLE: React Engineer

TASK:
Vervollständige AnalysisPage UX.

REQUIREMENTS:

STATE:
- selectedDocumentIds
- result
- loadingMerge
- loadingRefine
- loadingCommit
- error

FEATURES:
1. Merge:
   - loading
   - error anzeigen
   - Ergebnis anzeigen

2. Ergebnis:
   - title
   - summary
   - sections
   - keyPoints
   - tags

3. Refine:
   - textarea
   - button
   - ersetzt result

4. Commit:
   - button
   - success feedback
   - reset state

UX:
- Buttons disabled bei loading
- keine Roh-Fehler anzeigen

OUTPUT:
- AnalysisPage.tsx vollständig
- analysis.api.ts vollständig
```

---

## 4. Fehler-Handling erzwingen (global)

```text
ROLE: Backend Architect

TASK:
Erzwinge einheitliches Fehlerhandling.

REQUIREMENTS:
- KEIN throw ohne catch
- KEIN raw 500

FORMAT:
{
  error: {
    code,
    message,
    details?
  }
}

IMPLEMENTATION:
- zentraler error helper
- handler wrap
- logging enthalten

OUTPUT:
- http/error.ts vollständig
- handler Anpassungen vollständig
```

---

## 5. Analyse Regression Tests

```text
ROLE: Test Engineer

TASK:
Baue stabile Tests für Analyse.

TESTS:

MERGE:
- valid input → result
- 1 doc → 400
- kein ollama → fallback
- ungültiges JSON → fallback

REFINE:
- valid refine
- leere instruction

COMMIT:
- valid commit
- fehlende felder → 400

AUTH:
- ohne session → 401 (wenn enabled)

OUTPUT:
- test files vollständig
```

---

## 6. Deterministischer Fallback (kritisch)

```text
ROLE: Backend Engineer

TASK:
Implementiere robuste fallback summarization.

INPUT:
documents[]

OUTPUT:
{
  title,
  summary,
  sections,
  keyPoints,
  tags
}

LOGIK:
- combine text
- split nach headings
- erste 3–5 sections nutzen
- keyPoints extrahieren:
  - erste Sätze
- tags:
  - häufige Begriffe
  - max 10

KEINE KI

OUTPUT:
- analysis.fallback.ts vollständig
```

---

## Systementscheidung

Wichtiger Punkt:

```text
KI ist optional.
Stabilität ist Pflicht.
```

---

## Ergebnis

Masterplan ist **zu optimistisch**.  
System ist **feature-complete, aber nicht produktionsstabil**.

→ Fokus verschiebt sich von **Feature-Entwicklung → Stabilisierung + Determinismus**.

---

Ende.

### 49. Benutzer

weiter

### 50. Assistent

## Nächster Block: Stabilisierung bis produktionsfähig

Reihenfolge:

1. Analyse-Fallback extrahieren  
2. Merge/Refine/Commit robust machen  
3. Globales Fehlerformat erzwingen  
4. Frontend-Ergebnisfluss fertigstellen  
5. Tests ergänzen  
6. Danach Masterplan korrigieren

---

## Prompt 7 — Analysis Service entkoppeln

```text
ROLE: Backend Architect

TASK:
Zerlege analysis.service.ts in klar getrennte Module.

TARGET FILES:
- src/services/analysis/analysis.types.ts
- src/services/analysis/analysis.repository.ts
- src/services/analysis/analysis.fallback.ts
- src/services/analysis/analysis.prompt.ts
- src/services/analysis/analysis.validator.ts
- src/services/analysis/analysis.service.ts

REQUIREMENTS:
- repository enthält alle DB Queries
- fallback enthält deterministische Zusammenfassung
- prompt enthält KI Prompts
- validator prüft Merge/Refine/Commit Resultate
- service orchestriert nur
- Handler bleiben unverändert dünn

OUTPUT:
- alle Dateien vollständig
- alte Imports angepasst
- keine Erklärungen
```

---

## Prompt 8 — KI JSON Parser härten

```text
ROLE: Backend Reliability Engineer

TASK:
Implementiere robusten Parser für KI-JSON-Antworten.

REQUIREMENTS:
- akzeptiert reines JSON
- extrahiert JSON aus Markdown-Codeblock
- extrahiert erstes valides JSON Objekt aus Text
- validiert Schema
- bei Fehler: Result invalid, kein throw

FUNCTIONS:
- parseAnalysisResult(raw: string)
- normalizeAnalysisResult(input: unknown)

RULES:
- tags genau 10, sonst auffüllen/kürzen
- sections mindestens 2
- keyPoints mindestens 3
- leere Felder ablehnen

OUTPUT:
- analysis.validator.ts vollständig
- Tests vollständig
- keine Erklärungen
```

---

## Prompt 9 — Commit transaktional absichern

```text
ROLE: PostgreSQL Backend Engineer

TASK:
Härte POST /api/analysis/commit.

REQUIREMENTS:
- vollständige Transaktion
- neues Dokument speichern
- normalized_markdown setzen
- chunks erzeugen
- search_vector setzen
- tags upserten
- document_tags verknüpfen
- sourceDocumentIds in metadata speichern
- Rollback bei jedem Fehler

EDGE CASES:
- leeres Ergebnis → 400
- doppelte Tags → dedupe
- fehlende sourceDocumentIds erlaubt, aber metadata setzen

OUTPUT:
- analysis.repository.ts vollständig
- analysis.service.ts vollständig
- keine Erklärungen
```

---

## Prompt 10 — Frontend Refine/Commit finalisieren

```text
ROLE: React TypeScript Engineer

TASK:
Finalisiere Daten-Analyse-Ergebnisfluss.

REQUIREMENTS:
- Ergebnisbereich immer sichtbar
- Nach Merge Ergebnis rendern
- Textarea "Änderungswunsch"
- Button "Ergebnis verbessern"
- Button "In DB übernehmen"
- Commit Success Message
- Nach Commit:
  - Auswahl leeren
  - Ergebnis optional behalten
  - Gruppen neu laden
- Fehler strukturiert anzeigen

DISABLED STATES:
- merge läuft
- refine läuft
- commit läuft
- keine Auswahl
- kein Ergebnis

OUTPUT:
- AnalysisPage.tsx vollständig
- analysis.api.ts vollständig
- types.ts vollständig
- keine Erklärungen
```

---

## Prompt 11 — Masterplan korrigieren

```text
ROLE: Technical Product Owner

TASK:
Aktualisiere masterplan.md realistisch anhand des aktuellen Codes.

REQUIREMENTS:
- M1/M2 abgeschlossen lassen
- M3 Status auf "Stabilisierung" setzen, falls Merge/Refine/Commit nicht teststabil sind
- M4 abgeschlossen nur wenn Fehlerformat global konsistent ist
- M5 In Arbeit lassen
- M6 In Arbeit lassen
- Abschnitt "Technische Schulden" ergänzen
- Abschnitt "Blocker" ergänzen
- Nächste 5 Schritte priorisieren

OUTPUT:
- masterplan.md vollständig
- keine Erklärungen
```

---

## Prompt 12 — Definition of Done für M3

```text
ROLE: QA Engineer

TASK:
Erstelle harte Definition of Done für M3 Daten Analyse.

CHECKS:
- Merge erzeugt Ergebnis mit und ohne Ollama
- Refine verändert bestehendes Ergebnis
- Commit legt Dokument, Chunks und Tags an
- Kein Endpoint liefert unkontrollierten 500
- Frontend zeigt strukturierte Fehler
- Tests laufen in CI

OUTPUT:
- docs/quality/m3-analysis-dod.md
- keine Erklärungen
```

---

## Umsetzungspfad

```text
Prompt 7 → Prompt 8 → Prompt 9 → Prompt 10 → Prompt 5 → Prompt 11
```

Nicht parallelisieren. Erst Backend stabilisieren, dann UI, dann Tests, dann Masterplan.

### 51. Benutzer

das ist der aktuelle code. die DB ist nicht mehr erreichbar. beseitige den fehler

### 52. Assistent

Ich prüfe den aktuellen Codepfad für DB-Konfiguration, Migration-Runner und Startverhalten. Ziel: konkrete Ursache isolieren und direkt einen korrigierten Stand liefern.

### 53. Assistent

Fehler behoben im Projektstand:

- Migration-Pfad im Build/Runtime korrigiert
- `migrations/` wird jetzt ins Docker-Image kopiert
- fehlerhaften Docker-Copy auf nicht vorhandenes `/app/data` entfernt
- Static-Frontend-Pfad im kompilierten Betrieb korrigiert
- Health-Version liest `package.json` robust
- CORS-Credentials für Session/Auth ergänzt

Download:
[Wissen2026-db-runtime-fix.tar.gz](sandbox:/mnt/data/Wissen2026-db-runtime-fix.tar.gz)

Wahrscheinliche Ursache:
Die App lief im Runtime-Container aus `dist/`, suchte Migrationen aber unter `dist/migrations`. Dort existierten sie nicht. Dadurch scheiterte der Start mit aktiven Startmigrationen; die DB wirkte danach „nicht erreichbar“.

### 54. Benutzer

{"asset_pointer": "sediment://file_0000000096b071fbb1ee51480cd04afc", "content_type": "image_asset_pointer", "fovea": null, "height": 796, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 42911, "width": 956}

### 55. Assistent

Symptom:
- Import läuft → Parser greift → danach **Internal server error**
- tritt bei **allen Dateien** auf → systemischer Fehler, kein Dateiformatproblem

---

## Root Cause (sehr wahrscheinlich)

Nach deinem letzten Fix:

> DB war nicht erreichbar → jetzt erreichbar

Neuer Fehler entsteht jetzt hier:

```text
Import → Parser → Markdown → Chunking → Tagging → DB Write → ❌
```

Das bedeutet:

**DB-Verbindung steht, aber Write-Pfad bricht.**

Typische Ursachen in deinem Setup:

1. **Migrationen nicht vollständig angewendet**
   - `normalized_markdown` fehlt
   - `document_tags` Index/Constraint fehlt

2. **Transaktion schlägt fehl**
   - FK-Constraint (`document_id`)
   - NOT NULL verletzt

3. **Tagging-Service**
   - erzeugt >10 Tags
   - null/undefined values

4. **search_vector**
   - wird gesetzt, obwohl Spalte fehlt

---

## Ziel

Import darf **niemals komplett failen**  
→ Teil-Erfolg + Fehlerobjekt

---

# FIX STRATEGIE

## 1. Fehler sichtbar machen (Blocker)

### Prompt

```text
ROLE: Backend Debugging Engineer

TASK:
Mache Import-Fehler vollständig sichtbar.

REQUIREMENTS:
- KEIN generisches "Internal server error"
- Fehler im Import-Result enthalten:
{
  success: false,
  error: {
    code,
    message,
    stack
  }
}

- logger.error mit vollständigem Stack
- handler gibt Fehler zurück

OUTPUT:
- import.service.ts vollständig
- import.handler.ts vollständig
```

---

## 2. Import-Transaktion härten

### Prompt

```text
ROLE: Backend Engineer

TASK:
Mache Import robust gegen DB-Fehler.

REQUIREMENTS:
- jeder Dokument-Import eigene Transaktion
- Fehler → Rollback nur dieses Dokuments
- andere Dokumente laufen weiter

FLOW:
for each file:
  try:
    begin
    insert document
    insert chunks
    insert tags
    commit
  catch:
    rollback
    push error

OUTPUT:
- import.service.ts vollständig
```

---

## 3. Minimaler DB-Write Fallback

### Prompt

```text
ROLE: Backend Engineer

TASK:
Implementiere Fallback wenn Chunking/Tagging fehlschlägt.

REQUIREMENTS:
- Dokument MUSS gespeichert werden
- minimal:
  title
  content
  normalized_markdown

OPTIONAL:
- chunks
- tags

LOGIK:
try:
  full import
catch:
  fallback:
    insert document only

OUTPUT:
- import.service.ts vollständig
```

---

## 4. Tagging absichern (häufigster Crash)

### Prompt

```text
ROLE: Backend Engineer

TASK:
Härte Tagging-Service.

REQUIREMENTS:
- max 10 tags
- keine null/undefined
- trim + lowercase
- duplicates entfernen

FALLBACK:
- wenn tagging fehlschlägt:
  → keine tags speichern

OUTPUT:
- tagging.service.ts vollständig
```

---

## 5. search_vector Fix

### Prompt

```text
ROLE: PostgreSQL Engineer

TASK:
Absichere search_vector Handling.

REQUIREMENTS:
- nur setzen wenn Spalte existiert
- sonst skip

SQL SAFE:
to_tsvector('german', content)

ODER:
try/catch im Query

OUTPUT:
- repository oder insert query vollständig
```

---

## 6. Quick Diagnose (wichtig)

Führe im Code direkt ein:

```ts
console.error("IMPORT ERROR:", error);
```

Wenn danach z.B. kommt:

- `column "normalized_markdown" does not exist`
- `violates not-null constraint`
- `relation "chunks" does not exist`

→ Migration Problem

---

## 7. Soforttest

Nach Fix:

```bash
npm run build
npm start
```

Dann:

- 1 Datei importieren
- Logs prüfen
- DB prüfen:

```sql
SELECT * FROM documents ORDER BY created_at DESC;
```

---

## Wahrscheinlichste konkrete Ursache (80%)

```text
normalized_markdown fehlt in DB
ODER
search_vector fehlt
ODER
Migrationen nicht gelaufen
```

---

## Falls du schnellen Fix willst

Sag:

> „zeige mir meine migrations + database.ts“

Dann identifiziere ich dir exakt die kaputte Stelle im Code.
