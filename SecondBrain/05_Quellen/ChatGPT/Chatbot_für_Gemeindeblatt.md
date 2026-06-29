---
title: "Chatbot für Gemeindeblatt"
type: chatgpt_conversation
source: chatgpt
source_id: "69e35d0d-2dfc-8391-8664-703d2e737f6c"
created: 2026-04-18
tags:
  - chatgpt
  - import
  - ki
  - obsidian
  - sap
  - verein
---


# Chatbot für Gemeindeblatt

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69e35d0d-2dfc-8391-8664-703d2e737f6c`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Ich möchte einen eigenen Chatbot zum erstellen meiner Beiträge fürs gemeindeblatt. Gib mir die Parameter und prompt

### 2. Assistent

Ziel: deterministischer, reproduzierbarer Textgenerator für Gemeindeblatt-Beiträge mit konsistenter Tonalität, korrekten Fakten, klarer Struktur.

---

## 1) Systemparameter (LLM-Konfiguration)

**Modellklasse**
- GPT-4/5-level (hohe Sprachqualität, stabile Stiltreue)

**Temperatur**
- 0.3–0.5  
Trade-off: niedriger = konsistent/korrekt; höher = variantenreicher, aber driftet im Stil.

**Top_p**
- 0.9  
Erhält Vielfalt ohne starke Halluzinationsneigung.

**Max Tokens**
- 800–1500 pro Beitrag  
Abhängig von Rubrik (Kurzmeldung vs. Leitartikel).

**Frequency Penalty**
- 0.2  
Reduziert Wiederholungen (Namen, Floskeln).

**Presence Penalty**
- 0.0–0.1  
Keine erzwungene Themenausweitung.

**Stop-Sequenzen**
- `["### ENDE", "—"]`  
Sauberer Abschluss, verhindert Abschweifen.

**Response-Format**
- Strukturiertes Markdown oder JSON (für Pipeline-Verarbeitung)

---

## 2) Rollenmodell (System Prompt)

Fixe Rolle für alle Runs:

```
Du bist Redakteur eines deutschen Gemeindeblatts.
Ziel: präzise, sachliche, lokal relevante Beiträge mit klarer Struktur.

Schreibe:
- neutral, verständlich, ohne Marketing-Sprache
- faktenbasiert, keine Spekulation
- kurze Sätze, aktive Formulierungen
- konkrete Angaben (Datum, Ort, Ansprechpartner)

Struktur:
1. Überschrift (max. 10 Wörter)
2. Teaser (1–2 Sätze, Kernaussage)
3. Haupttext (3–6 Absätze)
4. Infokasten (optional: Termine, Kontakt, Teilnahme)

Regeln:
- keine Emojis, keine Anglizismen ohne Notwendigkeit
- Zahlen konkret (z. B. „12. Mai 2026“, nicht „nächsten Monat“)
- Ortsbezug immer explizit nennen
- keine Füllsätze, keine Wiederholungen
- wenn Daten fehlen: Platzhalter [DATUM], [ORT], [KONTAKT]

Ausgabe strikt im definierten Format.
```

---

## 3) Eingabe-Schema (User Prompt Template)

Standardisierte Inputs für konsistente Outputs:

```
Thema: {z.B. Feuerwehrfest}
Ort: {Ortsteil/Gemeinde}
Datum: {konkretes Datum}
Veranstalter: {Verein/Institution}
Zielgruppe: {Bürger, Familien, Senioren, etc.}
Kernaussage: {was ist wichtig?}
Details:
- Programmpunkte:
- Uhrzeiten:
- Besonderheiten:
- Ansprechpartner:
- Kontakt:
Ton: {neutral | informativ | leicht einladend}
Länge: {kurz | mittel | lang}
```

---

## 4) Generativer Prompt (Runtime Prompt)

Kombination aus System + Input:

```
Erstelle einen Beitrag für ein Gemeindeblatt basierend auf folgenden Daten:

{EINGABE-SCHEMA}

Halte dich strikt an die vorgegebene Struktur und Regeln.
Vermeide Wiederholungen und unnötige Ausschmückung.
Wenn Informationen fehlen, verwende Platzhalter.
```

---

## 5) Output-Schema (für Weiterverarbeitung)

Markdown:

```
# {Überschrift}

**Teaser:** {Text}

{Absatz 1}

{Absatz 2}

{Absatz 3}

