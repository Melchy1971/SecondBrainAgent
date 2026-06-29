---
title: "Wissensdatenbank Masterplan erstellen"
type: chatgpt_conversation
source: chatgpt
source_id: "69f1df7b-6970-8396-8311-2ce7f7f254f4"
created: 2026-04-29
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
---


# Wissensdatenbank Masterplan erstellen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69f1df7b-6970-8396-8311-2ce7f7f254f4`
- Nachrichten: 28

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Entwicklung einer neuen Wissensdatenbank. Die Anforderung an die DB bekommst du gleich von mir. Deine aufgabe ist es dann durch gezielte nachfragen einen Masterplan für diese DB zu erstellen. Auf der Basis des MP erstellst du mir dann Prompts mit welchen ich die DB mit Claude Workflow und Codex entwickle und erstelle.

### 2. Assistent

Verstanden.

Liefer mir die Anforderungen. Danach arbeite ich in dieser Reihenfolge:

1. Anforderungen strukturieren
2. Lücken, Risiken, Zielkonflikte identifizieren
3. Gezielt nachfragen
4. Masterplan erstellen
5. Umsetzungslogik ableiten
6. Claude-Workflow-Prompts erstellen
7. Codex-Prompts erstellen
8. Iterations- und Qualitätssicherungsplan definieren

Für die Anforderungen nutze am besten dieses Raster:

```text
Ziel der Wissensdatenbank:
Zielgruppen/Nutzerrollen:
Welche Inhalte/Wissensarten:
Quellen/Input-Kanäle:
Suche/Navigation:
KI-Funktionen:
Berechtigungen:
Workflows:
Integrationen:
Technologie-Vorgaben:
Nicht-Ziele:
Erfolgsmetriken:
Risiken/Probleme heute:
Zeitrahmen:
```

Schick auch Rohnotizen. Unsortiert reicht.

### 3. Benutzer

{"asset_pointer": "sediment://file_000000003d20720ca6dbec2c3ca2ecbe", "content_type": "image_asset_pointer", "fovea": null, "height": 2048, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 1283553, "width": 1486}
als erstes bekommst du eine Projektstruktur und diese sool erweitert werden wie auf der grafik

### 4. Assistent

Aus dem gelieferten Artefakt lassen sich zwei Dinge ableiten:

1. **Ist-Zustand (dein ZIP)** ≠ **Zielstruktur (Grafik)**
2. Die Grafik ist kein simples Folder-Template, sondern impliziert bereits **Architekturprinzipien**:
   - Layer-Trennung (UI / API / Data)
   - Verantwortlichkeiten pro Layer
   - Erweiterbarkeit (services, context, middleware)
   - Skalierbarkeit (modularer Aufbau)

---

## Analyse der Zielstruktur (aus Grafik extrahiert)

### 1. Frontend (React)

**Zielstruktur**
```
frontend/
 ├── public/
 └── src/
     ├── assets/
     ├── components/
     ├── pages/
     ├── hooks/
     ├── context/
     ├── services/
     ├── utils/
     ├── App.jsx
     ├── main.jsx
     └── index.css
```

**Implizite Architekturentscheidung**
- `components` = atomare UI-Bausteine
- `pages` = Routing-Ebene (Container)
- `services` = API-Abstraktion (kein Direktzugriff aus Komponenten)
- `context` = globaler State (kein Redux-Zwang)
- `hooks` = Wiederverwendbare Logik

**Risiko**
- Ohne klare Trennung zwischen `pages` und `components` entsteht schnell Spaghetti
- `services` kann zu einem Dumping-Ground werden

---

### 2. Backend (Node.js / Express)

**Zielstruktur**
```
backend/
 └── src/
     ├── config/
     ├── controllers/
     ├── models/
     ├── routes/
     ├── middleware/
     ├── services/
     ├── utils/
     ├── app.js
     └── server.js
```

**Implizite Architektur**
- klassische **MVC + Service Layer**
- Trennung:
  - `routes` → Routing
  - `controllers` → Request/Response
  - `services` → Businesslogik
  - `models` → Datenstruktur
  - `middleware` → Cross-Cutting Concerns

**Risiko**
- Businesslogik verteilt sich zwischen `controllers` und `services`
- fehlende Domain-Trennung (alles flach)

---

### 3. Datenbank

```
database/
 └── schema.sql
```

**Implizit**
- initial SQL-first Ansatz
- keine Migration-Strategie sichtbar
- kein ORM-Zwang definiert

**Risiko**
- Schema-Drift ohne Migrationstool
- fehlende Versionierung

---

### 4. Root-Ebene

```
.env
.gitignore
package.json
README.md
```

---

## Kritische Lücken zwischen Grafik und realem Aufbau

1. **Keine Domain-Struktur**
   - alles ist technisch organisiert, nicht fachlich
   - spätere Skalierung schwierig

2. **Keine KI-/Wissenslogik berücksichtigt**
   - für Wissensdatenbank kritisch:
     - Embeddings
     - Chunking
     - Retrieval
     - Versionierung von Wissen

3. **Keine Pipeline für Content-Ingestion**
   - Input-Kanäle fehlen komplett

4. **Keine Sucharchitektur**
   - Volltext vs. semantische Suche ungeklärt

5. **Keine Rollen-/Rechtestruktur**

6. **Keine Observability**
   - Logging, Monitoring fehlen

---

## Ziel: Erweiterte Struktur für Wissensdatenbank

Du brauchst nicht nur die Grafik – du brauchst eine **erweiterte Variante**, die deine DB wirklich tragen kann.

### Erweiterte Zielstruktur (Version 1)

```
fullstack-system/
│
├── frontend/
│   └── src/
│       ├── assets/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── context/
│       ├── services/
│       ├── utils/
│       ├── features/            # NEU: fachliche Module
│       └── routes/
│
├── backend/
│   └── src/
│       ├── config/
│       ├── controllers/
│       ├── routes/
│       ├── middleware/
│       ├── services/
│       ├── utils/
│
│       ├── modules/             # NEU: Domain Layer
│       │   ├── knowledge/
│       │   ├── users/
│       │   ├── search/
│       │   └── ingestion/
│
│       ├── models/
│       ├── app.js
│       └── server.js
│
├── database/
│   ├── schema.sql
│   ├── migrations/              # NEU
│   └── seeds/                   # NEU
│
├── ai/
│   ├── embeddings/              # NEU
│   ├── retrieval/
│   ├── prompts/
│   └── pipelines/
│
├── scripts/
│   ├── ingest/
│   ├── migrate/
│   └── sync/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── docs/
    ├── architecture.md
    └── api.md
```

---

## Ableitung: Was du jetzt liefern musst

Die Grafik definiert nur **technische Struktur**, nicht das System.

Für den Masterplan fehlen:

### 1. Wissensmodell
- Was ist eine Wissenseinheit?
- Granularität (Dokument / Abschnitt / Chunk)
- Versionierung

### 2. Nutzung
- Lesen vs. Bearbeiten
- KI-gestützte Interaktion?

### 3. Suche
- Keyword / semantisch / hybrid

### 4. Input
- manuell / Upload / API / Sync

### 5. Governance
- Freigaben
- Qualitätssicherung

---

