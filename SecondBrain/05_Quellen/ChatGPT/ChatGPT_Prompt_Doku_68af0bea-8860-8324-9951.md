---
title: "ChatGPT Prompt Doku"
type: chatgpt_conversation
source: chatgpt
source_id: "68af0bea-8860-8324-9951-d4db6e8be759"
created: 2025-08-27
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# ChatGPT Prompt Doku

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68af0bea-8860-8324-9951-d4db6e8be759`
- Nachrichten: 10

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Openai Chat gpd prompt Doku

### 2. Assistent

Meinst du Doku für „ChatGPT Prompting“ von OpenAI. Hier ist eine kurze, praxistaugliche Übersicht mit Beispielen und Links zur offiziellen Doku.

Ziele von Prompts
• Klare Anweisung geben.  
• Kontext liefern.  
• Gewünschtes Format definieren.  
• Qualität iterativ verbessern. citeturn3view0

Grundregeln
• Verwende das aktuellste Modell.  
• Stelle die Anweisungen an den Anfang. Trenne Anweisungen und Kontext mit """ oder ###.  
• Sei konkret zu Länge, Stil, Output-Format.  
• Zeige das gewünschte Ausgabeformat mit 1 bis 2 Beispielen.  
• Temperatur 0 für faktennahe Aufgaben. Höhere Temperatur für kreativ. citeturn4view0

Minimal-Template für Chat
System
Du definierst Rolle, Ziele, Stil, Grenzen. Kurz und eindeutig.

User
Deine eigentliche Aufgabe mit Kontext und Formatvorgaben.

Beispiel
System:
Du bist ein präziser Assistent. Antworte knapp. Nutze Listen. Keine Füllwörter.

User:
Fasse den Text als 5 Stichpunkte zusammen.
Text:
"""
[Dein Text hier]
"""
Ausgabeformat:
• Punkt 1
• Punkt 2
• Punkt 3
• Punkt 4
• Punkt 5
citeturn4view0

Gute Prompts für Standardaufgaben
• Zusammenfassen
Aufgabe: Fasse den Text in 5 Punkten zusammen. Maximal 80 Wörter gesamt.
Text:
"""
[Text]
"""
Ausgabe:
• …

• Umformulieren
Formuliere den Text in einfachem Deutsch um. Niveau B1. Maximal 120 Wörter.
Text:
"""
[Text]
"""
Ausgabe:
Neuer Text:

• Extraktion
Extrahiere aus dem Text Unternehmen, Personen, Orte. Gib eine JSON-Liste mit Schlüsseln companies, people, locations zurück.
Text:
"""
[Text]
"""
Ausgabe:
{"companies":[], "people":[], "locations":[]}
citeturn4view0

Few-shot statt lange Erklärungen
• Liefere 1 bis 2 Beispiele, wie Eingabe und gewünschte Ausgabe aussehen.  
• Nutze das exakt gleiche Format in deiner Vorgabe und im Ziel. citeturn4view0

Langkontext und Struktur
• Lege Regeln oben und zur Sicherheit am Ende des Prompts ab, wenn der Kontext sehr lang ist.  
• Halte Anweisungen widerspruchsfrei. Spätere Anweisungen überschreiben frühere. citeturn1view0

Agentische Aufgaben und Tools
• Erkläre, ob das Modell Tools verwenden soll, wie und wann.  
• Definiere Persistenz klar, zum Beispiel: „Führe alle Schritte vollständig aus. Beende erst, wenn alle Teilaufgaben erledigt sind.“  
• Beschreibe Stop-Kriterien und welche Aktionen unsicher sind. citeturn2view0

Parameter kurz erklärt
• temperature: 0 für Daten und Fakten. 0.2 bis 0.5 für sachlich kreativ.  
• max_completion_tokens: harte Obergrenze für Antwortlänge.  
• stop: Stop-Sequenzen, um die Ausgabe zu beenden. citeturn4view0

Checkliste vor dem Absenden
• Ist die Hauptaufgabe in 1 Satz klar.  
• Sind Input-Grenzen definiert, zum Beispiel „maximal 800 Wörter“.  
• Ist das Ausgabeformat eindeutig, zum Beispiel „JSON, valide und ohne Kommentare“.  
• Gibt es Beispiele für gewünschte und unerwünschte Ausgaben.  
• Stehen Prüfregeln drin, z. B. „prüfe Daten auf Datum-Format JJJJ-MM-TT“.

Typische Fehler
• Nur sagen, was das Modell nicht tun soll, ohne Alternativen.  
• Vage Vorgaben wie „kurz“ oder „lebhaft“.  
• Fehlende Formatvorgaben bei strukturierten Ausgaben.  
• Widersprüchliche Regeln. citeturn4view0turn1view0

Nützliche offizielle Doku
• Prompt Engineering Best Practices für ChatGPT. Aktualisiert vor 4 Monaten. citeturn3view0  
• Best Practices für Prompt Engineering mit der API. Aktualisiert vor 12 Tagen. citeturn4view0  
• GPT-4.1 Prompting Guide. Stand 14. April 2025. citeturn1view0  
• GPT-5 Prompting Guide. Stand 7. August 2025. citeturn2view0

Wenn du willst, erstelle ich dir jetzt eine schlanke Prompt-Vorlage für dein konkretes Use Case und teste sie mit Beispielinput.

### 3. Benutzer

Ja

### 4. Assistent

Alles klar, dann baue ich dir eine schlanke Prompt-Vorlage, die du universell einsetzen kannst. Sie ist so gestaltet, dass du nur noch Text und gewünschtes Ausgabeformat einsetzen musst.

---

**Prompt-Template für ChatGPT**

```
System:
Du bist ein [Rolle, z. B. „präziser Assistent“, „Marketing-Texter“, „Python-Entwickler“]. 
Halte dich strikt an den Stil: [z. B. „kurze Sätze, Listen, keine Füllwörter“]. 
Ignoriere alles, was dagegen verstößt.

