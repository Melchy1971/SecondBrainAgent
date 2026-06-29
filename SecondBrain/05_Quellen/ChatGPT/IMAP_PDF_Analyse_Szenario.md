---
title: "IMAP PDF Analyse Szenario"
type: chatgpt_conversation
source: chatgpt
source_id: "67d40259-5e54-8007-86dc-99c6d156186b"
created: 2025-03-14
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# IMAP PDF Analyse Szenario

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67d40259-5e54-8007-86dc-99c6d156186b`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich möchte in Make ein senario erstellen mit welchem ich ein imap konto auslese und alle pdf anlagen mit einem modul analysieren und die pdf in einem bestimmten format und beschriftung in einem ordner auf der festplatte speichern

Please write in German language.

### 2. Assistent

Hier eine detaillierte Schritt-für-Schritt-Anleitung, wie du dieses Szenario in Make erstellst:

### Ziel des Szenarios:
Ein IMAP-E-Mail-Konto regelmäßig abrufen, eingehende E-Mails auf PDF-Anhänge prüfen, diese Anhänge mittels eines Analysemoduls auswerten und anschließend in einem lokalen Ordner speichern. Dabei werden die PDFs gemäß eines bestimmten Formats benannt.

---

## Schritt-für-Schritt Anleitung für das Szenario in Make:

### 1. Modul: **IMAP - E-Mails abrufen**
- Modul: **IMAP** → „Neue E-Mails ansehen“ (Watch Emails)
- Zugangsdaten (Server, Benutzername, Passwort) eingeben.
- Postfach auswählen (meist „INBOX“).
- Wähle ein Intervall (z. B. alle 15 Minuten).

### 2. Modul: **Iterator - Anhänge durchlaufen**
- Modul: **Flow Control → Iterator**
- Als Array verwendest du `Attachments` aus dem vorherigen IMAP-Modul.
- Der Iterator stellt sicher, dass alle Anhänge einzeln verarbeitet werden.

### 3. Modul: **Filter - Nur PDF-Dateien zulassen**
- Erstelle einen Filter zwischen Iterator und nächstem Modul.
- Bedingung:  
  `Dateiname` **endet mit** `.pdf`

### 4. Modul: **PDF Analyse (optional, je nach Anforderung)**
- Falls du ein spezielles Modul zur PDF-Analyse nutzt (z.B. „PDF.co“, „PDFMonkey“, „Cloudmersive PDF“ oder ein eigenes API-Modul):
- Modul hinzufügen und mit dem Iterator-Ausgang verbinden.
- PDF-Datei zur Analyse hochladen (Inhalt aus dem Iterator).
- Ergebnis analysieren oder Metadaten extrahieren, um später die Datei entsprechend benennen zu können.

> **Beispiel:**  
> Analyse der Rechnung, Extraktion von Rechnungsnummer und Datum als Metadaten.

### 5. Modul: **Datei speichern**
- Modul: **Tools → Dateien → Datei speichern**
  - Alternativ: Nutze Module wie Dropbox, Google Drive oder SFTP zur lokalen Speicherung.
- Dateiinhalt: Nutze den binären Dateiinhalt (`Data`) aus dem Iterator-Modul.
- Dateiname: Dynamisch zusammengesetzt, z.B.  
  ```
  Rechnung-{{Rechnungsnummer}}-{{Datum}}.pdf
  ```
  (Nutze hier Ergebnisse des PDF-Analysemoduls für individuelle Benennung.)
- Zielordner auf Festplatte oder Cloud-Speicher festlegen.

---

## Praxis-Beispiel für den Dateinamen:
Falls dein PDF-Analysemodul beispielsweise „Rechnungsnummer“ und „Datum“ extrahiert, könnte der Dateiname so aussehen:

```
{{formatDate(Datum; "YYYY-MM-DD")}}_Rechnung_{{Rechnungsnummer}}.pdf
```

Das ergibt z. B.:
```
2025-03-14_Rechnung_12345.pdf
```

---

## Szenario-Test:
Nach Einrichtung solltest du dein Szenario testen, um sicherzustellen, dass:

- E-Mails korrekt gelesen werden.
- Nur PDF-Anhänge verarbeitet werden.
- PDFs analysiert und korrekt benannt werden.
- Dateien wie gewünscht abgelegt werden.

---

Wenn du Unterstützung bei der Integration eines bestimmten PDF-Analysemoduls brauchst oder noch eine andere Anpassung wünschst, sag gerne Bescheid!

### 3. Benutzer

welches Filtermodul

Please write in German language.

### 4. Assistent

In Make gibt es kein eigenständiges Modul namens „Filter“. Die Filter werden in Make direkt zwischen Modulen eingefügt, indem du auf die Verbindungslinie zwischen zwei Modulen klickst und dort eine Bedingung festlegst.

### Wie du in Make einen Filter einrichtest (Schritt-für-Schritt):

**1. Verbindung zwischen Modulen auswählen**  
- Klicke auf die Verbindungslinie zwischen dem **Iterator-Modul** (Anhänge durchlaufen) und dem nächsten Modul (z.B. PDF-Analyse).

**2. Filter-Bedingung hinzufügen**  
- Klicke auf „Filter hinzufügen“ (oder „Set up a filter“).
- Gib deinem Filter einen Namen, z.B.: `Nur PDF-Dateien`.

**3. Filterbedingung einstellen**  
- Stelle folgende Bedingung ein:
  
  ```
  Attachment file name (Dateiname des Anhangs)
  Operator: Ends with (Endet mit)
  Wert: .pdf
  ```

**Erklärung:**  
Der Filter stellt sicher, dass nur Anhänge, deren Dateiname mit `.pdf` endet, weiterverarbeitet werden.

---

### Ergebnis:  
Der Ablauf im Szenario sieht so aus:

```
IMAP-Modul → Iterator (Anhänge) → [Filter: nur .pdf-Dateien] → PDF-Analysemodul → Datei speichern
```

Anhänge, die keine PDFs sind, werden ignoriert.

---

Sag mir gerne, falls du weitere Details brauchst!
