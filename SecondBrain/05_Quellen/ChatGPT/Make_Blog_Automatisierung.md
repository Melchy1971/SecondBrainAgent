---
title: "Make Blog Automatisierung"
type: chatgpt_conversation
source: chatgpt
source_id: "67b56cc2-89a8-8007-984f-ffb79ef2ae9a"
created: 2025-02-19
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# Make Blog Automatisierung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67b56cc2-89a8-8007-984f-ffb79ef2ae9a`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Erstelle mir einen Agenten mit Make welcher mir das Internet nach Chat Tod durchsucht und daraus ein Blog generiert der auf wordpress veröffentlicht wird

### 2. Assistent

Im Folgenden findest du einen beispielhaften Workflow (Szenario) für Make, der automatisch das Internet nach Inhalten zu „Chat Tod“ durchsucht, daraus einen Blogartikel generiert und diesen über die WordPress-Integration veröffentlicht. Beachte, dass du für die einzelnen Schritte ggf. entsprechende API-Zugänge (z. B. zu einer Such-API und – falls du einen externen Textgenerator einbinden möchtest – zu einer GPT‑API) benötigst.

---

### 1. Szenario-Trigger einrichten

- **Scheduler-Modul**: Starte dein Szenario z. B. täglich oder in einem gewünschten Intervall.  
  *Beispiel:* „Täglich um 9:00 Uhr.“

---

### 2. Inhalte im Internet suchen