User:
Aufgabe: [klare Anweisung in 1 Satz].  
Kontext:
"""
[Dein Input-Text oder Daten]
"""  
Ausgabeformat:  
[klare Vorgabe, z. B. „Liste mit 5 Punkten“, „valide JSON ohne Kommentare“, „Text in 100 Wörtern“]  

Beispiel:
Input: [Optionales Mini-Beispiel]  
Output: [Wunschformat mit Dummy-Daten]
```

---

**Beispiel 1: Zusammenfassung**

```
System:
Du bist ein präziser Assistent. Antworte in Stichpunkten. Keine Einleitung, keine Erklärungen.

User:
Aufgabe: Fasse den Text in 5 Punkten zusammen. Maximal 80 Wörter.
Kontext:
"""
ChatGPT ist ein KI-gestütztes Sprachmodell von OpenAI. Es wird für Texte, Code, Ideen und vieles mehr genutzt...
"""
Ausgabeformat:
• Punkt 1
• Punkt 2
• Punkt 3
• Punkt 4
• Punkt 5
```

---

**Beispiel 2: JSON-Ausgabe**

```
System:
Du bist ein strenger Datenextraktor. Gib ausschließlich gültiges JSON zurück.

User:
Aufgabe: Extrahiere Personen, Orte und Firmen aus dem Text.
Kontext:
"""
Markus arbeitet bei Siemens in München. Er trifft Anna von BMW.
"""
Ausgabeformat:
{"people":[], "companies":[], "locations":[]}

