---
title: "Prompt für lovable.dev"
type: chatgpt_conversation
source: chatgpt
source_id: "6900886e-9a1c-832a-9496-5225cf703dba"
created: 2025-10-28
tags:
  - chatgpt
  - code
  - import
---


# Prompt für lovable.dev

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6900886e-9a1c-832a-9496-5225cf703dba`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Alles klar, Markus. Lass uns den Prompt so bauen, dass **lovable.dev** versteht, was du brauchst: ein Tool, das eine **PDF-Datei einliest** und daraus wahlweise eine **PowerPoint (PPTX)** oder eine **Word-Datei (DOCX)** erzeugt, die du dann **lokal speichern** kannst.  

Hier ein sauber formulierter Prompt, den du direkt einsetzen kannst:  

---

**Prompt für lovable.dev:**  

Erstelle ein Tool mit einer einfachen Benutzeroberfläche, das folgende Funktionen bietet:  

1. Der Benutzer kann eine **PDF-Datei hochladen**.  
2. Das Tool bietet eine Auswahl, ob die PDF in eine **Word-Datei (DOCX)** oder eine **PowerPoint-Datei (PPTX)** umgewandelt werden soll.  
3. Nach der Umwandlung soll die Datei **lokal heruntergeladen und gespeichert** werden können.  
4. Die Konvertierung soll den Inhalt der PDF so gut wie möglich in das Zielformat übertragen (Text, Bilder, Layout).  

Technische Hinweise:  
- Verwende eine geeignete PDF-to-DOCX und PDF-to-PPTX Library (z. B. `pdf2docx` oder `python-pptx`).  
- Stelle sicher, dass die Ausgabe-Dateien direkt als Download angeboten werden.  
- Die Oberfläche sollte minimalistisch sein (Upload-Button, Auswahlfeld für Zielformat, Download-Button).  

---

Damit hätte lovable.dev die nötigen Infos, um das Tool zu generieren.  

Willst du, dass ich dir den Prompt noch so umschreibe, dass er direkt als **genaue Eingabe für den Code-Generator** gedacht ist (also weniger erklärend, mehr als konkrete Anweisung in Entwickler-Sprache)?

### 2. Benutzer

erstelle mir einen prompt für lovable.dev zum erstellen eines tool, welches mir aus einer pdf datei eine Powerpoint oder word datei erstellt welche ich lokal speichern kann