- **HTTP-Modul (GET)**:  
  - Wähle einen Suchdienst, der eine API anbietet (z. B. [Google Custom Search](https://developers.google.com/custom-search/v1/overview) oder [Bing Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)).  
  - Konfiguriere die Anfrage mit dem Suchbegriff „Chat Tod“.  
  - Verarbeite die JSON-Antwort, um relevante Felder (z. B. Titel, Snippet, URL) zu extrahieren.

*Hinweis:* Achte auf API-Limits und Authentifizierungsanforderungen.

---

### 3. Inhalte aggregieren und Blogartikel generieren

- **Datenaufbereitung**:  
  - Nutze Make-Module wie „JSON Parse“ oder „Text Aggregator“, um die gefundenen Ergebnisse zu sammeln und zu strukturieren.  
  - Eventuell Filter: Du kannst z. B. nur Artikel mit hoher Relevanz oder aus bestimmten Quellen weiterverwenden.

- **Textgenerierung (optional, z. B. über ChatGPT-API)**:  
  - Wenn du den Blogartikel dynamisch generieren möchtest, kannst du ein Modul einbinden, das die gesammelten Daten als Input an einen Textgenerator sendet.  
  - Beispiel: Ein Modul, das über die OpenAI-API eine Zusammenfassung oder einen Artikeltext erstellt, basierend auf den extrahierten Suchergebnissen.

- **Manuelle Zusammenführung:**  
  - Alternativ kannst du die aggregierten Daten auch formatieren und mithilfe von Formatierungsmodulen (wie z. B. „Text Formatter“) in einen Artikel-Text überführen.

---

### 4. Veröffentlichung in WordPress

- **WordPress-Modul in Make:**  
  - Konfiguriere das WordPress-Modul, indem du deine WordPress-URL, Benutzername und ein Anwendungs- oder API-Passwort einträgst.  
  - Erstelle einen neuen Post, indem du den generierten Titel (z. B. „Insights zu Chat Tod – [Datum]“) und den Artikeltext als Inhalt einfügst.  
  - Optional: Du kannst noch weitere Parameter setzen (Kategorie, Schlagwörter etc.).

---

### 5. Zusammengefasstes Szenario

1. **Trigger:**  
   - Scheduler-Modul startet das Szenario täglich.

2. **Datenabruf:**  
   - HTTP-Modul führt einen GET-Request an die gewählte Such-API mit der Query „Chat Tod“ aus.  
   - Ergebnisse werden als JSON abgerufen.

3. **Datenverarbeitung:**  
   - JSON-Parsing-Module extrahieren relevante Inhalte (Titel, Snippets, URLs).  
   - Ein Aggregationsmodul fasst die Inhalte zusammen.

4. **Artikelgenerierung:**  
   - (Optional) Ein Textgenerator-Modul (z. B. OpenAI) erstellt basierend auf den aggregierten Daten einen zusammenhängenden Blogartikel.  
   - Alternativ: Du kombinierst die Ergebnisse manuell mit Formatierungsmodulen.

5. **Veröffentlichung:**  
   - WordPress-Modul postet den generierten Artikel als neuen Blogbeitrag auf deiner WordPress-Seite.

---

### Umsetzungshinweise

- **API-Zugänge:**  
  Stelle sicher, dass du für alle verwendeten APIs (Suchmaschine, Textgenerator, WordPress) gültige Zugangsdaten und API-Schlüssel hast.

- **Fehlerbehandlung:**  
  Baue in dein Szenario Fehlerprüfungen ein (z. B. was passiert, wenn keine relevanten Suchergebnisse gefunden werden).

- **Testen:**  
  Teste jeden Schritt einzeln in Make, um sicherzustellen, dass die Daten korrekt abgerufen, verarbeitet und letztlich veröffentlicht werden.

---

Mit diesem Ansatz hast du eine Grundlage, um in Make einen Agenten zu erstellen, der automatisch Inhalte zum Thema „Chat Tod“ sammelt, einen Blogartikel generiert und diesen auf deiner WordPress-Seite veröffentlicht. Natürlich können je nach deinen Anforderungen weitere Module oder Anpassungen notwendig sein.

Wenn du weitere Details oder Unterstützung bei der konkreten Implementierung (z. B. Skripte für die HTTP-Anfragen oder die Textgenerierung) benötigst, lass es mich wissen!

### 3. Benutzer

Erstelle mir einen Agenten mit Make welcher mir das Internet nach Chat Gpd durchsucht und daraus ein Blog generiert der auf wordpress veröffentlicht wird

### 4. Assistent

Im Folgenden findest du ein Beispiel, wie du mit Make (ehemals Integromat) einen Agenten erstellst, der das Internet nach Inhalten zum Thema „Chat Gpd“ durchsucht, daraus einen Blogartikel generiert und diesen anschließend auf einer WordPress-Seite veröffentlicht. Beachte, dass du für die verwendeten APIs (Such-API, ggf. Textgenerierung über OpenAI und WordPress) jeweils gültige API-Schlüssel benötigst.

---

## 1. Szenario-Übersicht

Das Szenario gliedert sich in folgende Schritte:

1. **Trigger:** Festlegen, wann das Szenario ausgeführt werden soll (z. B. täglich).
2. **Internet-Recherche:** Suchen nach Inhalten zum Stichwort „Chat Gpd“ über eine Such-API.
3. **Datenverarbeitung:** Aufbereiten und ggf. Aggregieren der Suchergebnisse.
4. **Artikelgenerierung:** (Optional) Dynamisches Erzeugen eines Blogbeitrags mithilfe eines Textgenerators (z. B. OpenAI).
5. **Veröffentlichung:** Posten des Artikels über die WordPress-Integration.

---

## 2. Detaillierte Umsetzung

### Schritt 1: Trigger einrichten

- **Scheduler-Modul:**  
  - Lege fest, wann dein Agent aktiv werden soll (z. B. täglich um 8:00 Uhr).  
  - Dieses Modul startet dein Szenario automatisch.

### Schritt 2: Inhalte im Internet suchen

- **HTTP-Modul (GET):**  
  - Wähle einen Suchdienst, der eine API anbietet, wie z. B. [Bing Web Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) oder [Google Custom Search API](https://developers.google.com/custom-search/v1/overview).  
  - Konfiguriere die Anfrage mit dem Suchbegriff „Chat Gpd“.  
  - Achte darauf, die API-Authentifizierung (z. B. API-Schlüssel) korrekt einzurichten.

- **Beispiel-Request:**  
  ```http
  GET https://api.bing.microsoft.com/v7.0/search?q=Chat+Gpd
  Headers: { "Ocp-Apim-Subscription-Key": "DEIN_API_KEY" }
  ```

### Schritt 3: Datenverarbeitung

- **JSON Parsing:**  
  - Nutze ein JSON-Parsing-Modul, um die Antwort zu verarbeiten und relevante Daten wie Titel, Beschreibung/Snippet und URL der gefundenen Inhalte zu extrahieren.

- **Filter und Aggregation:**  
  - Filtern die Ergebnisse ggf. nach Relevanz.  
  - Aggregiere die Inhalte, sodass sie als Grundlage für den Blogartikel dienen können.

### Schritt 4: Blogartikel generieren

Es gibt zwei Ansätze:

1. **Manuelle Zusammenführung:**  
   - Verwende Text-Formatter-Module, um die aggregierten Informationen in einen strukturierten Artikel (mit Einleitung, Hauptteil und Schluss) zu überführen.

2. **Automatisierte Textgenerierung:**  
   - Binde ein Modul ein, das über die OpenAI-API (z. B. ChatGPT) basierend auf den extrahierten Daten einen zusammenhängenden Blogtext erstellt.  
   - Übergib dem Modul einen Prompt, der die gesammelten Inhalte integriert und einen lesbaren, informativen Artikel generiert.

   **Beispiel-Prompt:**  
   ```
   Erstelle einen Blogartikel basierend auf folgenden Informationen: [Liste der aggregierten Inhalte]. Der Artikel soll eine Einleitung, einen Hauptteil und einen abschließenden Kommentar enthalten.
   ```

### Schritt 5: Veröffentlichung in WordPress

- **WordPress-Modul:**  
  - Konfiguriere das Modul mit deiner WordPress-URL, Benutzername und einem Anwendungs- oder API-Passwort.  
  - Fülle die notwendigen Felder wie Titel, Inhalt und Kategorie aus.  
  - Beispiel:  
    - **Titel:** „News zu Chat Gpd – [aktuelles Datum]“
    - **Inhalt:** Der generierte Artikeltext

- **Veröffentlichung:**  
  - Sende die Daten an deine WordPress-Seite, sodass der Blogartikel automatisch als neuer Beitrag veröffentlicht wird.

---

## 3. Zusammenfassung des Szenarios

1. **Trigger:**  
   - Scheduler-Modul startet das Szenario zu definierten Zeiten.

2. **Datenabruf:**  
   - HTTP-Modul führt eine GET-Anfrage an eine Such-API mit dem Query „Chat Gpd“ aus.
   - Ergebnisse werden als JSON abgerufen.

3. **Datenverarbeitung:**  
   - JSON-Parser extrahiert relevante Inhalte.
   - Mit Filter- und Aggregationsmodulen werden die Daten aufbereitet.

4. **Artikelgenerierung:**  
   - Entweder manuell via Text-Formatter oder automatisiert über die OpenAI-API wird ein Blogartikel erstellt.

5. **Veröffentlichung:**  
   - Das WordPress-Modul postet den Artikel als neuen Blogbeitrag.

---

## 4. Zusätzliche Hinweise

- **API-Schlüssel und Limits:**  
  Stelle sicher, dass du für alle verwendeten APIs (Such-API, OpenAI, WordPress) die notwendigen Zugangsdaten und ausreichende Zugriffsrechte besitzt.  
- **Fehlerbehandlung:**  
  Implementiere in deinem Szenario Module zur Fehlererkennung und -behandlung (z. B. was passiert, wenn keine Suchergebnisse vorliegen oder die Textgenerierung fehlschlägt).  
- **Testphase:**  
  Teste jeden Schritt einzeln, um sicherzustellen, dass die Daten korrekt abgerufen, verarbeitet und veröffentlicht werden.

---

Mit dieser Vorgehensweise hast du einen Agenten in Make konfiguriert, der das Internet nach Inhalten zum Thema „Chat Gpd“ durchsucht, die Informationen zu einem Blogartikel aggregiert (ggf. mithilfe eines Textgenerators) und diesen Artikel automatisch auf deiner WordPress-Seite veröffentlicht.  

Falls du weitere Details zu einzelnen Modulen oder eine konkrete Konfiguration benötigst, stehe ich gerne zur Verfügung!
