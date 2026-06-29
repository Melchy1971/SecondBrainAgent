---
title: "KI Website Erstellung A11Y"
type: chatgpt_conversation
source: chatgpt
source_id: "682f0277-d6f0-8007-b012-a9993a8ec55e"
created: 2025-05-22
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
  - tischtennis
  - verein
---


# KI Website Erstellung A11Y

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `682f0277-d6f0-8007-b012-a9993a8ec55e`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

mit welcher AI erstelle ich eine private website auf basis einer vorhandenen seite und erstelle diese neu inkl. barriere freiheit zu beachten

### 2. Assistent

**Welche KI-Systeme eignen sich?**

| Szenario | Empfehltes KI-Tool | Stärken für Barrierefreiheit |
|----------|-------------------|------------------------------|
| **„Einfach klicken – fertig“** | **Wix AI Website Builder** + Accessibility Wizard | Chat-Geführte Site-Generierung in Minuten; Wizard scannt die fertige Seite, zeigt Kontrast-, Fokus- und Alt-Text-Probleme an und liefert Schritt-für-Schritt-Fixes. citeturn7search3turn7search0 |
| **Deutscher Hoster & BFSG-Konformität** | **STRATO SmartWebsite** (KI-Text-Optimierer, KI-Bildgenerator) | Fokus auf das Barrierefreiheitsstärkungsgesetz; KI vereinfacht Sprache, erzeugt Alt-Texte und semantisches HTML. citeturn2view0turn8view0 |
| **Design-Freiheit & Animation** | **Framer AI** (Wireframer + Workshop) | Generiert responsive Layouts und Komponenten; April-Update verbessert die A11Y der Seitennavigation. citeturn9view0 |
| **Volle Code-Kontrolle** | **Google “Stitch”** | Wandelt Text- oder Bild-Prompts in sauberes HTML/CSS um, Export nach Figma oder IDE möglich. citeturn6view0 |
| **Privater Mini-Shop** | **Shopify AI Store Builder** | Erzeugt komplette Shop-Layouts (Bilder, Texte, Struktur) aus Stichwörtern. citeturn5view0 |

---

### So gehst du praktisch vor

1. **Bestandsaufnahme**  
   - Alte Seite mit Lighthouse / WAVE / axe-core prüfen und Schwachstellen notieren.

2. **Content-Migration**  
   - Nur Inhalte übernehmen, an denen du die Rechte hältst.  
   - KI-Tools (z. B. STRATO-Text-Optimierer oder ChatGPT) nutzen, um Texte in Leichter Sprache und Alt-Texte vorzubereiten.

3. **KI-Site-Generierung**  
   - Gewünschtes Tool wählen, Inhalte importieren, Grund-Layout erzeugen lassen.

4. **Feinschliff & A11Y-Tests**  
   - Integrierte Assistenten (Wix Wizard, Framer Preview, Stitch-Linting) durchlaufen.  
   - Semantische Überschriften, ARIA-Labels, Skip-Links, Tastatur-Fokus, Kontrast und Responsive Design korrigieren.

5. **Pflicht-Check**  
   - Bis **28. Juni 2025** müssen viele deutsche Websites laut Barrierefreiheits­stärkungs­gesetz die WCAG 2.2-AA-Kriterien erfüllen. citeturn8view0

6. **User-Tests**  
   - Seite kurz von Personen mit Screen-Reader, Tastatur-Only-Navigation und Farbsehschwäche testen lassen.

---

### Entscheidungshilfe in einem Satz  
*Wenn du gar nicht coden willst, nimm Wix AI; willst du deutschen Support + Rechtssicherheit, nimm STRATO; liebst Design-Freiheit, nimm Framer; brauchst reinen Code, nimm Stitch; soll’s ein Shop werden, nimm Shopify.*  

**Wichtig:** Kein Tool nimmt dir den letzten Accessibility-Feinschliff komplett ab – plane immer etwas Zeit für manuelle WCAG-Tests ein, dann bist du nicht nur gesetzeskonform, sondern erreichst wirklich alle Besucher:innen.

### 3. Benutzer

kostenloses tool verwenden

### 4. Assistent