## Nächster Schritt (zwingend)

Liefer die Anforderungen wie gefordert.

Ohne diese entstehen:
- falsches Datenmodell
- falsche Service-Struktur
- nicht skalierbare KI-Integration

Sobald die Anforderungen da sind:
→ ich zerlege sie in Systemlogik  
→ identifiziere Engpässe  
→ baue den Masterplan  
→ liefere dir präzise Claude- und Codex-Prompts für Umsetzung

### 5. Benutzer

liefere mir die struktur als zip

### 6. Assistent

Struktur erstellt und als ZIP paketiert.

[Download die Struktur](sandbox:/mnt/data/fullstack-system.zip)

### 7. Benutzer

ich möchte eine wissens datenbank erstellen. die daten kommen als einzelne dokumente, ganze ordner oder als email aus einer pst Datei und deren unterstruktur. bei emails werden auch die anlagen inhaltlich erfasst. der import bereich soll daher in mehrere bereiche unterteilt sein. beim import analysiert die ki das dokument oder email oder anlage und übernimmt den inhalt ohne grafiken in eine MD datei pro dokument. es werden tags aus dem inhalt generiert die sinnvoll sind. es können aber auch eigene tags erfasst werden. nach dieser analyse werden die inhalt inkl. tag in die db übernommen.

ich werde zuerst alle einzelnen bereiche beschreiben bevor du den masterplan erstellst und mit den promt weiter machst. Stell mir zur ersten anforderung fragen falls du hast bevor wir mit teil 2 weiter machen

### 8. Assistent

Ja. Für Teil 1 fehlen diese Klärungen:

## 1. Importquellen

Welche Dateitypen müssen initial unterstützt werden?

```text
PDF
DOCX
TXT
MD
HTML
XLSX
CSV
PPTX
EML
MSG
PST
Bilder mit OCR
Sonstige
```

## 2. PST / E-Mail-Struktur

Soll die Ordnerstruktur aus der PST erhalten bleiben?

Beispiel:

```text
PST
 └── Kunde A
     └── Projekt X
         └── Mail
             └── Anlagen
```

Als mögliche DB-Felder:

```text
source_type = email
source_path = Kunde A / Projekt X
email_subject
email_sender
email_recipients
email_date
attachment_count
attachment_names
```

## 3. E-Mail + Anlagen

Wie soll eine E-Mail mit Anlagen behandelt werden?

Variante A:

```text
1 Wissenseintrag für die E-Mail
1 separater Wissenseintrag pro Anlage
Verknüpfung über parent_id
```

Variante B:

```text
1 gemeinsamer Wissenseintrag aus E-Mail + allen Anlagen
```

Für Suche, Nachvollziehbarkeit und Dublettenprüfung ist **Variante A** robuster.

## 4. Markdown-Erzeugung

Soll die MD-Datei dauerhaft gespeichert werden oder nur als Zwischenschritt vor DB-Import?

Empfohlene Struktur:

```text
/imported_md/
 ├── documents/
 ├── emails/
 └── attachments/
```

## 5. Grafiken

„Ohne Grafiken“ heißt konkret:

```text
Bilder komplett ignorieren
Bildbeschriftungen übernehmen
Tabellen aus Bildern ignorieren
OCR optional
```

Hier muss festgelegt werden, ob OCR später relevant ist.

## 6. Tabellen

Sollen Tabellen aus Dokumenten übernommen werden?

Optionen:

```text
als Markdown-Tabelle
als Fließtext-Zusammenfassung
beides
ignorieren
```

## 7. KI-Analyse

Was soll die KI beim Import erzeugen?

```text
Titel
Kurzbeschreibung
Zusammenfassung
Vollständige Markdown-Konvertierung
Tags
Dokumenttyp
Themenbereich
Entitäten: Personen, Firmen, Projekte, Produkte
Vertraulichkeitsstufe
Qualitätsbewertung
```

## 8. Tags

Soll es ein kontrolliertes Tag-System geben?

Variante A:

```text
freie Tags
```

Variante B:

```text
KI schlägt Tags vor
User bestätigt/ändert
```

Variante C:

```text
zentrale Tag-Taxonomie
ähnliche Tags werden zusammengeführt
Beispiel: KI, AI, künstliche Intelligenz → künstliche-intelligenz
```

Empfehlung: **Variante C**, sonst entsteht Tag-Müll.

## 9. Importfreigabe

Soll der Import automatisch in die DB laufen oder erst nach Prüfung?

```text
Import → KI-Analyse → Vorschau → User bestätigt → DB
```

Oder:

```text
Import → KI-Analyse → direkte DB-Übernahme
```

Für Qualität: erste Variante.

## 10. Dubletten

Wie sollen doppelte Dokumente behandelt werden?

```text
Dateiname gleich
Inhalt gleich
E-Mail-ID gleich
Hash gleich
ähnlicher Inhalt
```

Mindestens erforderlich:

```text
content_hash
source_hash
message_id bei E-Mails
```

## 11. Versionierung

Wenn ein Dokument erneut importiert wird:

```text
überschreiben
neue Version anlegen
ignorieren
manuell entscheiden
```

Für Wissensdatenbank: **neue Version mit Version-Historie**.

## 12. Speicherlogik

Soll die DB nur strukturierte Metadaten speichern oder auch den vollständigen Markdown-Inhalt?

Empfohlen:

```text
DB speichert:
- Metadaten
- Tags
- Markdown-Inhalt
- Chunk-Daten für Suche
- Quelle / Pfad / Hash

Dateisystem speichert:
- Originaldatei optional
- erzeugte MD-Datei
```

## 13. Importbereiche im UI

Vorschlag für Importbereiche:

```text
Einzeldokument importieren
Ordner importieren
PST-Datei importieren
E-Mail importieren
Anlagen importieren
Import-Warteschlange
Analyse-Vorschau
Fehlerhafte Importe
Import-Historie
```

## 14. Lokale Verarbeitung vs. Cloud

Dürfen Inhalte an externe KI-APIs gesendet werden?

```text
ja
nein
nur ausgewählte Inhalte
lokales Modell bevorzugt
```

Das ist kritisch wegen PST/E-Mail-Daten und Datenschutz.

## 15. Mindestfrage für Teil 2

Für den nächsten Teil reicht diese Entscheidung:

```text
Soll E-Mail + Anlage als getrennte, verknüpfte Wissenseinträge gespeichert werden?
Soll der Import vor DB-Übernahme manuell bestätigt werden?
Soll die erzeugte Markdown-Datei dauerhaft gespeichert werden?
Dürfen Inhalte an externe KI-APIs gesendet werden?
```

### 9. Benutzer

1. ausser XLS/X alle 2. Struktur ja übernehmen. Felder für mvp laut Vorschlag 3. Variante A 4. MVP als zwischenschritt 5. OCR optional 6. als Markdown-Tabelle 7. Titel
Kurzbeschreibung
Zusammenfassung
Vollständige Markdown-Konvertierung
Tags
Dokumenttyp
Themenbereich
Entitäten: Personen, Firmen, Projekte, Produkte
Vertraulichkeitsstufe

8. Variante C 9. Variante A 10. Dubletten (Dateiname gleich
Inhalt gleich
E-Mail-ID gleich
Hash gleich
ähnlicher Inhalt)