## Infos
- Termin:
- Ort:
- Veranstalter:
- Kontakt:
```

Optional JSON (für Automatisierung, CMS-Import):

```json
{
  "title": "",
  "teaser": "",
  "body": ["", "", ""],
  "info": {
    "termin": "",
    "ort": "",
    "veranstalter": "",
    "kontakt": ""
  }
}
```

---

## 6) Qualitätskontrolle (Post-Processing)

**Validierungsregeln**
- Titel ≤ 10 Wörter
- Jeder Absatz ≤ 80 Wörter
- Mindestens 1 konkretes Datum
- Keine verbotenen Muster: „wir freuen uns“, „herzlich willkommen“ (Marketing-Floskeln)

**Fehlermodi**
- Halluzinierte Details → Gegenmaßnahme: Pflichtfelder + Platzhalter
- Stilbruch → niedrige Temperatur + strikter Systemprompt
- Redundanz → Frequency Penalty + Längenlimit pro Abschnitt

---

## 7) Erweiterungen (optional)

**Mehrere Varianten**
- n=3 Generierungen → Auswahl per Heuristik (kürzester + vollständigster)

**Stilprofile**
- „amtlich“
- „bürgernah“
- „vereinsintern“

→ als zusätzlicher Parameter im Prompt

**Automatisierung**
- Input aus Formular (z. B. Vereinsmeldung)
- Output direkt ins CMS
- Batch-Generierung für ganze Ausgabe

---

## 8) Minimal funktionierendes Beispiel

**Input**
```
Thema: Frühjahrsputz Aktion
Ort: Mühlacker
Datum: 12. Mai 2026
Veranstalter: Stadtverwaltung
Zielgruppe: alle Bürger
Kernaussage: gemeinsames Reinigen öffentlicher Flächen
Details:
- Programmpunkte: Müllsammeln, Abschlussimbiss
- Uhrzeiten: 9:00–13:00
- Ansprechpartner: Bauhof
- Kontakt: bauhof@muehlacker.de
Ton: informativ
Länge: mittel
```

**Erwartetes Verhalten**
- keine Ausschmückung
- klare Struktur
- alle Fakten integriert
- keine erfundenen Inhalte

---

Ergebnis: stabiler, reproduzierbarer Redaktions-Chatbot mit kontrollierter Varianz, klaren Schnittstellen und geringer Fehlerquote.

### 3. Benutzer

Ich möchte diesen in Chat gpd anlegen um einen Artikel zu erstellen

### 4. Assistent

Ziel: Umsetzung direkt in entity["mobile_app","ChatGPT","OpenAI chat application"] ohne externe Infrastruktur. Ergebnis: wiederverwendbarer Redaktions-Chatbot (Custom GPT).

---

## 1) Architekturentscheidung

**Variante A: Custom GPT (empfohlen)**
- Persistenter Systemprompt
- Konfigurierbare Instruktionen
- Wiederverwendbar ohne Copy/Paste

**Variante B: Einmal-Prompt**
- Schnellstart, aber keine Persistenz
- Höhere Drift-Risiken

---

## 2) Einrichtung Custom GPT

Pfad:
- ChatGPT → „GPTs“ → „Create“

### 2.1 Name
- `Gemeindeblatt Redakteur`

### 2.2 Beschreibung
- `Erstellt strukturierte, sachliche Beiträge für ein deutsches Gemeindeblatt auf Basis definierter Eingaben.`

---

## 3) Instruktionen (System Prompt)

In das Feld „Instructions“ einfügen:

``` id="sys901"
Rolle: Redakteur eines deutschen Gemeindeblatts.

Ziel: Erstellung präziser, sachlicher, lokal relevanter Beiträge.

Schreibstil:
- neutral, verständlich, keine Werbung
- kurze Sätze, aktiv
- keine Floskeln
- keine Emojis

Struktur (zwingend):
1. Überschrift (max. 10 Wörter)
2. Teaser (1–2 Sätze)
3. Haupttext (3–6 Absätze)
4. Infokasten (Termin, Ort, Veranstalter, Kontakt)

Regeln:
- immer konkrete Daten (Datum, Uhrzeit, Ort)
- Ortsbezug explizit nennen
- keine Spekulationen
- keine erfundenen Inhalte
- fehlende Daten als [PLATZHALTER]

Validierung vor Ausgabe:
- Titel ≤ 10 Wörter
- keine Wiederholungen
- jeder Absatz < 80 Wörter

Ausgabeformat: Markdown
```

---

## 4) Conversation Starter (optional, aber sinnvoll)

``` id="start77"
Erstelle einen Beitrag.

Thema:
Ort:
Datum:
Veranstalter:
Zielgruppe:
Kernaussage:
Details:
- Programmpunkte:
- Uhrzeiten:
- Besonderheiten:
- Ansprechpartner:
- Kontakt:
Ton:
Länge:
```

---

## 5) Nutzung im Betrieb

Eingabe (jedes Mal strukturiert liefern):

``` id="run552"
Thema: Sommerfest Sportverein
Ort: Mühlacker
Datum: 20. Juni 2026
Veranstalter: TSV Mühlacker
Zielgruppe: Familien
Kernaussage: jährliches Vereinsfest
Details:
- Programmpunkte: Spiele, Turniere, Musik
- Uhrzeiten: 14:00–22:00
- Besonderheiten: Kinderprogramm
- Ansprechpartner: Vorstand
- Kontakt: info@tsv-muehlacker.de
Ton: informativ
Länge: mittel
```

---

## 6) Steuerparameter (indirekt)

In ChatGPT nicht explizit einstellbar, daher über Prompt simulieren:

- Kreativität ↓ → „keine Ausschmückung“
- Konsistenz ↑ → „strikte Struktur“
- Halluzination ↓ → „keine erfundenen Inhalte + Platzhalterpflicht“

---

## 7) Fehlerquellen und Gegenmaßnahmen

**Problem: erfundene Details**
- Ursache: fehlende Inputs
- Maßnahme: harte Platzhalterregel im Prompt

**Problem: Stil driftet**
- Ursache: lange Sessions
- Maßnahme: neue Konversation pro Artikel

**Problem: zu lang / zu weich**
- Ursache: unklare Länge
- Maßnahme: Parameter „Länge: kurz|mittel|lang“ erzwingen

---

## 8) Skalierung

**Mehrere Artikel pro Ausgabe**
- Batch: mehrere Eingaben nacheinander
- Konsistenz bleibt durch festen Systemprompt stabil

**Standardisierung**
- Einheitliche Eingabemaske (Formular → Copy in ChatGPT)

---

## 9) Minimaler Workflow

1. Custom GPT öffnen  
2. Eingabemaske ausfüllen  
3. Output prüfen (30–60 Sekunden)  
4. Direkt ins Layout/CMS übernehmen  

---

Ergebnis: deterministischer Redaktionsprozess innerhalb von ChatGPT ohne zusätzliche Tools, mit kontrollierter Qualität und minimalem manuellen Aufwand.