### 100 % kostenlose KI-Bausteine für dein Relaunch-Projekt  

| Aufgabe | Gratis-Tool | Warum es passt |
|---------|------------|----------------|
| **Neue Seiten per KI generieren** | **TeleportHQ – AI Website Builder** <br>Free-Plan mit Code-Export, bis zu 3 Seiten je Projekt, Veröffentlichung und HTML/React-Export kostenfrei. citeturn6view0 |
| | **Dora AI** <br>Aktuell (Alpha 2.0) komplett gratis, erzeugt sogar 3-D-Layouts in einem Prompt. citeturn8view0 |
| | **Butternut AI** <br>“Freemium” – unbegrenzt viele Website-Generierungen und Basis-Anpassungen ohne Abo. citeturn7view0 |
| **Automatisierte A11Y-Checks** | **Google Lighthouse** (im Chrome DevTools) – Open Source, prüft WCAG-konforme Kontraste, ARIA-Struktur u. v. m. citeturn10search3 |
| | **Pa11y** – CLI & Dashboard, komplett Open Source, lässt sich in jedes Build- oder CI-Skript hängen. citeturn9view0 |

---

## Schritt-für-Schritt-Leitfaden

1. **Alte Inhalte sichern**  
   *Mit HTTrack oder dem Browser “Als HTML speichern” herunterladen.*  
   Strukturiere Texte und Bilder lokal (z. B. Markdown-Dateien), damit du sie später per Copy-&-Paste oder Upload in das KI-Tool schieben kannst.

2. **Seiten per KI neu erzeugen**  
   - **TeleportHQ**: Erstelle ein Free-Projekt, gib eine Kurzbeschreibung („Portfolio einer Fotografin …“) ein und lass dir bis zu drei Screens generieren. Anschließend per Drag-&-Drop verfeinern und als React/Vue oder pures HTML exportieren.  
   - **Dora AI** (falls du Eye-Candy und Animation willst) oder **Butternut AI** (wenn du schnell viele Varianten testen möchtest) funktionieren ähnlich.  

3. **Barrierefreiheit sofort im Editor beachten**  
   - Überschriften richtig gliedern ( `<h1>` → `<h2>` → … ).  
   - Für alle Bilder gleich Alt-Texte eintragen – die Generatoren füllen sie manchmal leer.  
   - Farb­kontraste prüfen (TeleportHQ und Dora zeigen dir live HEX-Farben; halte Ratio ≥ 4.5:1).

4. **Automatisierte Audits fahren**  
   ```bash
   # einmalige CLI-Prüfung
   npx pa11y https://localhost:3000
   
   # DevTools → Lighthouse → “Accessibility” ausführen
   ```  
   Behebe gemeldete Fehler (z. B. fehlende Labels, geringer Kontrast). Mit jedem Commit kannst du Pa11y CI im GitHub-Action-Workflow laufen lassen, um Regressionen zu verhindern.

5. **Manuelle Checks nicht vergessen**  
   - Ganze Seite nur mit **Tab** bedienen.  
   - **Screen-Reader-Kurztest** (NVDA oder VoiceOver).  
   - Farb­seh­schwächen-Simulator benutzen (z. B. Chrome-Erweiterung „VisBug“).

6. **Veröffentlichen & warten**  
   Beim Free-Plan von TeleportHQ erhältst du ein kostenloses Sub-Domain-Hosting; alternativ lädst du den Code zu Netlify, Vercel oder GitHub Pages hoch. Auch dort kannst du Lighthouse-Reports als Pull-Request-Check integrieren.

---

### Kurzentscheidung

- **Nur eine Handvoll Seiten?** → **TeleportHQ** (schnell, sauberer Code-Export).  
- **Fancy 3-D-Landingpage?** → **Dora AI**.  
- **Viele-Versionen-Test & Blog-Fokus?** → **Butternut AI**.  

> **Tipp:** Egal für welches Tool du dich entscheidest – die Kombination aus *kostenlosem* Generator + *Open-Source*-Tests (Lighthouse/Pa11y) bringt dich ohne Budget ans Ziel **und** hält das Projekt vor dem BFSG-Stichtag (28. Juni 2025) rechtssicher.