11. manuell entscheiden
12. wie empfohlen
13 wie Vorschlag
14. nur ausgewählte Inhalte
lokales Modell bevorzugt
15. Soll E-Mail + Anlage als verknüpfte Wissenseinträge gespeichert werden? 
Soll der Import vor DB-Übernahme manuell bestätigt werden? ja 
Soll die erzeugte Markdown-Datei dauerhaft gespeichert werden? ja 
Dürfen Inhalte an externe KI-APIs gesendet werden? nur ausgewählte Inhalte
lokales Modell bevorzugt

### 10. Assistent

Teil 1 ist spezifiziert.

## Festgelegte Anforderungen Import

```text
Dateitypen:
- PDF
- DOCX
- TXT
- MD
- HTML
- CSV
- PPTX
- EML
- MSG
- PST
- Bilder mit optionalem OCR
- keine XLS/XLSX im MVP
```

```text
PST / E-Mail:
- PST-Ordnerstruktur wird übernommen
- E-Mail wird eigener Wissenseintrag
- Jede Anlage wird eigener Wissenseintrag
- Verknüpfung über parent_id
```

```text
MVP-Felder E-Mail:
- source_type
- source_path
- email_subject
- email_sender
- email_recipients
- email_date
- attachment_count
- attachment_names
```

```text
Markdown:
- pro Dokument / E-Mail / Anlage eine MD-Datei
- dauerhaft gespeichert
- zusätzlich vollständiger Markdown-Inhalt in DB
```

```text
KI-Analyse:
- Titel
- Kurzbeschreibung
- Zusammenfassung
- vollständige Markdown-Konvertierung
- Tags
- Dokumenttyp
- Themenbereich
- Entitäten: Personen, Firmen, Projekte, Produkte
- Vertraulichkeitsstufe
```

```text
Tags:
- zentrale Tag-Taxonomie
- KI schlägt Tags vor
- ähnliche Tags werden normalisiert
```

```text
Importprozess:
Import → KI-Analyse → Vorschau → User bestätigt → DB
```

```text
Dublettenprüfung:
- Dateiname gleich
- Inhalt gleich
- E-Mail-ID gleich
- Hash gleich
- ähnlicher Inhalt
```

```text
Reimport:
- manuelle Entscheidung
```

```text
KI-Verarbeitung:
- lokales Modell bevorzugt
- externe KI-APIs nur für ausgewählte Inhalte
```

## Architekturentscheidung für Teil 1

Für den Import entsteht ein eigener Systembereich:

```text
backend/src/modules/ingestion/
 ├── import.controller.js
 ├── import.routes.js
 ├── import.service.js
 ├── parsers/
 │   ├── pdf.parser.js
 │   ├── docx.parser.js
 │   ├── txt.parser.js
 │   ├── md.parser.js
 │   ├── html.parser.js
 │   ├── csv.parser.js
 │   ├── pptx.parser.js
 │   ├── eml.parser.js
 │   ├── msg.parser.js
 │   ├── pst.parser.js
 │   └── image.parser.js
 ├── analyzers/
 │   ├── ai-analysis.service.js
 │   ├── tag-normalizer.service.js
 │   ├── entity-extractor.service.js
 │   └── confidentiality-classifier.service.js
 ├── converters/
 │   └── markdown-converter.service.js
 ├── duplicate-check/
 │   ├── hash.service.js
 │   ├── similarity.service.js
 │   └── duplicate.service.js
 ├── review/
 │   ├── import-preview.service.js
 │   └── import-approval.service.js
 └── storage/
     ├── original-storage.service.js
     ├── markdown-storage.service.js
     └── import-log.service.js
```

## Offene Punkte für später

```text
- Welche lokalen KI-Modelle genutzt werden
- Ob externe KI-Freigabe pro Dokument, pro Importjob oder pro Bereich erfolgt
- Welche Vertraulichkeitsstufen gelten
- Wie ähnlichkeitsbasierte Dubletten bewertet werden
- Ob Originaldateien dauerhaft gespeichert werden
```

Teil 2 kann folgen.

### 11. Benutzer

{"asset_pointer": "sediment://file_000000005b40722f8eb03df2896de7c9", "content_type": "image_asset_pointer", "fovea": null, "height": 544, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 21920, "width": 688}
Bereich einstellungen: 1. Hell und dunkel Modus 2. KI

### 12. Assistent

Teil 2 erweitert das System um **Einstellungen (UI + Backend + Persistenz + KI-Steuerung)**.

---

## 1. Systemlogik: Einstellungen

Zwei Domänen:

```text
1. UI-Einstellungen
2. KI-Konfiguration
```

Trennung notwendig, da:
- unterschiedliche Lebenszyklen
- unterschiedliche Sicherheitsanforderungen
- unterschiedliche Nutzung (Frontend vs. Backend)

---

## 2. Datenmodell (Backend)

### 2.1 User Settings

```text
user_settings
- id
- user_id
- theme                (light | dark | system)
- created_at
- updated_at
```

**Constraint**
```text
1:1 Beziehung zu User
Fallback: system default
```

---

### 2.2 AI Settings

```text
ai_settings
- id
- provider            (ollama | openai | gemini | custom)
- endpoint_url
- model
- temperature
- max_tokens
- context_window
- is_local            (boolean)
- is_active           (boolean)
- created_at
- updated_at
```

---

### 2.3 Provider-Spezifische Konfiguration

```text
ai_provider_config
- id
- provider
- api_key (verschlüsselt)
- organization
- additional_config (json)
```

---

## 3. Backend-Struktur

```text
backend/src/modules/settings/
 ├── settings.controller.js
 ├── settings.routes.js
 ├── settings.service.js
 ├── validators/
 │   ├── theme.validator.js
 │   └── ai-config.validator.js
 └── mappers/
     └── settings.mapper.js
```

---

## 4. API-Endpunkte

### UI Settings

```text
GET    /api/settings/ui
PUT    /api/settings/ui
```

Payload:

```json
{
  "theme": "dark"
}
```

---

### AI Settings

```text
GET    /api/settings/ai
PUT    /api/settings/ai
POST   /api/settings/ai/test
```

Payload:

```json
{
  "provider": "ollama",
  "endpoint_url": "http://localhost:11434",
  "model": "gemma4:31b",
  "temperature": 0.2,
  "max_tokens": 512,
  "context_window": 4096,
  "is_local": true
}
```

---

## 5. Frontend-Struktur

```text
frontend/src/features/settings/
 ├── pages/
 │   └── SettingsPage.jsx
 ├── components/
 │   ├── ThemeToggle.jsx
 │   ├── AIProviderTabs.jsx
 │   ├── AIConfigForm.jsx
 │   └── TestConnectionButton.jsx
 ├── hooks/
 │   ├── useSettings.js
 │   └── useAIConfig.js
 └── services/
     └── settings.api.js
```

---

## 6. UI-Logik

### 6.1 Theme

```text
State:
- light
- dark
- system

Persistenz:
- DB (user_settings)
- localStorage (Fallback für schnelle UI-Reaktion)
```

---

### 6.2 KI-Konfiguration (aus Screenshot abstrahiert)

