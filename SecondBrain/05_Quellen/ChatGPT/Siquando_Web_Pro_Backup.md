---
title: "Siquando Web Pro Backup"
type: chatgpt_conversation
source: chatgpt
source_id: "6878e72b-029c-8007-b1de-263499119dea"
created: 2025-07-17
tags:
  - chatgpt
  - import
  - projekt
---


# Siquando Web Pro Backup

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6878e72b-029c-8007-b1de-263499119dea`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Siquando Web pro 9 Projekt Backup erstellen

### 2. Assistent

Um ein vollständiges Backup eines **Siquando Web Pro 9** Projekts zu erstellen, sind **drei Komponenten** relevant:

---

### ✅ 1. **Projektdateien sichern (lokal auf dem PC)**
Siquando Web Pro speichert Projekte in der Regel **lokal auf deinem PC**, nicht in der Cloud. Standardmäßig liegt das Projekt unter folgendem Pfad:

```
C:\Users\<DeinName>\Documents\SIQUANDO\Web Pro 9\Projects\
```

#### Vorgehensweise:
1. Öffne den Windows Explorer.
2. Navigiere zu:  
   `C:\Users\<DeinBenutzername>\Documents\SIQUANDO\Web Pro 9\Projects\`
3. Kopiere den gesamten Ordner deines Projekts (z. B. `MeineWebsite`) auf ein Backupmedium:
   - externe Festplatte  
   - USB-Stick  
   - NAS oder Cloud-Speicher

---

### ✅ 2. **Datenbank sichern (falls du MySQL nutzt)**
Falls du in Siquando **MySQL als Datenbanktyp** verwendest (z. B. bei Blog, Shop, Gästebuch), musst du zusätzlich die Datenbank sichern.

#### So geht’s mit phpMyAdmin:
1. Melde dich bei deinem Webhoster (z. B. IONOS, STRATO) an.
2. Öffne **phpMyAdmin**.
3. Wähle deine Datenbank aus.
4. Klicke auf **Exportieren** → Format: **SQL** → Start.

Ergebnis: Du erhältst eine `.sql`-Datei, die du zusammen mit deinem Projekt sichern solltest.

---

### ✅ 3. **Online-Daten (FTP-Webspace) sichern (optional)**
Auch die auf dem Server befindlichen Webdateien kannst du sichern:

#### So geht's:
1. Mit **FileZilla** oder einem anderen FTP-Client verbinden.
2. Alle Dateien auf dem Webspace herunterladen:
   - vor allem wichtig, wenn du manuelle Änderungen per FTP vorgenommen hast.

---

### ✅ Empfehlung zur Backup-Frequenz:
- Bei **jeder größeren Änderung** am Projekt.
- Vor **Updates** der Software.
- Regelmäßig z. B. **monatlich**, wenn die Website aktiv gepflegt wird.

---

### ✅ Optional: Alles als ZIP archivieren
Um dein Backup später einfacher zu verwalten:
- Lege Projektordner, SQL-Datei und ggf. Webdateien in einen Ordner.
- Erstelle ein ZIP-Archiv davon.

---

Wenn du möchtest, kann ich dir eine **Checkliste als Word- oder PDF-Datei** für deine Backups erstellen. Sag einfach Bescheid.
