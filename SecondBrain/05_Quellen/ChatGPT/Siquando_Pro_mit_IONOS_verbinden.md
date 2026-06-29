---
title: "Siquando Pro mit IONOS verbinden"
type: chatgpt_conversation
source: chatgpt
source_id: "6835f310-bf08-8007-b6a5-193866a3df25"
created: 2025-05-27
tags:
  - chatgpt
  - import
  - projekt
---


# Siquando Pro mit IONOS verbinden

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6835f310-bf08-8007-b6a5-193866a3df25`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Um **Siquando Pro Web 9** mit **IONOS** zu verbinden, musst du mehrere Schritte durchführen – vor allem für die **Verbindung mit der Datenbank** und das **Veröffentlichen deiner Website**. Hier ist eine vollständige Anleitung mit den notwendigen Informationen, die du bei IONOS einrichten musst:

---

## 🔧 1. **MySQL-Datenbank bei IONOS einrichten**

### Schritt-für-Schritt:

1. Melde dich bei IONOS an: [https://www.ionos.de/login](https://www.ionos.de/login)
2. Gehe zu **Hosting > MySQL-Datenbanken**.
3. Klicke auf **neue Datenbank anlegen**.
4. Notiere dir folgende Informationen:
   - ✅ **Datenbankname**
   - ✅ **Datenbank-Benutzername**
   - ✅ **Passwort**
   - ✅ **Datenbank-Host (z. B. db123456789.hosting-data.io)**

---

## 🌐 2. **FTP-Zugang bei IONOS einrichten**

1. Gehe zu **Hosting > FTP-Zugänge**.
2. Lege einen neuen Zugang an, falls noch keiner vorhanden ist.
3. Notiere dir:
   - ✅ **FTP-Server (z. B. home123456.1and1-data.host)**  
   - ✅ **Benutzername**
   - ✅ **Passwort**
   - ✅ **Startverzeichnis (optional: z. B. `/htdocs` oder `/`)**

---

## 🛠️ 3. **Einstellungen in Siquando Pro Web 9**

### Projekt > Publizieren > Webserver konfigurieren:

- **Serveradresse (FTP-Host)**: z. B. `home123456.1and1-data.host`
- **Benutzername / Passwort**: wie im FTP-Zugang festgelegt
- **Verzeichnis**: z. B. `/htdocs` oder dein Zielverzeichnis

---

### Projekt > Einstellungen > Datenbank:

- **Datenbank-Host**: z. B. `db123456789.hosting-data.io`
- **Datenbankname**: aus Schritt 1
- **Benutzername**: aus Schritt 1
- **Passwort**: aus Schritt 1
- **Datenbank-Typ**: MySQL

> ❗ Achte darauf, dass die Verbindung zur Datenbank oft erst nach dem **Veröffentlichen der Seite auf dem Server** funktioniert – insbesondere bei Siquando.

---

## 📂 4. **Veröffentlichen**

1. Klicke auf **Veröffentlichen** in Siquando.
2. Wähle den eingerichteten Server.
3. Veröffentliche dein Projekt.
4. Prüfe online die Verbindung – ggf. wird beim ersten Aufruf ein Installations-Skript ausgeführt.

---

## 🧪 5. **Fehlersuche (falls nötig)**

- **Datenbankfehler**: Überprüfe die Schreibweise von Host, DB-Name, Benutzer, Passwort.
- **FTP-Fehler**: Prüfe ob du im richtigen Verzeichnis bist.
- **Seite lädt nicht**: Warte ggf. 1–2 Minuten, leere den Cache, prüfe ob `.htaccess`-Dateien korrekt sind.

---

Möchtest du eine fertige Beispielkonfiguration (als Screenshot oder Exportdatei) oder eine Checkliste im PDF-Format?

### 2. Benutzer

siquando 9 pro mit ionos verknüpfen. welche informationen muss ich einrichten. inkl. sql datenbank