```text
Tabs:
- Ollama
- ChatGPT
- Gemini
- Custom

Felder:
- API Endpoint
- Model
- Temperature
- Max Tokens
- Context Window

Aktionen:
- Testen
- Aktiv setzen
```

---

## 7. KI-Testlogik

```text
POST /api/settings/ai/test

Flow:
1. Input validieren
2. Provider Adapter auswählen
3. Test-Prompt senden:
   "Return OK"
4. Timeout + Fehlerhandling
5. Status zurückgeben
```

Response:

```json
{
  "status": "success",
  "latency_ms": 320,
  "model": "gemma4:31b"
}
```

---

## 8. Provider-Abstraktion (kritisch)

```text
backend/src/ai/providers/
 ├── ollama.provider.js
 ├── openai.provider.js
 ├── gemini.provider.js
 └── provider.factory.js
```

**Ziel:**
- einheitliche Schnittstelle
- austauschbare Modelle
- kontrollierte externe API-Nutzung

---

## 9. Sicherheitsmodell

```text
- API Keys verschlüsselt speichern
- lokale Modelle bevorzugen
- externe Calls nur wenn:
    ai_settings.is_local = false
    UND explizit erlaubt
```

---

## 10. Risiken

```text
1. Modell-Inkompatibilität (Token/Context)
2. Endpoint nicht erreichbar (lokal)
3. unterschiedliche Promptformate je Provider
4. falsche Tokenlimits → abgeschnittene Inhalte
5. Datenschutzverletzung bei externen APIs
```

---

## 11. Abhängigkeiten zu Teil 1

Diese Einstellungen steuern direkt:

```text
- KI-Analyse beim Import
- Tag-Generierung
- Entitäten-Erkennung
- Markdown-Konvertierung
```

Fehlkonfiguration → komplette Pipeline instabil.

---

## 12. Offene Entscheidung für spätere Teile

```text
- mehrere aktive Modelle parallel?
- fallback-strategie bei KI-Ausfall?
- unterschiedliches Modell je Use Case (Import vs. Suche)?
```

---

Teil 2 abgeschlossen.  
Teil 3 kann folgen.

### 13. Benutzer

bereich Datenanalyse: hier werden neue inhalte angezeigt und mit bereits erfassten inhalten verglichen und ggf. ergänzt. dafür wird ebenfalls ki verwendet um eine logische zusammenfassung zu erstellen und per import button in die db überführt. Inhalte werden in einem fenster daegestellt. qualitätssicherung. es kann inhalt manuell angepasst werden bevor importiert wird. tags werden mit übernommen

### 14. Assistent

Teil 3 spezifiziert den Bereich **Datenanalyse / Import-Review / Qualitätssicherung**.

## Ziel des Bereichs

```text
Neue Inhalte werden vor DB-Übernahme analysiert, mit bestehendem Wissen verglichen, angereichert, manuell geprüft und anschließend kontrolliert importiert.
```

## Prozesslogik

```text
1. Neuer Inhalt wird importiert
2. KI erzeugt Markdown, Tags, Metadaten, Zusammenfassung
3. System sucht ähnliche / verwandte bestehende Inhalte
4. KI vergleicht neuen Inhalt mit vorhandenen Einträgen
5. System erzeugt Vorschlag:
   - neuer Wissenseintrag
   - Ergänzung bestehender Eintrag
   - neue Version
   - Dublette
   - Konflikt
6. Inhalt wird im Analysefenster angezeigt
7. User kann Inhalt, Tags, Titel, Zusammenfassung manuell bearbeiten
8. Import-Button überführt freigegebenen Inhalt in DB
```

## Backend-Modul

```text
backend/src/modules/analysis/
 ├── analysis.controller.js
 ├── analysis.routes.js
 ├── analysis.service.js
 ├── comparison.service.js
 ├── enrichment.service.js
 ├── quality-check.service.js
 ├── merge-suggestion.service.js
 ├── import-decision.service.js
 └── validators/
     └── analysis.validator.js
```

## Frontend-Modul

```text
frontend/src/features/analysis/
 ├── pages/
 │   └── AnalysisPage.jsx
 ├── components/
 │   ├── AnalysisQueue.jsx
 │   ├── AnalysisDetailView.jsx
 │   ├── MarkdownEditor.jsx
 │   ├── TagEditor.jsx
 │   ├── SimilarContentPanel.jsx
 │   ├── QualityScorePanel.jsx
 │   ├── ImportDecisionPanel.jsx
 │   └── ImportButton.jsx
 ├── hooks/
 │   └── useAnalysis.js
 └── services/
     └── analysis.api.js
```

## Datenmodell-Erweiterung

```text
analysis_items
- id
- import_job_id
- source_document_id
- generated_title
- generated_summary
- generated_markdown
- edited_markdown
- generated_tags
- edited_tags
- detected_entities
- confidentiality_level
- quality_score
- duplicate_score
- similarity_score
- decision_status
- decision_type
- created_at
- updated_at
```

```text
analysis_matches
- id
- analysis_item_id
- existing_knowledge_id
- match_type
- similarity_score
- conflict_score
- suggested_action
- explanation
```

## Decision Types

```text
new_entry
extend_existing
create_new_version
duplicate_ignore
manual_review
```

## Qualitätsprüfung

```text
Prüfkriterien:
- Vollständigkeit
- Verständlichkeit
- Dublettenrisiko
- Quellenbezug
- Tag-Qualität
- Konflikt mit bestehendem Wissen
- Vertraulichkeitsstufe
```

## Analysefenster

Pflichtbereiche:

```text
Linke Seite:
- neuer Inhalt als Markdown
- editierbar

Rechte Seite:
- KI-Zusammenfassung
- Tags
- ähnliche Inhalte
- Dublettenhinweise
- Qualitätsbewertung
- empfohlene Importentscheidung
```

## Importentscheidung

```text
Import Button darf nur aktiv sein, wenn:
- Analyse abgeschlossen
- Pflichtfelder vorhanden
- Qualitätsscore >= definierter Schwelle
- Entscheidungstyp gesetzt
- keine blockierenden Konflikte offen
```

## API-Endpunkte

```text
GET    /api/analysis/queue
GET    /api/analysis/:id
PUT    /api/analysis/:id/content
PUT    /api/analysis/:id/tags
POST   /api/analysis/:id/compare
POST   /api/analysis/:id/quality-check
POST   /api/analysis/:id/import
```

## KI-Aufgaben in diesem Bereich

```text
- logische Zusammenfassung erstellen
- neue Inhalte gegen bestehende Inhalte vergleichen
- Ergänzungsvorschläge erzeugen
- Konflikte erkennen
- Dubletten bewerten
- Tags übernehmen und normalisieren
- Qualitätsscore berechnen
```

## Risiken

```text
1. KI überschreibt relevante Details durch zu starke Zusammenfassung
2. ähnliche Inhalte werden fälschlich als Dubletten bewertet
3. Konflikte werden nicht erkannt
4. manuelle Änderungen werden nicht auditierbar gespeichert
5. Importentscheidung ist nicht reproduzierbar
```

## Erforderliche Audit-Felder

```text
reviewed_by
reviewed_at
manual_changes_diff
ai_model_used
ai_prompt_version
import_decision_reason
```

