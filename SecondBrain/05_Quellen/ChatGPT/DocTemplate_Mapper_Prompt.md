---
title: "DocTemplate Mapper Prompt"
type: chatgpt_conversation
source: chatgpt
source_id: "68ea080c-5640-8332-a4dc-0326ca2db1f6"
created: 2025-10-11
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
  - verein
---


# DocTemplate Mapper Prompt

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68ea080c-5640-8332-a4dc-0326ca2db1f6`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Ich benötige einen prompt für loveable.dev zur Erstellung eines Programms das mir Text in eine wordvorlage mit kompletter Struktur übernimmt. Es muss möglich sein verschiedene Vorlagen ein einen dokumentenpool aufzunehmen und dort zu speichern. B im hinzufügen einer Vorlage muss diese auf Struktur oder Markus Dickscheit Vorgaben zb inhahlsverzeichnis und einzelne Kapitel überprüft werden damit importierte Inhalt korrekt zugeordnet werden können. Die zu verarbeitenden Texte können per copy Paste oder Word importiert werden

### 2. Assistent

Alles klar, Markus. Hier ist ein **sofort verwendbarer Prompt für lovable.dev**, der eine komplette App spezifiziert. Danach bekommst du mein kritisches Sparring zu deinen Annahmen (wie von dir gewünscht).

# Prompt für lovable.dev (Copy-Paste)

Baue eine produktionsreife Anwendung namens **DocTemplate Mapper**. Ziel: Beliebige Texte (Copy-Paste oder .docx) in **strukturierte Word-Dokumente** (.docx) übertragbar machen – basierend auf **vorab geprüften Word-Vorlagen** mit definierter Kapitelstruktur.  

## Hauptfunktionen
1. **Dokumentenpool für Vorlagen**
   - Upload von **.docx-Vorlagen** in einen „Vorlagenpool“ mit Metadaten (Name, Version, Ersteller, Gültig-ab, Tags).
   - **Validierung beim Upload** gegen feste und konfigurierbare Regeln („Markus-Dickscheit-Vorgaben“):
     - Muss ein **Inhaltsverzeichnis** enthalten oder automatisch generierbar sein (ToC basiert auf Word-Überschriftenformaten).
     - Muss definierte **Kapitelstruktur** haben: mindestens eine Sequenz von Überschriften (Heading 1–3) gemäß Regelwerk.
     - Verbindliche Kapitel (z. B. „Einleitung“, „Methodik“, „Ergebnisse“, „Fazit“) müssen als **Heading-1** existieren, optional Unterkapitel als Heading-2/3.
     - **Stilprüfung**: Überschriften verwenden echte Word-Heading-Styles (nicht manuell fett).
     - Optional: Platzhalter-Bookmarks (z. B. `{Abstract}`, `{Ziele}`, `{Risiken}`) sind eindeutig und nicht doppelt.
   - Nach Validierung: Speichere Vorlagen inkl. **extrahierter Struktur** (Kapitel-Baum, Styles, Bookmarks) im Pool.
   - **Versionierung**: gleiche Vorlage mit neuer Version, Migrationshinweis, „aktiv/deprecated“-Flag.

2. **Import von Quelltext**
   - Quelle A: **Copy-Paste** in ein Rich-Text-Feld (eingefügte Tabellen/Bilder optional).
   - Quelle B: **Word-Import** (.docx). Extrahiere **Semantik** (Überschriften, Absätze, Listen, Tabellen, Bilder, Fußnoten).
   - Normalisiere Inhalt in ein internes **Zwischenformat** (Abschnittsliste mit Typ: heading(level), paragraph, list, table, image, footnote).

3. **Automatisches Mapping in Vorlage**
   - Erzeuge ein **Mapping** von Quell-Abschnitten zu Ziel-Kapitelknoten der gewählten Vorlage:
     - Heuristiken: Überschriften-Matching (Levenshtein/Ähnlichkeit), Synonym-Liste, konfigurierbare Regeln (Regex), Bookmarks.
     - Regeln priorisieren: Explizite Bookmarks > genauer Überschriftstreffer > fuzzy Match > manuelle Zuordnung.
   - **Manuelle Nachsteuerung**: UI zeigt Vorlage links (Kapitelbaum) und Quellinhalt rechts; per Drag-&-Drop Abschnitte zuweisen/neu ordnen.
   - **Validierungscheck vor Export**: Alle **Pflichtkapitel** müssen befüllt sein oder bewusst als „leer/entfällt“ markiert.

4. **Export nach .docx**
   - Erzeuge ein neues **Word-Dokument** basierend auf der gewählten Vorlage mit:
     - Korrekt gesetzten Word-Überschriften-Styles (Heading 1–3 etc.).
     - Eingefügten Tabellen/Bildern in den gemappten Kapiteln.
     - **Automatischem Inhaltsverzeichnis** (feldbasiert, aktualisierbar in Word).
     - Übernahme/Mapping von **Fußnoten/Endnoten**.
   - Option „Striktes Styling beibehalten“: erzwinge Vorlagen-Styles und säubere fremde Direktformatierungen.

5. **Regelwerk („Markus-Dickscheit-Vorgaben“) verwalten**
   - UI für **Regelsätze**: Pflichtkapitel, verbotene Styles, erlaubte Heading-Ebenen, Muss-Bookmarks, erlaubte Zeichenlängen je Abschnitt.
   - Export/Import der Regeln als **JSON**.

6. **Projekte & Historie**
   - Projekte speichern (Quelle, gewählte Vorlage, Mapping-Entscheidungen, Exporte).
   - **Diff-Ansicht** zwischen zwei Exporten (z. B. Versionen vergleichen).

## Architektur & Tech-Stack
- **Backend**: Python **FastAPI**.
- **Word-Handling**: `python-docx` (Schreiben), `docx`/`mammoth` oder `python-docx` (Lesen & Struktur); Bilder/Tabellen extrahieren; ToC via Feldschalter (TOC) anlegen.
- **Fuzzy-Matching**: `rapidfuzz`.
- **Datenbank**: PostgreSQL (Metadaten), Objektspeicher (z. B. lokal/MinIO) für Binär-.docx.
- **Frontend**: React + TypeScript. Links: Vorlagen-Kapitelbaum; Rechts: Quellinhalt; Mitte: Mapping-Status. Drag-&-Drop, Ampel-Validierung.
- **Auth**: Email/Passwort (später OIDC möglich).
- **Tests**: Pytest (Backend), Playwright (E2E).

## Datenmodell (vereinfacht)
- `template(id, name, version, active, ruleset_id, uploaded_by, created_at)`
- `template_blob(template_id, file_uri, checksum)`
- `template_outline(template_id, json_outline)`  // Kapitelbaum + Styles + Bookmarks
- `ruleset(id, name, json_rules)`
- `project(id, name, template_id, created_by, created_at)`
- `source(id, project_id, type: 'paste'|'docx', file_uri?, normalized_json)`
- `mapping(id, project_id, mapping_json, status)`
- `export(id, project_id, file_uri, created_at)`

## API (Auswahl)
- `POST /templates` (multipart .docx) → validiert, speichert, extrahiert `template_outline`.
- `GET /templates`, `GET /templates/{id}`, `PUT /templates/{id}/activate`
- `POST /rulesets` / `GET /rulesets`
- `POST /import/paste` → normalisiert zu `normalized_json`
- `POST /import/docx` (multipart .docx) → normalisiert
- `POST /map/auto` → {normalized_json, template_outline, rules} → {mapping_json, score}
- `POST /map/manual` → speichert `mapping_json`
- `POST /export/docx` → liefert .docx-Datei

## Validierungslogik (beim Vorlagen-Upload)
- Prüfe, ob mindestens ein **TOC-Feld** existiert oder generierbar ist (ansonsten Flag „TOC erzeugen“).
- Parse alle **Heading-Styles** (built-in „Heading 1…3“). Warnung, wenn Überschriften nur formatiert, aber nicht als Heading-Style markiert sind.
- Verifiziere **Pflichtkapitel** aus dem **Ruleset**:
  - Exakte Überschrift oder Regex-Match (z. B. `^Einleitung$`, `^Inhaltsverzeichnis$` wird ausgeschlossen als Kapitel).
  - Keine Duplikate bei Bookmarks `{Name}`.
- Ergebnis als **ValidationReport** (Errors/Warnings/Infos) speichern.

## Mapping-Algorithmus (Skizze)
1. Erzeuge Kandidaten-Matches zwischen Quell-Headings und Ziel-Kapitel (Heading 1–3) per `rapidfuzz.fuzz.token_sort_ratio`.
2. Berücksichtige Synonyme/Aliase aus Ruleset: z. B. „Zusammenfassung“ ≈ „Management Summary“.
3. Harte Regeln zuerst anwenden:
   - Wenn Quellabschnitt mit `{Bookmark}` beginnt → direkte Zuordnung.
   - Wenn exakter Überschriftstreffer → Zuordnung.
4. Danach Fuzzy-Zuordnung mit **Score-Schwelle** (z. B. ≥ 85). Darunter → „Review nötig“.
5. Reihenfolge konservieren; Listen/Tabellen/Bilder dem zuletzt zugeordneten Kapitel anhängen.
6. Ergebnis als `mapping_json` speichern (inkl. Unsicherheiten/Confidence).

## UI-Details
- **Vorlagen-Pool**: Liste, Detailansicht (Kapitelbaum, Regeln, ValidationReport).
- **Import-Ansicht**: Editor/Preview, Word-Upload, Normalisierungsreport.
- **Mapping-Ansicht**: Split-View mit Drag-&-Drop, Statuschips (grün/gelb/rot), Filter „Ungemappte Elemente“.
- **Export-Ansicht**: Download .docx, erneutes Generieren mit anderer Vorlage/Regelsatz.

## Beispiel-Ruleset (JSON)
```json
{
  "required_headings": [
    {"level": 1, "label": "Titelblatt", "regex": "^Titelblatt$"},
    {"level": 1, "label": "Einleitung", "regex": "^Einleitung$"},
    {"level": 1, "label": "Methodik", "regex": "^Methodik$"},
    {"level": 1, "label": "Ergebnisse", "regex": "^Ergebnisse$"},
    {"level": 1, "label": "Fazit", "regex": "^Fazit$"}
  ],
  "allowed_heading_levels": [1,2,3],
  "forbidden_styles": ["Normal (Web)"],
  "bookmarks_required": [],
  "synonyms": {
    "Management Summary": ["Zusammenfassung", "Executive Summary"],
    "Methodik": ["Vorgehen", "Methoden"]
  },
  "min_fuzzy_score": 85,
  "toc_required": true,
  "max_section_length_chars": 20000
}
```

## Akzeptanzkriterien
- ✅ Upload einer ungültigen Vorlage erzeugt **klare Fehlermeldungen** (fehlende Pflichtkapitel, falsche Styles).
- ✅ Copy-Paste-Text mit Überschriften wird **korrekt erkannt** und kann automatisch zugeordnet werden; Unsicherheiten werden markiert.
- ✅ Word-Import mit Tabellen/Bildern bleibt erhalten und landet im richtigen Kapitel.
- ✅ Exportiertes .docx hat **korrektes ToC** (in Word aktualisierbar) und **Vorlagen-Styles**.
- ✅ Mindestens **80 %** automatisches Mapping bei sauber strukturierten Quellen (Testset bereitstellen).
- ✅ Projekte und Exporte sind reproduzierbar, inkl. Versionen der Vorlage/Regeln.

---

## Beispiel-User-Flow
1. Markus lädt „Bericht_v1.docx“ als Vorlage hoch → Validierung zeigt 1 Warnung (fehlendes Bookmark), 0 Fehler → Vorlage aktiv.
2. Markus fügt Quelltext per Copy-Paste ein → Normalisierung zeigt 12 Abschnitte, 5 Heading-1.
3. Auto-Mapping ergibt 10 grün, 2 gelb → Markus ordnet 2 Abschnitte per Drag-&-Drop zu.
4. Export → „Bericht_Ausgabe_2025-10-11.docx“ mit ToC, Bildern, Fußnoten.

---

## Testbare Beispiel-Dokumente (generieren)
- **Gültige Vorlage**: Enthält Heading 1–3, ToC-Feld, Pflichtkapitel.
- **Ungültige Vorlage**: Überschriften nur fett, kein ToC, doppelte Bookmarks.
- **Quelle**: Doc mit „Management Summary“, „Vorgehen“, Tabellen, 2 Bilder.

Implementiere Unit- und E2E-Tests für: Validierung, Normalisierung, Mapping, Export.

# Ende des Prompts


---

## Dein gewünschtes Sparring (kritisch & konstruktiv)

1) **Annahmen, die wackeln könnten**
- Du setzt voraus, dass ein ToC als statisches Objekt vorliegt. In Word wird das Inhaltsverzeichnis meist **automatisch aus Heading-Styles generiert**; wichtiger als „ToC vorhanden“ ist „Heading-Styles konsistent gesetzt“.  
- Du erwartest konsistente Kapitelnamen. In der Praxis heißen „Methodik“ auch „Vorgehen“ oder „Ansatz“. Ohne Synonyme/Fuzzy-Matching bricht die Automatik.  
- Du gehst davon aus, dass Copy-Paste die Struktur nicht zerstört. Viele Editoren strippen Styles – du brauchst eine robuste **Normalisierung**.

2) **Gegenargumente eines Skeptikers**
- „Warum Word-Vorlagen prüfen? Reicht nicht, beim Export Styles zu erzwingen?“ – Teilweise ja, aber **Pflichtkapitel und Bookmarks** lassen sich nur sauber sicherstellen, wenn die Vorlage geprüft ist.  
- „python-docx kann kein echtes ToC generieren!“ – Korrekt: Man setzt ein **TOC-Feld**, das in Word aktualisiert wird. Das muss im Design berücksichtigt werden.

3) **Logik-Check**
- Die Pipeline **Vorlage prüfen → Quelle normalisieren → mappen → exportieren** ist konsistent. Achte auf **Fehlerpfade**: Was passiert bei 30 % ungemapptem Inhalt? Lösung: Export blockieren oder explizit „Leer/entfällt“ erzwingen.

4) **Alternative Perspektiven**
- **OpenXML-SDK (.NET)** statt Python liefert feinere Kontrolle über ToC/Styles. Wenn du in Windows-Umgebungen bist, könnte C# die robustere Wahl sein.  
- **Template-Schema als JSON** (kapitelbaum + constraints) unabhängig von .docx speichern und beim Export erst auf die eigentliche .docx-Vorlage „aufprägen“. Erhöht Wiederverwendbarkeit.  
- **LLM-gestützte Segmentierung** für chaotische Quellen (optional), aber mit Vorsicht: deterministic first, AI second.

5) **Wahrheit vor Zustimmung – klare Empfehlungen**
- Implementiere **Fuzzy-Matching + Synonymliste** von Anfang an, sonst ist die Auto-Zuordnung zu schwach.  
- Erzwinge echte **Heading-Styles**; formatiertes „fett“ gilt als Fehler.  
- Plane **Versionierung** für Vorlagen und Regeln – sonst sind Exporte nicht reproduzierbar.

---

Wenn du willst, erstelle ich dir zusätzlich eine **Mini-Vorlage (.docx)** mit korrekten Heading-Styles und ein **Beispiel-Ruleset**, damit du sofort testen kannst, oder ich passe den Prompt auf einen **.NET/OpenXML-Stack** an.

### 3. Benutzer

Mini-Vorlage und Beispiel-Ruleset

### 4. Assistent

Funktioniert. Hier sind deine Dateien:

- [DocTemplate_Mini_Vorlage.docx](sandbox:/mnt/data/DocTemplate_Mini_Vorlage.docx)
- [Beispiel_Ruleset_Markus_Dickscheit_v1.json](sandbox:/mnt/data/Beispiel_Ruleset_Markus_Dickscheit_v1.json)

Kurz zur Nutzung:
- Die Vorlage enthält echte **Heading 1–3**, ein **Inhaltsverzeichnisfeld** (aktualisierbar in Word) und Beispiel-Bookmarks (u. a. bei Unterkapiteln mit `{…}`).
- Das Ruleset spiegelt die „Markus-Dickscheit“-Vorgaben wider (Pflichtkapitel, Synonyme, Fuzzy-Schwelle, TOC-Pflicht).  

Wenn du magst, passe ich dir das Ruleset an eure realen Kapitelbezeichnungen an oder füge „Muss-Bookmarks“ hinzu, die beim Vorlagen-Upload hart validiert werden.
