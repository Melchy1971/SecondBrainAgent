---
title: "Regel einrichten in Outlook"
type: chatgpt_conversation
source: chatgpt
source_id: "67efac59-e948-8007-8e67-ff1cacc57ad5"
created: 2025-04-04
tags:
  - chatgpt
  - import
  - ki
---


# Regel einrichten in Outlook

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67efac59-e948-8007-8e67-ff1cacc57ad5`
- Nachrichten: 8

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

wie kann ich in outlook365 neu eine regel einrichten

### 2. Assistent

In **Outlook 365 (Web oder Desktop-App)** kannst du relativ einfach eine neue Regel einrichten, um E-Mails automatisch zu verwalten (z. B. verschieben, weiterleiten, markieren). Hier sind die Schritte für beide Varianten:

---

## ✅ **In der Outlook Web-Version (Outlook on the Web)**

1. Öffne [Outlook im Web](https://outlook.office.com).
2. Klicke oben rechts auf das **Zahnrad-Symbol** (⚙️) → **„Alle Outlook-Einstellungen anzeigen“** ganz unten.
3. Navigiere zu **E-Mail** → **Regeln**.
4. Klicke auf **„Neue Regel hinzufügen“**.
5. Gib der Regel einen Namen.
6. Lege fest:
   - **Bedingung(en)**: z. B. „Von“, „Betreff enthält“, „An mich“, etc.
   - **Aktion(en)**: z. B. „In Ordner verschieben“, „Kennzeichnen“, „Weiterleiten“, etc.
7. Optional: Lege Ausnahmen fest.
8. Aktiviere die Regel mit dem Schalter, und klicke auf **„Speichern“**.

---

## ✅ **In der Outlook Desktop-App (Windows/Mac)**

1. Starte Outlook.
2. Gehe oben auf **„Datei“** > **„Regeln und Benachrichtigungen verwalten“**.
3. Klicke auf **„Neue Regel“**.
4. Wähle eine Vorlage, z. B. **„Nachrichten von einer bestimmten Person in einen Ordner verschieben“**, oder starte mit einer leeren Regel.
5. Folge dem Assistenten:
   - Wähle **Bedingungen** (z. B. Absender, Betreff).
   - Lege die **Aktionen** fest (z. B. verschieben, löschen, kategorisieren).
   - Bestimme **Ausnahmen**.
   - Gib der Regel einen Namen und aktiviere sie.
6. Klicke auf **„Fertig stellen“**.

---

Wenn du magst, sag mir, **was genau du automatisieren möchtest**, dann mache ich dir die passende Regel-Vorlage direkt fertig.

### 3. Benutzer

die regel lässt sich leider nur auf der hotmail adresse einrichten

### 4. Assistent

Ah, das klingt nach einem typischen Szenario in Outlook, wo **Regeln nur für bestimmte Kontotypen** verfügbar sind – vor allem bei Konten wie **@hotmail.com**, **@outlook.com**, **@live.com**, etc., die als **Microsoft Exchange- oder Outlook.com-Konten** geführt werden.

---

## 🔍 Mögliche Gründe, warum die Regel nur bei der Hotmail-Adresse geht:

### 1. **Nur Hotmail ist ein echtes Microsoft-Konto**
Andere Konten (z. B. IMAP, POP wie z. B. GMX, Web.de, eigene Domains) **unterstützen keine serverseitigen Regeln** in Outlook Web oder haben nur eingeschränkten Support in der App.

### 2. **Serverseitige Regeln funktionieren nur bei Microsoft-Accounts**
Bei IMAP- oder POP-Konten laufen Regeln **nur beim geöffneten Outlook** – und manche Regel-Funktionen (wie „verschieben in Ordner X“) funktionieren da eingeschränkt oder gar nicht.

---

## ✅ Mögliche Lösungen:

### 🔁 **Lösung 1: Regel direkt in Outlook-Desktop-App einrichten**
Wenn du z. B. ein GMX-, Web.de- oder IMAP-Konto verwendest:
1. Öffne die Outlook-App.
2. Gehe auf **Datei > Regeln und Benachrichtigungen verwalten**.
3. Lege eine neue Regel für das gewünschte Konto an.
   > Hinweis: Diese Regeln funktionieren nur, solange Outlook läuft (clientseitig), aber du kannst trotzdem viele Automationen machen.

---

### 🌐 **Lösung 2: Nutze die Weboberfläche deines E-Mail-Providers**
Falls du z. B. GMX, Web.de oder ein anderes IMAP-Konto nutzt, schau mal direkt im jeweiligen Webmail-Portal:
- GMX: [E-Mail-Regeln](https://www.gmx.net) → Einstellungen → Filterregeln
- Web.de: → Einstellungen → Filterregeln
- Eigene Domain (z. B. über IONOS, Strato): dort gibt's meist auch Filterregeln

---

Wenn du mir sagst, **welche E-Mail-Adresse du zusätzlich zur Hotmail nutzen willst**, kann ich dir genau sagen, wie und wo du die passende Regel einrichten kannst.

### 5. Benutzer

eine ionos email markus@dickscheit.de diese möchte ich verwenden um eine mail von ai autonauten in den ordner ai zu verschieben

### 6. Assistent

Perfekt, danke für die Info! Du nutzt also **markus@dickscheit.de über IONOS**, und möchtest eingehende Mails z. B. von **„AI Autonauten“** automatisch in den Ordner **„AI“** verschieben. Da es sich bei IONOS-Mail meist um ein **IMAP-Konto** handelt, hängt die Umsetzung davon ab, **wo du die Regel einrichten möchtest**:

---

## 🧭 Möglichkeiten im Überblick:

### ✅ **A) Direkt bei IONOS im Webmail-Postfach (serverseitig – funktioniert immer)**
Das ist der zuverlässigste Weg, weil die Regel direkt auf dem Server ausgeführt wird – auch wenn Outlook oder dein PC nicht läuft.

#### 🔧 So geht's:
1. Logge dich ein unter: [https://mail.ionos.de](https://mail.ionos.de)
2. Oben rechts auf das **Zahnrad (⚙️ Einstellungen)** klicken.
3. Wähle **„Filterregeln“** oder „E-Mail-Filter“.
4. Klicke auf **„Neue Regel“** oder „Neue Filterregel erstellen“.
5. Regel einrichten:
   - **Bedingung**: z. B. *Absender enthält* oder *Betreff enthält* „AI Autonauten“.
   - **Aktion**: *Verschiebe in Ordner* → wähle oder erstelle den Ordner **„AI“**.
6. Speichern.

Fertig! Diese Regel gilt für alle Geräte automatisch.

---

### ✅ **B) In Outlook Desktop (lokal, wenn IONOS per IMAP eingebunden ist)**
Falls du lieber Outlook nutzt:

1. Öffne Outlook.
2. Gehe auf **Datei > Regeln und Benachrichtigungen**.
3. Wähle dein IONOS-Konto aus.
4. Klicke **„Neue Regel…“**
5. Vorlage: **„Nachrichten mit bestimmten Wörtern im Absender verschieben“** oder **„Von einer Person in Ordner verschieben“**
6. Bedingungen:
   - z. B. *Von enthält „AI Autonauten“*
7. Aktion: *In Ordner „AI“ verschieben*
8. Speichern

⚠️ Hinweis: Diese Regel funktioniert **nur**, wenn Outlook geöffnet ist, da IMAP-Regeln lokal ausgeführt werden.

---

## 💡Tipp:
Wenn die Absenderadresse von AI Autonauten eindeutig ist (z. B. `newsletter@autonauten.ai`), nimm **„Von enthält“ oder „Von ist genau“**, das ist zuverlässiger als „Betreff enthält“.

---

Möchtest du, dass ich dir eine beispielhafte Regel-Formulierung für IONOS oder Outlook konkret vorbereite? Sag einfach, welche Variante du nutzen willst (Webmail oder Outlook).

### 7. Benutzer

b

### 8. Assistent

Perfekt! Du willst die Regel also **in Outlook Desktop** für dein **IONOS-E-Mail-Konto (IMAP)** einrichten – hier kommt eine ganz konkrete Schritt-für-Schritt-Anleitung für deinen Fall:

---

## ✅ Ziel:  
E-Mails **von "AI Autonauten"** automatisch in den Ordner **„AI“** verschieben.

---

## 🔧 Schritt-für-Schritt in Outlook Desktop:

1. **Outlook öffnen**

2. Oben auf **„Datei“** klicken  
   → Dann auf **„Regeln und Benachrichtigungen verwalten“**

3. Stelle sicher, dass **das richtige Konto** (markus@dickscheit.de) oben im Dropdown ausgewählt ist.

4. Klicke auf **„Neue Regel…“**

5. Im Regel-Assistenten:
   - Wähle: **„Regel auf von mir empfangene Nachrichten anwenden“**  
     (unter „Regel ohne Vorlage erstellen“)  
   - Klicke auf **„Weiter“**

---

### 🔎 Bedingungen auswählen:

- Setze ein Häkchen bei:  
  **„mit bestimmten Wörtern im Absenderadresse“**

- Unten im Schritt-Text auf **„bestimmten Wörtern“** klicken → Gib z. B. ein:  
  ```
  autonauten
  ai-autonauten
  newsletter@autonauten.ai
  ```  
  (je nachdem, was genau in der Absenderadresse steht)

- Klicke auf **„Hinzufügen“** → **OK** → **Weiter**

---

### 📥 Aktion auswählen:

- Setze Häkchen bei:  
  **„diese in den Ordner Zielordner verschieben“**

- Klicke unten auf **„Zielordner“** → Wähle oder erstelle den Ordner **„AI“** unter deinem IONOS-Konto  
  → **OK**

- Klicke auf **„Weiter“**

---

### 🚫 Ausnahme (optional):

- Falls keine Ausnahme notwendig ist → einfach **„Weiter“**

---

### 🏁 Regelname & Fertigstellung:

- Gib der Regel einen Namen, z. B. **„AI Autonauten verschieben“**
- Haken setzen bei **„Diese Regel jetzt auf bereits im Posteingang vorhandene Nachrichten anwenden“**, falls du willst
- Klicke auf **„Fertig stellen“**, dann **„OK“**

---

### 🔁 Wichtig:
Diese Regel funktioniert **nur, wenn Outlook geöffnet ist**, weil IMAP keine serverseitigen Regeln unterstützt. Aber sie läuft zuverlässig im Hintergrund während Outlook aktiv ist.

---

Willst du noch, dass ich dir eine passende *.rwz*-Datei (Regel-Export) vorbereite, die du direkt importieren kannst?
