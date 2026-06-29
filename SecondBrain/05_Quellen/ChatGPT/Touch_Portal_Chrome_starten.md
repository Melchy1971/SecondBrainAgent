---
title: "Touch Portal Chrome starten"
type: chatgpt_conversation
source: chatgpt
source_id: "688a0faf-1f90-832a-a344-0c226d41abf9"
created: 2025-07-30
tags:
  - chatgpt
  - import
  - sap
---


# Touch Portal Chrome starten

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `688a0faf-1f90-832a-a344-0c226d41abf9`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Um **Google Chrome** über **Touch Portal** zu starten, musst du einen Button mit einer **„Open Application“ (Anwendung starten)**-Aktion einrichten. Hier ist eine **Schritt-für-Schritt-Anleitung**, um Chrome korrekt zu starten:

---

### 🔧 **Voraussetzungen**
- Touch Portal ist installiert und läuft.
- Du kennst den Pfad zur ausführbaren Datei von Google Chrome.

---

### 🪜 Schritt-für-Schritt-Anleitung

#### 1. **Button erstellen**
- Öffne Touch Portal.
- Wähle eine Seite oder erstelle eine neue.
- Klicke auf ein freies Button-Feld.
- Gib dem Button einen Namen, z. B. **„Chrome starten“**.
- Optional: Füge ein Icon hinzu (z. B. Chrome-Logo).

#### 2. **Aktion hinzufügen**
- Klicke auf **„+“** im Bereich **Actions**.
- Wähle:  
  **„System“ → „Open application / file / folder“**

#### 3. **Pfad zu Google Chrome eintragen**

##### Standardpfad bei Windows:
```text
C:\Program Files\Google\Chrome\Application\chrome.exe
```

##### Falls du Windows x86 oder benutzerdefinierte Pfade nutzt, könnte es auch sein:
```text
C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
```

- Füge diesen Pfad im Feld „Application Path“ ein.

#### 4. (Optional) **Website oder Parameter mitgeben**
- Wenn du direkt eine Website öffnen willst:
  
  Beispiel mit Parameterfeld:
  ```text
  https://www.google.de
  ```

---

### ✅ **Testen**
- Klicke auf den Button in Touch Portal.
- Chrome sollte starten (ggf. mit Website).

---

### 🧪 **Troubleshooting**
- **Keine Reaktion?** Prüfe:
  - Ob Touch Portal mit Administratorrechten läuft (bei Systemaktionen empfehlenswert).
  - Ob der Pfad zu Chrome korrekt ist (teste ihn in der Windows-„Ausführen“-Box mit `Win + R`).
- **Fehlermeldung?** Pfad enthält Leerzeichen → Pfad ggf. in Anführungszeichen setzen:
  ```text
  "C:\Program Files\Google\Chrome\Application\chrome.exe"
  ```

---

### 🏁 Optional: Mehrere Chrome-Instanzen oder Inkognito
Falls du Chrome mit Argumenten starten willst (z. B. Inkognito-Modus), verwende:
```text
chrome.exe --incognito https://www.google.com
```
Dann:  
- `Application path`: nur der Pfad zur `chrome.exe`  
- `Arguments`: `--incognito https://www.google.com`

---

Wenn du willst, kann ich dir eine komplette Touch Portal `.tpi`-Button-Datei exportieren oder dir ein Beispiel mit Logo als ZIP bereitstellen. Sag Bescheid.

### 2. Benutzer

wie kann ich in touch portal google chrome starten
