---
title: "Add-in für Vorlagenintegration"
type: chatgpt_conversation
source: chatgpt
source_id: "69c663ef-8ae8-8389-a5b5-5d0eaf3089dc"
created: 2026-03-27
tags:
  - chatgpt
  - import
  - ki
  - projekt
  - sap
---


# Add-in für Vorlagenintegration

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69c663ef-8ae8-8389-a5b5-5d0eaf3089dc`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich habe von meiner firma ein master template für powerpoint und word erhalten nun möchte ich ein add in bauen mit welchem ich erstellte texte in diese vorlage integrieren kann und somit das format übernehme. kannst du mir soetwas bauen

### 2. Assistent

Ja.

Ich habe dir ein lauffähiges MVP als Office-Add-in-Projekt gebaut:
[office-template-addin.zip](sandbox:/mnt/data/office-template-addin.zip)

Was das Add-in jetzt kann:

- **Word**: Text aus dem Taskpane einfügen und auf selektierte Absätze definierte **Word-Stilnamen** anwenden. Das ist der saubere Weg, wenn dein Firmendokument bzw. die Vorlage die Corporate Styles bereits enthält, weil Word-Absätze direkt einen Stilnamen tragen können. citeturn316772search14turn316772search2
- **PowerPoint**: selektierten Text typografisch formatieren oder auf der gewählten Folie eine neue Textbox mit Corporate-Schrift, -Größe und -Farbe erzeugen. Die PowerPoint-JavaScript-API unterstützt Textbereiche, Formen und Textboxen, sodass dieser Weg technisch belastbar ist. citeturn316772search1turn989942search4turn989942search13turn316772search16

Wichtige Systemgrenze:

- **Word** lässt sich gut über Stilnamen an dein Master-Template anbinden. citeturn316772search14turn316772search5
- **PowerPoint** ist deutlich restriktiver. Für bestehende Folien gibt es in Office.js keine volle Kontrolle über das erneute Anwenden von Slide Master oder Theme. Deshalb ist ein robuster Produktivansatz meist: **vordefinierte Template-Folien einfügen und nur Platzhaltertexte ersetzen**, statt freie Folien nachträglich “auf Corporate” zu ziehen. Microsoft dokumentiert heute Text-/Shape-Zugriff und das Einfügen von Folien aus einer anderen Präsentation; genau das ist für so einen Anwendungsfall die stabilere Richtung. citeturn316772search3turn316772search7turn316772search1turn989942search4

In der ZIP sind enthalten:

- `manifest.xml`
- `src/taskpane.html`
- `src/taskpane.js`
- `README.md`
- einfache Icons
- `package.json`

Implementierte Logik:

- Konfiguration lokaler Style-Mappings
- Word-Mapping:
  - `Titel -> Title`
  - `Heading 1 -> Heading 1`
  - `Body -> Normal`
- PowerPoint-Mapping:
  - Font Name
  - Title Size
  - Body Size
  - Font Color
  - Textbox-Position

Technische Bewertung:

1. **Für Word** ist dieses Muster produktionsnah.
2. **Für PowerPoint** ist es nur ein MVP.
3. Für eine echte Unternehmenslösung solltest du auf dieses Zielmodell gehen:
   - **Word**: Template mit stabilen Stilnamen oder Content Controls
   - **PowerPoint**: Bibliothek aus Template-Folien + Platzhalterersetzung
   - **Konfiguration**: JSON-Mapping `contentType -> style/layout`

Installationslogik:

- Projekt lokal hosten
- Manifest in Word/PowerPoint als Add-in laden
- Taskpane öffnen
- Text einfügen oder Auswahl formatieren

Im README steht die lokale Inbetriebnahme.

Was noch fehlt, um daraus deine echte Firmenlösung zu machen:

- Einbindung deiner **realen Word-Vorlage** (`.dotx/.docx`)
- Einbindung deiner **realen PowerPoint-Vorlage** (`.potx/.pptx`)
- Extraktion der **exakten Stilnamen**
- Definition der **Layout-Mappings**
- optional REST-API-Anbindung für KI-generierte Texte

Nächster sinnvoller Ausbauschritt wäre ein **Version-2-Add-in**, das:
- deine reale Vorlage einliest,
- Word-Styles automatisch erkennt,
- in PowerPoint definierte Template-Slides einfügt,
- Platzhalter wie `{{title}}`, `{{summary}}`, `{{bullets}}` ersetzt.