Teil 3 abgeschlossen.

### 15. Benutzer

Bereich Tehmen: hier kann anhand der tags gefiltert werden und inhalte dazu angezeigt. durch markieren können inhalte wieder durch ki zusammengeführt werden und muss änderbar sein. der neue inhalt wird nach freigabe in db übernommen.

### 16. Assistent

Teil 4 spezifiziert den Bereich **Themen / Tag-basierte Wissensverdichtung**.

## Ziel des Bereichs

```text
Inhalte werden über Tags gefiltert, thematisch angezeigt, manuell ausgewählt, durch KI zusammengeführt, bearbeitet, freigegeben und als neuer oder aktualisierter Wissenseintrag in die DB übernommen.
```

## Prozesslogik

```text
1. User öffnet Bereich Themen
2. System zeigt Tag-Taxonomie
3. User filtert nach einem oder mehreren Tags
4. System zeigt passende Wissenseinträge
5. User markiert relevante Inhalte
6. KI erstellt daraus einen konsolidierten Inhalt
7. Ergebnis wird editierbar angezeigt
8. User passt Inhalt manuell an
9. User gibt Ergebnis frei
10. System übernimmt neuen Inhalt in DB
```

## Frontend-Modul

```text
frontend/src/features/topics/
 ├── pages/
 │   └── TopicsPage.jsx
 ├── components/
 │   ├── TagFilterPanel.jsx
 │   ├── TopicContentList.jsx
 │   ├── ContentSelectionPanel.jsx
 │   ├── MergePreviewPanel.jsx
 │   ├── MergedMarkdownEditor.jsx
 │   ├── TopicTagEditor.jsx
 │   ├── TopicApprovalPanel.jsx
 │   └── SaveMergedContentButton.jsx
 ├── hooks/
 │   └── useTopics.js
 └── services/
     └── topics.api.js
```

## Backend-Modul

```text
backend/src/modules/topics/
 ├── topics.controller.js
 ├── topics.routes.js
 ├── topics.service.js
 ├── tag-filter.service.js
 ├── topic-merge.service.js
 ├── topic-approval.service.js
 ├── topic-version.service.js
 └── validators/
     └── topics.validator.js
```

## Datenmodell-Erweiterung

```text
tags
- id
- name
- normalized_name
- description
- parent_tag_id
- created_at
- updated_at
```

```text
knowledge_tags
- knowledge_id
- tag_id
```

```text
topic_merge_jobs
- id
- selected_tag_ids
- selected_knowledge_ids
- generated_title
- generated_summary
- generated_markdown
- edited_markdown
- generated_tags
- edited_tags
- status
- created_by
- approved_by
- approved_at
- created_at
- updated_at
```

```text
topic_merge_sources
- id
- topic_merge_job_id
- knowledge_id
- contribution_type
- relevance_score
```

## Merge-Entscheidung

Beim Speichern muss entschieden werden:

```text
create_new_entry
update_existing_entry
create_new_version
```

Empfohlener Default:

```text
create_new_entry
```

Grund:
- Ursprungswissen bleibt unverändert
- Zusammenführung ist auditierbar
- keine destruktive Veränderung bestehender Einträge

## KI-Aufgaben

```text
- ausgewählte Inhalte vergleichen
- redundante Aussagen entfernen
- Widersprüche markieren
- logische Gesamtstruktur erzeugen
- konsolidierten Markdown-Inhalt erstellen
- Titel und Zusammenfassung erzeugen
- Tags übernehmen und ergänzen
- Quellenbezüge erhalten
```

## UI-Anforderung

```text
Linke Seite:
- Tag-Filter
- Ergebnisliste
- Auswahlcheckboxen

Mitte:
- ausgewählte Quellen
- relevante Auszüge

Rechte Seite:
- KI-generierter zusammengeführter Inhalt
- Markdown-Editor
- Tags
- Freigabe/Speichern
```

## API-Endpunkte

```text
GET    /api/topics/tags
GET    /api/topics/content?tags=...
POST   /api/topics/merge-preview
PUT    /api/topics/merge/:id/content
PUT    /api/topics/merge/:id/tags
POST   /api/topics/merge/:id/approve
POST   /api/topics/merge/:id/save
```

## Qualitätsregeln

```text
Merge darf nur gespeichert werden, wenn:
- mindestens 2 Inhalte ausgewählt wurden
- generierter oder bearbeiteter Markdown-Inhalt vorhanden ist
- Tags vorhanden sind
- Quellenverweise gespeichert werden
- User-Freigabe erfolgt ist
```

## Risiken

```text
1. KI vermischt Quellen ohne Nachvollziehbarkeit
2. Widersprüche werden geglättet statt markiert
3. Zusammengeführter Inhalt ersetzt versehentlich Originalwissen
4. Tags werden unscharf oder doppelt
5. aus Auswahl wird ein zu allgemeiner Artikel ohne Nutzwert
```

## Audit-Pflichtfelder

```text
source_knowledge_ids
selected_tag_ids
ai_model_used
ai_prompt_version
generated_markdown
edited_markdown
manual_changes_diff
approved_by
approved_at
save_decision
```

## Architekturentscheidung

Themenbereich ist kein reiner Filter. Er ist ein **Wissensverdichtungsmodul**.

Das bedeutet:

```text
Tags → Filter
Auswahl → Kontextbildung
KI → Synthese
User → Qualitätssicherung
DB → neuer auditierbarer Wissenseintrag
```

Teil 4 abgeschlossen.

### 17. Benutzer

bereich suchen: hier kann per suche und ki unterstützung nach schlagwörten oder tags gesucht werden. ergebiss wird angezeigt und kann in eine pdf übernommen werden

### 18. Assistent

Teil 5 spezifiziert den Bereich **Suchen / KI-gestützte Recherche / PDF-Export**.

## Ziel

```text
User sucht per Schlagwort, Tag oder KI-Frage nach Wissen.
Ergebnisse werden angezeigt, auswählbar gemacht und als PDF exportiert.
```

## Sucharten

```text
1. Schlagwortsuche
2. Tag-Suche
3. kombinierte Suche: Schlagwort + Tags
4. KI-gestützte semantische Suche
5. Frage-Antwort-Suche über vorhandene Inhalte
```

## Prozesslogik

```text
1. User gibt Suchbegriff, Frage oder Tags ein
2. System durchsucht Wissensdatenbank
3. KI erweitert optional die Suchintention
4. Ergebnisse werden nach Relevanz angezeigt
5. User markiert relevante Treffer
6. System erstellt Vorschau
7. User exportiert Auswahl als PDF
```

## Backend-Modul

```text
backend/src/modules/search/
 ├── search.controller.js
 ├── search.routes.js
 ├── search.service.js
 ├── keyword-search.service.js
 ├── tag-search.service.js
 ├── semantic-search.service.js
 ├── ai-query-expansion.service.js
 ├── result-ranking.service.js
 ├── pdf-export.service.js
 └── validators/
     └── search.validator.js
```

## Frontend-Modul

