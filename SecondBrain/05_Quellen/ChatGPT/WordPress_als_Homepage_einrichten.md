---
title: "WordPress als Homepage einrichten"
type: chatgpt_conversation
source: chatgpt
source_id: "67926ee8-3eac-8007-8ba7-727499f94efb"
created: 2025-01-23
tags:
  - chatgpt
  - import
  - sap
---


# WordPress als Homepage einrichten

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67926ee8-3eac-8007-8ba7-727499f94efb`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Wie stelle ich wordpress so ein das es sich wie eine homepage verhält und niemand Einträge erstellen kann

### 2. Assistent

Um WordPress wie eine klassische Homepage einzurichten, bei der niemand Blog-Einträge erstellen kann, solltest du einige Einstellungen und Anpassungen vornehmen. Hier eine Schritt-für-Schritt-Anleitung:

---

### 1. **Startseite und statische Seiten einrichten**
- **Statische Startseite wählen:**
  1. Erstelle eine neue Seite unter **Seiten > Erstellen** (z. B. „Startseite“).
  2. Erstelle eine weitere Seite für den Blog (z. B. „Blog“), falls du später Blog-Einträge haben möchtest.
  3. Gehe zu **Einstellungen > Lesen**.
  4. Wähle unter **Startseite zeigt** die Option **Eine statische Seite**.
  5. Setze „Startseite“ auf die zuvor erstellte Seite „Startseite“. Wenn du keine Blog-Seite willst, lasse den „Beiträge“-Bereich leer.

---

### 2. **Beiträge deaktivieren**
Wenn du keine Blog-Funktion möchtest:
- Gehe zu **Design > Menüs** und entferne Links zu „Blog“ oder ähnlichen Seiten aus deinem Menü.
- Optional: Deaktiviere die Funktion für Beiträge komplett, indem du ein Plugin wie **"Disable Blog"** installierst.

---

### 3. **Kommentarfunktion deaktivieren**
- Gehe zu **Einstellungen > Diskussion** und deaktiviere die Optionen wie:
  - „Erlaube Besuchern, neue Kommentare zu schreiben.“
- Entferne bestehende Kommentarbereiche:
  1. Öffne eine Seite oder einen Beitrag im Editor.
  2. Im Bereich **Diskussion** (unten im Editor) deaktiviere „Kommentare erlauben“. Falls du diesen Bereich nicht siehst, aktiviere ihn in den **Bildschirmoptionen** oben rechts.

---

### 4. **Benutzerrollen einschränken**
- Gehe zu **Einstellungen > Allgemein** und stelle sicher, dass „Jeder kann sich registrieren“ deaktiviert ist.
- Unter **Neue Benutzerrolle** wähle **Abonnent**, damit neue Benutzer keine Bearbeitungsrechte haben.

---

### 5. **Design anpassen**
- Wähle ein passendes Theme, das sich für statische Seiten eignet (z. B. „Astra“, „Neve“ oder „GeneratePress“).
- Passe das Menü unter **Design > Menüs** an, um Links zu den gewünschten Seiten (z. B. „Über uns“, „Kontakt“) einzufügen.

---

### 6. **Widgets und Seitenleisten aufräumen**
- Gehe zu **Design > Widgets** und entferne oder deaktiviere Widgets, die Beiträge, Kategorien oder Kommentare anzeigen.

---

### 7. **Extras mit Plugins hinzufügen**
Falls du erweiterte Funktionen für eine statische Homepage brauchst:
- **Elementor** oder **Beaver Builder**: Erstellen von Seiten mit einem Drag-and-Drop-Editor.
- **Disable Comments**: Entfernt alle Kommentarbereiche global.
- **Coming Soon Page** oder ähnliche Plugins, um die Seite vorübergehend offline zu stellen, während du sie einrichtest.

---

Nach diesen Anpassungen wird deine WordPress-Seite wie eine klassische Homepage funktionieren, ohne dass Blog-Einträge oder Kommentare sichtbar sind.