Beispiel:
Input: "Peter arbeitet bei Bosch in Stuttgart"
Output: {"people":["Peter"], "companies":["Bosch"], "locations":["Stuttgart"]}
```

---

Damit kannst du praktisch jede Aufgabe strukturieren: klare Rolle, klare Aufgabe, Kontext in """-Block, und ein strenges Ausgabeformat.  

Soll ich dir die Vorlage jetzt in eine **deutsche Kurz-Doku** mit ein paar Regeln zum „Baukasten-System“ umbauen, damit du sie als Referenz immer parat hast?

### 5. Benutzer

Ja

### 6. Assistent

Perfekt, hier ist eine kurze, klare **Prompt-Doku auf Deutsch**. Du kannst sie wie einen Baukasten nutzen und schnell anpassen.  

---

## Prompt-Doku (ChatGPT / OpenAI)

### 1. Aufbau eines Prompts
Ein guter Prompt hat drei Teile:  

1. **System**  
   - Rolle festlegen: „Du bist …“  
   - Stil festlegen: z. B. kurze Sätze, Listen, keine Füllwörter.  
   - Grenzen setzen: was ignoriert werden soll.  

2. **User (Aufgabe + Kontext)**  
   - Aufgabe in einem Satz.  
   - Kontext in einem klar abgegrenzten Block `""" … """`.  

3. **Ausgabeformat**  
   - Exaktes Format vorgeben (Liste, JSON, Text mit Länge).  
   - Optional: ein Beispiel mit Dummy-Daten.  

---

### 2. Baukasten-Regeln
- **Klarheit**: Aufgabe in 1 Satz formulieren.  
- **Kontext begrenzen**: nur relevanten Text oder Daten übergeben.  
- **Format streng definieren**: Listenpunkte, JSON, Wörterzahl.  
- **Beispiel nutzen**: 1–2 Mini-Beispiele verbessern die Genauigkeit.  
- **Widersprüche vermeiden**: spätere Regeln überschreiben frühere.  

---

### 3. Beispiel-Prompts

**Zusammenfassung**
```
System:
Du bist ein präziser Assistent. Schreibe kurze Listen. Keine Einleitungen.

User:
Aufgabe: Fasse den Text in 5 Punkten zusammen. Maximal 80 Wörter.
Kontext:
"""
[Dein Text]
"""
Ausgabeformat:
• Punkt 1
• Punkt 2
• Punkt 3
• Punkt 4
• Punkt 5
```

**Umformulieren**
```
System:
Du bist ein Sprachtrainer. Schreibe in einfachem Deutsch, Niveau B1.

User:
Aufgabe: Formuliere den Text einfacher. Maximal 120 Wörter.
Kontext:
"""
[Dein Text]
"""
Ausgabeformat:
Neuer Text:
```

**Datenextraktion (JSON)**
```
System:
Du bist ein Datenextraktor. Gib ausschließlich gültiges JSON zurück.

User:
Aufgabe: Extrahiere Personen, Orte und Firmen aus dem Text.
Kontext:
"""
[Dein Text]
"""
Ausgabeformat:
{"people":[], "companies":[], "locations":[]}

Beispiel:
Input: "Peter arbeitet bei Bosch in Stuttgart"
Output: {"people":["Peter"], "companies":["Bosch"], "locations":["Stuttgart"]}
```

---

### 4. Checkliste vor Absenden
- Ist die Aufgabe in 1 Satz klar?  
- Ist der Kontext sauber begrenzt?  
- Ist das Ausgabeformat eindeutig?  
- Gibt es ein Beispiel für gewünschte Ausgabe?  

---

Willst du, dass ich dir diese Doku als **PDF zum schnellen Nachschlagen** vorbereite?

### 7. Benutzer

Ja

### 8. Assistent

Fertig! Hier ist deine kompakte Prompt-Doku als PDF zum Nachschlagen:  

[Prompt_Doku.pdf herunterladen](sandbox:/mnt/data/Prompt_Doku.pdf)  

Willst du, dass ich dir noch eine **kompakte 1-Seiten-Version** mache, die du als Spickzettel nutzen kannst?

### 9. Benutzer

Ja

### 10. Assistent

Hier ist dein kompakter 1-Seiten-Spickzettel als PDF:  

[Prompt_Spickzettel.pdf herunterladen](sandbox:/mnt/data/Prompt_Spickzettel.pdf)  

Damit hast du eine schnelle Übersicht für den Alltag. Soll ich dir zusätzlich eine **Version für den Handy-Bildschirm** (z. B. schmal im Hochformat) bauen, damit du sie unterwegs nutzen kannst?
