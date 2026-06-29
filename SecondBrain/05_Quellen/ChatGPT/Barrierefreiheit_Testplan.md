---
title: "Barrierefreiheit Testplan"
type: chatgpt_conversation
source: chatgpt
source_id: "682f2ee8-58c0-8007-9d9f-7897ff0305fb"
created: 2025-05-22
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# Barrierefreiheit Testplan

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `682f2ee8-58c0-8007-9d9f-7897ff0305fb`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

erstelle einen Test für eine website in welcher ein album hinterlegt ist in welchem die räume des kindergarten gezeigt werden um barrierefrei zu sein

### 2. Assistent

### Barrierefreiheits-Testplan – Foto-Album „Räume des Kindergartens“

| ID | Prüfziel | Prüfschritte (manuell, Tastatur, SR* etc.) | Erwartetes Ergebnis | WCAG / BITV-Bezug |
|---|---|---|---|---|
| T-01 |Alle Bilder sind inhaltlich beschrieben|Seite laden → Zufällig 5 Fotos im Album auswählen → Quellcode oder CMS-Feld prüfen|Jedes Foto besitzt einen aussagekräftigen `alt`-Text (z. B. „Gruppenraum Sternchen mit runder Leseecke“)|1.1.1 Non-text Content citeturn0search4|
| T-02 |Album vollständig per Tastatur nutzbar|Mit <kbd>Tab</kbd>/<kbd>Shift + Tab</kbd> Album öffnen, Fotos durchblättern, Lightbox schließen|Fokus erreicht jedes interaktive Element; kein „Keyboard Trap“|2.1.1 Keyboard citeturn0search3 & 2.1.2 No Keyboard Trap citeturn0search5|
| T-03 |Fokus stets sichtbar|Während T-02 beobachten, ob der sichtbare Fokus nie verdeckt wird (z. B. bei Karussell-Pfeilen)|Fokus-Umrandung ist mindestens teilweise sichtbar|2.4.11 Focus Not Obscured (Level AA) citeturn0search11|
| T-04 |Kontrast & Lesbarkeit|Albumtitel, Bildbeschriftungen und Pfeile mit WCAG-Kontrast-Checker prüfen|Text ≥ 4.5:1 (normal) bzw. 3:1 (groß); Bedienelement-Glyphen ≥ 3:1|1.4.3 / 1.4.11|
| T-05 |Skalierung/Zoom|Browser-Zoom auf 200 % → alle Funktionen erneut bedienen|Kein horizontales Scrollen, Inhalte und Bedienelemente vollständig erreichbar|1.4.4 Resize Text; 1.4.10 Reflow|
| T-06 |Screen-Reader-Ausgabe (NVDA/JAWS/VoiceOver)|Album öffnen → mit Pfeiltasten durch Bilder|SR liest Überschrift, Bildposition (z. B. „Bild 3 von 12“) und `alt`-Text; keine irrelevanten Dateinamen|1.3.1 Info & Relationships|
| T-07 |Cognitive feedback|Foto als Favorit markieren oder herunterladen|Nach Aktion erscheint verständliche Bestätigung (z. B. ARIA-`live`-Region)|4.1.3 Status Messages (WCAG 2.2)|
| T-08 |Mobil-first / Touch|Album auf Smartphone-Viewport (≤ 320 px) testen|Bedienelemente ≥ 48 × 48 CSS-px (SC 2.5.8 Target Size Min)|2.5.8 (neu in 2.2)|
| T-09 |Zeitbasierte Medien (falls Rundgang-Video enthalten)|Video abspielen → Untertitel/Transkript prüfen|Untertitel vorhanden; Audiodeskription oder gleichwertige Info|1.2.x Audiovisuell|
| T-10 |Rechtliche Erklärung|Fußzeile → „Erklärung zur Barrierefreiheit“ öffnen|Erklärung verfügbar, aktuell, enthält Feedback-Kontakt und Durchsetzungs­stelle gemäß BITV 2.0 §7 / BGG §12b|BITV 2.0 citeturn1search3|

\* SR = Screen Reader

---

#### Vorgehen & Werkzeuge
1. **Automatisierte Erstprüfung**: WAVE, axe, Lighthouse Barrierefreiheit – als Vorfilter, decken ~30 % der Kriterien.  
2. **Manuelle WCAG-Referenztests**: gemäß obiger Tabelle, Browser-DevTools für Kontrastprüfung.  
3. **Assistive-Technik-Tests**:  
   * **Tastatur-Only** (Windows + macOS)  
   * **Screen-Reader** (NVDA + Firefox, JAWS + Chrome, VoiceOver + Safari)  
4. **Geräte-Varianten**: 13″-Laptop, 6.1″-Smartphone (Portrait & Landscape), 10″-Tablet.  
5. **Dokumentation**: Jede Abweichung mit Screenshot, Schritt, IST-/SOLL-Zustand und Schweregrad (kritisch, hoch, mittel, niedrig).  
6. **Konformitätsziel**: WCAG 2.2 Level AA gemäß EN 301 549; damit Erfüllung BITV 2.0 in Deutschland. citeturn0search2turn0search6turn1search3

---

#### Tipps für die Entwicklung
- **Alt-Texte kuratieren**: Atmosphäre & Raumfunktion beschreiben, keine vermutlich irrelevanten Angaben (Dateiname, „Bild 1“).  
- **Bedienpfad klar halten**: Karussell-Pfeile <kbd>Enter</kbd>/<kbd>Space</kbd> aktivierbar, ESC schließt die Lightbox.  
- **ARIA roles/labels**: Albumcontainer `role="region"` mit aussagekräftigem `aria-label`, innerhalb `aria-live="polite"` für dynamische Meldungen.  
- **Progressive Enhancement**: Album funktioniert ohne JavaScript (Fallback-Liste), damit Grundinformation immer zugänglich bleibt.

Mit diesem Testplan decken Sie alle wesentlichen technischen und rechtlichen Anforderungen ab und können systematisch nachweisen, dass das Album – und damit die gesamte Website – barrierefrei nutzbar ist.