```text
frontend/src/features/search/
 ├── pages/
 │   └── SearchPage.jsx
 ├── components/
 │   ├── SearchInput.jsx
 │   ├── TagSearchFilter.jsx
 │   ├── SearchModeSelector.jsx
 │   ├── SearchResultList.jsx
 │   ├── SearchResultCard.jsx
 │   ├── ResultPreviewPanel.jsx
 │   ├── SelectedResultsPanel.jsx
 │   ├── PdfExportPreview.jsx
 │   └── ExportPdfButton.jsx
 ├── hooks/
 │   └── useSearch.js
 └── services/
     └── search.api.js
```

## Datenmodell-Erweiterung

```text
search_queries
- id
- query_text
- selected_tag_ids
- search_mode
- ai_expanded_query
- result_count
- created_by
- created_at
```

```text
search_results_log
- id
- search_query_id
- knowledge_id
- rank_position
- relevance_score
- match_reason
```

```text
pdf_exports
- id
- title
- selected_knowledge_ids
- export_markdown
- export_file_path
- created_by
- created_at
```

## Suchindex

Für belastbare Suche erforderlich:

```text
knowledge_chunks
- id
- knowledge_id
- chunk_text
- chunk_index
- embedding_vector
- token_count
- created_at
```

## Suchlogik

```text
Keyword Search:
- Titel
- Kurzbeschreibung
- Zusammenfassung
- Markdown-Inhalt
- Tags
- Entitäten

Tag Search:
- exakte Tag-Zuordnung
- verwandte Tags
- Parent-/Child-Tags

Semantic Search:
- Query wird embedded
- Vergleich gegen knowledge_chunks
- Rückgabe nach similarity_score

Hybrid Search:
- Keyword Score
- Tag Score
- Semantic Score
- final_score
```

## Ranking

```text
final_score =
  keyword_score * 0.35
+ tag_score * 0.25
+ semantic_score * 0.30
+ freshness_score * 0.10
```

## KI-Unterstützung

```text
- Suchfrage interpretieren
- Synonyme ableiten
- passende Tags vorschlagen
- Suchergebnisse gruppieren
- Antwortzusammenfassung aus Treffern erzeugen
- Relevanzbegründung pro Treffer erstellen
```

## PDF-Export

```text
PDF enthält:
- Titel
- Suchbegriff / Filter
- Exportdatum
- ausgewählte Inhalte
- Tags
- Quellenangaben
- Zusammenfassungen
- optional vollständiger Markdown-Inhalt
```

## API-Endpunkte

```text
POST   /api/search
GET    /api/search/tags
GET    /api/search/:id/results
POST   /api/search/ai-expand
POST   /api/search/export-preview
POST   /api/search/export-pdf
GET    /api/search/export/:id/download
```

## Qualitätsregeln

```text
PDF-Export nur möglich, wenn:
- mindestens 1 Ergebnis ausgewählt wurde
- Inhalte noch in DB vorhanden sind
- User Exportberechtigung hat
- Quellenbezüge erzeugt wurden
```

## Risiken

```text
1. KI erweitert Suchanfrage falsch
2. semantische Suche liefert plausible, aber irrelevante Treffer
3. PDF übernimmt veraltete Inhalte
4. Quellenbezug fehlt
5. zu große Exporte erzeugen unlesbare PDFs
```

## Architekturentscheidung

Der Suchbereich ist nicht nur Recherche, sondern ein **Output-Modul**.

```text
Suche → Auswahl → Vorschau → PDF-Erzeugung → Download
```

Teil 5 abgeschlossen.

### 19. Benutzer

Bereich dashboard: modernes dashboard mit allen wichtigen anzeigen

### 20. Assistent

Teil 6 spezifiziert den Bereich **Dashboard / Systemübersicht / Steuerungszentrale**.

## Ziel

```text
Dashboard zeigt den aktuellen Zustand der Wissensdatenbank, Importpipeline, Datenqualität, Suche, Themen und KI-Konfiguration.
```

## Kernbereiche

```text
1. Wissensbestand
2. Importstatus
3. Analyse-Queue
4. Qualitätssicherung
5. Tags / Themen
6. Suche / Nutzung
7. KI-Systemstatus
8. Fehler / Risiken
```

## Dashboard-Kennzahlen

```text
Wissenseinträge gesamt
Neue Einträge diese Woche
Offene Analyse-Items
Wartende Importfreigaben
Fehlgeschlagene Importe
Dublettenverdacht
Durchschnittlicher Qualitätsscore
Anzahl Tags
Top-Tags
Letzte Suchanfragen
PDF-Exporte
Aktiver KI-Provider
KI-Verbindungsstatus
```

## Frontend-Modul

```text
frontend/src/features/dashboard/
 ├── pages/
 │   └── DashboardPage.jsx
 ├── components/
 │   ├── MetricCard.jsx
 │   ├── ImportStatusWidget.jsx
 │   ├── AnalysisQueueWidget.jsx
 │   ├── QualityScoreWidget.jsx
 │   ├── TagOverviewWidget.jsx
 │   ├── RecentKnowledgeWidget.jsx
 │   ├── SearchActivityWidget.jsx
 │   ├── AIStatusWidget.jsx
 │   ├── ErrorLogWidget.jsx
 │   └── DashboardGrid.jsx
 ├── hooks/
 │   └── useDashboard.js
 └── services/
     └── dashboard.api.js
```

## Backend-Modul

```text
backend/src/modules/dashboard/
 ├── dashboard.controller.js
 ├── dashboard.routes.js
 ├── dashboard.service.js
 ├── metrics.service.js
 ├── health.service.js
 └── aggregations/
     ├── import-metrics.aggregation.js
     ├── knowledge-metrics.aggregation.js
     ├── quality-metrics.aggregation.js
     ├── tag-metrics.aggregation.js
     └── search-metrics.aggregation.js
```

## API-Endpunkte

```text
GET /api/dashboard/overview
GET /api/dashboard/imports
GET /api/dashboard/analysis
GET /api/dashboard/quality
GET /api/dashboard/tags
GET /api/dashboard/search
GET /api/dashboard/ai-status
GET /api/dashboard/errors
```

## Dashboard-Layout

```text
Obere Zeile:
- Wissenseinträge gesamt
- Offene Freigaben
- Fehlgeschlagene Importe
- KI-Status

Mittlere Zeile:
- Importpipeline
- Analyse-Queue
- Qualitätsscore
- Top-Tags

Untere Zeile:
- letzte Wissenseinträge
- letzte Suchanfragen
- PDF-Exporte
- Fehlerlog
```

## Widget-Regeln

```text
MetricCard:
- Wert
- Veränderung gegenüber Vorperiode
- Statusfarbe
- Link zum Detailbereich

ImportStatusWidget:
- laufende Jobs
- abgeschlossene Jobs
- fehlgeschlagene Jobs
- Fehlergrund

AnalysisQueueWidget:
- offene Items
- Dublettenverdacht
- Konflikte
- manuelle Reviews

QualityScoreWidget:
- Durchschnitt
- niedrigste Scores
- blockierende Qualitätsprobleme

TagOverviewWidget:
- Top-Tags
- verwaiste Tags
- ähnliche Tags
- Tag-Merge-Vorschläge

AIStatusWidget:
- aktiver Provider
- Modell
- lokal/extern
- letzter Verbindungstest
- Latenz
```

## Datenmodell-Erweiterung

```text
dashboard_snapshots
- id
- snapshot_date
- knowledge_count
- open_analysis_count
- pending_import_count
- failed_import_count
- duplicate_suspect_count
- avg_quality_score
- tag_count
- search_count
- pdf_export_count
- ai_status
- created_at
```

Optional für MVP nicht zwingend. Dashboard kann initial live aggregieren.

## MVP-Entscheidung

```text
MVP:
- Live-Aggregation aus bestehenden Tabellen
- keine dashboard_snapshots erforderlich
```

```text
Später:
- tägliche Snapshots
- Trends
- historische Entwicklung
```

## Qualitätsregeln

```text
Dashboard darf keine Rohdaten verändern.
Dashboard zeigt nur aggregierte Zustände.
Jedes Widget muss in den betroffenen Funktionsbereich verlinken.
Fehler müssen priorisiert werden:
- kritisch
- warnung
- info
```

## Risiken

```text
1. Dashboard wird zur reinen Deko ohne Steuerungsnutzen
2. zu viele Kennzahlen ohne Entscheidungskontext
3. Live-Aggregationen werden bei größerer DB langsam
4. KI-Status zeigt Verbindung ok, obwohl Analysepipeline fehlschlägt
5. Fehlerlogs werden ignoriert, wenn keine Priorisierung erfolgt
```

## Architekturentscheidung

Dashboard ist die **operative Kontrollzentrale**.

```text
Nicht nur anzeigen.
Sondern Engpässe sichtbar machen:
- offene Freigaben
- Qualitätsprobleme
- Dublettenrisiko
- KI-Ausfälle
- Importfehler
```

Teil 6 abgeschlossen.

### 21. Benutzer

App design: modernes design im telekom Branding

### 22. Assistent

Teil 7 spezifiziert **App Design / UI-System im Telekom Branding**.

## Ziel

```text
Konsistentes, skalierbares UI-System im Telekom-Stil:
klar, reduziert, kontraststark, komponentenbasiert.
```

---

## 1. Designprinzipien (Telekom-Stil abstrahiert)

```text
- Fokus auf Inhalt, nicht Dekoration
- starke Kontraste (Magenta vs. Weiß/Schwarz)
- klare Typografie-Hierarchie
- modulare Karten-Layouts
- viel Weißraum
- konsistente Interaktionsmuster
```

---

## 2. Farbmodell

```text
Primary:
- Telekom Magenta: #E20074

Secondary:
- Dark: #1A1A1A
- Light: #FFFFFF

Neutral:
- Gray-100: #F5F5F5
- Gray-300: #D1D1D1
- Gray-600: #6B6B6B
- Gray-900: #111111

Status:
- Success: #2ECC71
- Warning: #F39C12
- Error: #E74C3C
- Info: #3498DB
```

---

## 3. Dark / Light Mode

```text
Light Mode:
- Background: #FFFFFF
- Surface: #F5F5F5
- Text: #111111

Dark Mode:
- Background: #121212
- Surface: #1E1E1E
- Text: #FFFFFF

Magenta bleibt konstant als Akzentfarbe
```

---

## 4. Typografie

```text
Font:
- Inter (Fallback: system-ui)

Skala:
- H1: 32px / bold
- H2: 24px / semibold
- H3: 20px / semibold
- Body: 14–16px
- Caption: 12px

Regeln:
- max 2 Schriftgrößen pro Komponente
- klare visuelle Hierarchie
```

---

## 5. Layout-System

```text
Grid:
- 12 Spalten
- max width: 1440px
- padding: 24px

Spacing-System:
- 4 / 8 / 12 / 16 / 24 / 32 / 48

Container:
- Card-basiert
- Border-Radius: 12px
- Shadow: leicht (kein Material-Overkill)
```

---

## 6. UI-Komponenten (global)

```text
Buttons:
- Primary (magenta)
- Secondary (outline)
- Ghost

Inputs:
- Text
- Search
- Select
- Tag-Selector

Cards:
- Dashboard Cards
- Content Cards
- Result Cards

Navigation:
- Sidebar (fix)
- Topbar

Feedback:
- Toasts
- Alerts
- Status Badges

Editor:
- Markdown Editor (zentral für System)
```

---

## 7. Navigation

```text
Sidebar (links, fix):

- Dashboard
- Import
- Datenanalyse
- Themen
- Suchen
- Einstellungen

Topbar:
- Suchfeld global
- Theme Toggle
- User / Status
```

---

## 8. Seitenstruktur (einheitlich)

```text
Header:
- Titel
- Kontextaktionen

Content:
- Grid / Split View

Footer optional:
- Aktionen / Status
```

---

## 9. Bereichsspezifisches Design

### Dashboard

```text
- Metric Cards (oben)
- Widgets (Grid)
- klare Statusfarben
- keine überladene Visualisierung
```

---

### Import / Analyse

```text
Split Layout:
- links: Inhalt
- rechts: KI / Tags / Qualität

Hervorhebung:
- Änderungen
- Dubletten
- Konflikte
```

---

### Themen

```text
3-Spalten Layout:
- Tags (links)
- Inhalte (mitte)
- Merge Editor (rechts)
```

---

### Suche

```text
- große Suchleiste
- Filterbar (Tags, Modus)
- Ergebnisliste als Cards
- Auswahlmodus aktivierbar
```

---

## 10. Interaktionsprinzipien

```text
- jede Aktion hat sichtbares Feedback
- kein versteckter Zustand
- klare CTA:
    - Import
    - Freigabe
    - Merge
    - Export

- Ladezustände sichtbar
- Fehlerzustände klar markiert
```

---

## 11. Zustandsvisualisierung

```text
Status Badges:
- Pending
- Approved
- Duplicate
- Conflict
- Error

Farblogik:
- Rot = blockierend
- Gelb = prüfen
- Grün = ok
```

---

## 12. Design-System-Struktur

```text
frontend/src/design/
 ├── tokens/
 │   ├── colors.js
 │   ├── spacing.js
 │   ├── typography.js
 │   └── shadows.js
 ├── components/
 │   ├── Button.jsx
 │   ├── Card.jsx
 │   ├── Input.jsx
 │   ├── Badge.jsx
 │   └── Modal.jsx
 ├── layouts/
 │   ├── DashboardLayout.jsx
 │   └── AppLayout.jsx
 └── themes/
     ├── light.js
     └── dark.js
```

---

## 13. Technische Umsetzung

```text
Framework:
- React

Styling:
- Tailwind oder CSS Modules

State:
- Context API

Theme Switching:
- class-based (dark/light)
```

---

## 14. Risiken

```text
1. Branding wird nur Farbe → kein konsistentes System
2. zu viele UI-Varianten → Inkonsistenz
3. Dark Mode unvollständig implementiert
4. Markdown-Editor passt nicht ins Design
5. komplexe Bereiche (Analyse, Merge) werden unübersichtlich
```

---

## Architekturentscheidung

```text
Design ist kein Layer oben drauf.

Es steuert:
- Verständlichkeit der Analyse
- Qualität der Entscheidungen
- Effizienz der Wissenspflege
```

Teil 7 abgeschlossen.

### 23. Benutzer

Bereich user: jeder user kann nur seine inhalte ändern. in der suche werden alle Inhalte zum thema angezeigt. es muss die möglichkeit geben inhalte für unterschiedliche bereiche freizugeben oder zu sperren. im MVP keine abfrage sondern eintieg per button pro bereich

### 24. Assistent

Teil 8 spezifiziert den Bereich **User / Rechte / Freigaben**.

## Ziel

```text
User können eigene Inhalte erstellen und ändern.
Suche zeigt bereichsübergreifend freigegebene Inhalte.
Inhalte können für definierte Bereiche freigegeben oder gesperrt werden.
MVP nutzt Bereichseinstieg per Button, keine Login-Abfrage.
```

## MVP-Usermodell

```text
Kein echtes Login im MVP.
User-Kontext wird über Bereichsbutton gesetzt.

Beispiel:
- Button: Bereich A
- Button: Bereich B
- Button: Bereich C

Nach Klick:
current_area = ausgewählter Bereich
```

## Rechteprinzip

```text
Ändern:
- nur eigene Inhalte

Lesen/Suchen:
- eigene Inhalte
- Inhalte, die für aktuellen Bereich freigegeben sind
- optional: globale Inhalte

Sperren:
- Inhalt ist für bestimmte Bereiche nicht sichtbar oder nicht verwendbar
```

## Datenmodell

```text
users
- id
- display_name
- area_id
- created_at
- updated_at
```

```text
areas
- id
- name
- description
- is_active
- created_at
- updated_at
```

```text
knowledge_items
- id
- owner_user_id
- owner_area_id
- title
- summary
- markdown_content
- confidentiality_level
- visibility_status
- created_at
- updated_at
```

```text
knowledge_area_permissions
- id
- knowledge_id
- area_id
- permission_type
- created_at
- updated_at
```

## Permission Types

```text
read
blocked
```

Für MVP ausreichend.

Später erweiterbar:

```text
read
comment
edit
approve
admin
blocked
```

## Sichtbarkeitslogik

```text
Ein Inhalt ist sichtbar, wenn:

owner_area_id = current_area
ODER knowledge_area_permissions enthält:
  area_id = current_area
  permission_type = read

UND knowledge_area_permissions enthält NICHT:
  area_id = current_area
  permission_type = blocked
```

## Änderungslogik

```text
Ein Inhalt ist änderbar, wenn:

owner_user_id = current_user_id
```

Im MVP ohne Login:

```text
owner_area_id = current_area
```

Das ist unpräziser, aber MVP-tauglich.

## Bereichseinstieg im MVP

```text
Startseite:
- Bereich auswählen

Buttons:
- Bereich 1
- Bereich 2
- Bereich 3
- Admin / Demo optional
```

Nach Auswahl:

```text
localStorage.current_area_id
localStorage.current_area_name
```

Backend bekommt Bereich über Header:

```text
X-Area-Id: <area_id>
```

## Frontend-Modul

```text
frontend/src/features/user/
 ├── pages/
 │   └── AreaSelectionPage.jsx
 ├── components/
 │   ├── AreaButton.jsx
 │   ├── AreaAccessBadge.jsx
 │   ├── PermissionSelector.jsx
 │   └── ContentVisibilityPanel.jsx
 ├── hooks/
 │   ├── useCurrentArea.js
 │   └── usePermissions.js
 └── services/
     └── user.api.js
```

## Backend-Modul

```text
backend/src/modules/users/
 ├── users.controller.js
 ├── users.routes.js
 ├── users.service.js
 ├── areas.service.js
 ├── permissions.service.js
 ├── access-control.service.js
 └── middleware/
     └── area-context.middleware.js
```

## API-Endpunkte

```text
GET    /api/areas
POST   /api/context/area
GET    /api/users/current-context

GET    /api/knowledge/:id/permissions
PUT    /api/knowledge/:id/permissions

GET    /api/knowledge/visible
PATCH  /api/knowledge/:id/visibility
```

## UI-Anforderungen

### Bereichsauswahl

```text
Beim App-Start:
- kein Login
- Bereichsbuttons anzeigen
- nach Auswahl Dashboard öffnen
```

### Inhalt bearbeiten

```text
Bearbeiten-Button nur sichtbar, wenn:
- Inhalt gehört aktuellem Bereich/User
```

### Inhalte freigeben/sperren

```text
Pro Inhalt:
- Freigegeben für Bereiche
- Gesperrt für Bereiche
- Standard: nur eigener Bereich
```

### Suche

```text
Suchergebnisse enthalten:
- eigene Inhalte
- freigegebene Inhalte anderer Bereiche
- keine gesperrten Inhalte
```

## Auswirkungen auf bestehende Bereiche

```text
Import:
- importierte Inhalte bekommen owner_area_id = current_area

Datenanalyse:
- nur eigene Import-Items bearbeitbar
- Vergleich darf freigegebene Inhalte berücksichtigen

Themen:
- Tag-Filter zeigt sichtbare Inhalte
- Merge darf nur sichtbare Inhalte verwenden
- neuer Merge-Inhalt gehört aktuellem Bereich

Suche:
- sucht über alle für Bereich sichtbaren Inhalte

Dashboard:
- zeigt Kennzahlen für aktuellen Bereich
- optional globale Kennzahlen für Admin später
```

## Risiken

```text
1. MVP ohne echtes Login ist nicht sicher
2. Bereich per localStorage/Header manipulierbar
3. Rechteprüfung darf nicht nur im Frontend stattfinden
4. Suche kann gesperrte Inhalte leaken, wenn Filter fehlt
5. KI-Vergleich darf keine Inhalte aus gesperrten Bereichen verwenden
```

## MVP-Sicherheitsgrenze

```text
MVP ist kein produktives Berechtigungssystem.
Es ist eine Bereichssimulation.

Produktiv erforderlich:
- Authentifizierung
- echte User-Identität
- Rollenmodell
- serverseitige Sessions/JWT
- Audit-Log
```

## Architekturentscheidung

```text
Berechtigungen müssen serverseitig im Query-Layer greifen.

Nicht:
Frontend filtert Ergebnisse.

Sondern:
Backend liefert nur Inhalte, die für current_area sichtbar sind.
```

Teil 8 abgeschlossen.

### 25. Benutzer

so inhalt ist für mvp vorhanden. erstelle mir die zu verwendete Projektstruktur inkl. dateien. zusätzlich einen entwicklungsplan als Entwicklung.md und den passenden masterplan.md  prompts erstellen wir noch nicht.

### 26. Assistent

Ich erstelle jetzt ein MVP-Projektgerüst mit fachlichen Modulen, leeren Implementierungsdateien, Konfigurationsdateien und zwei ausgearbeiteten Markdown-Dokumenten: `Masterplan.md` und `Entwicklung.md`.

### 27. Assistent

Die Struktur wird als ZIP erzeugt. Inhaltlich enthalten: Root-Projekt, Frontend, Backend, KI-Provider-Abstraktion, Import-/Analyse-/Suche-/Themenmodule, Storage-Bereiche, Tests sowie `Masterplan.md` und `Entwicklung.md`.

### 28. Assistent

Erstellt.

[Download ZIP: wissensdatenbank-mvp.zip](sandbox:/mnt/data/wissensdatenbank-mvp.zip)
