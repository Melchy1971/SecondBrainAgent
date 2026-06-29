---
title: "n8n lokal starten"
type: chatgpt_conversation
source: chatgpt
source_id: "680b3aca-b41c-8007-82e0-d8ad6821b03b"
created: 2025-04-25
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
---


# n8n lokal starten

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `680b3aca-b41c-8007-82e0-d8ad6821b03b`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

n8n local starten

### 2. Assistent

Um n8n lokal zu starten, kannst du den folgenden Befehl verwenden, wenn du n8n über npm installiert hast:

```bash
n8n start
```

Stelle sicher, dass du dich im richtigen Verzeichnis befindest, das dein n8n-Projekt enthält. Dieser Befehl startet den n8n-Server lokal, und du kannst dann über deinen Webbrowser auf die Benutzeroberfläche zugreifen, normalerweise unter `http://localhost:5678`.

Wenn du n8n über Docker installiert hast, lautet der Befehl zum Starten:

```bash
docker run -it --rm \
    --name n8n \
    -p 5678:5678 \
    n8nio/n8n
```

Dieser Befehl startet n8n ebenfalls lokal über Docker und stellt sicher, dass der Webserver auf Port 5678 verfügbar ist.

### 3. Benutzer

N8n inunraid docker installieren

### 4. Assistent

Um n8n in Docker auf Unraid zu installieren, folge diesen Schritten:

### 1. **Docker-Container in Unraid einrichten:**

1. **Öffne das Unraid Webinterface:**
   - Melde dich in deinem Unraid-Dashboard an.

2. **Gehe zu "Docker"**:
   - Navigiere im Unraid-Dashboard zu „Docker“ (im oberen Menü).
   
3. **Container hinzufügen:**
   - Klicke auf „Add Container“ oder „Container hinzufügen“.

4. **Docker-Image für n8n konfigurieren:**
   - Gib den Namen des Containers ein (z. B. `n8n`).
   - Setze das Image auf `n8nio/n8n` (dies ist das offizielle n8n Docker-Image).
   - Wähle die Version des Images, wenn du eine bestimmte benötigst (meistens ist die neueste Version sinnvoll).

### 2. **Ports und Volumes konfigurieren:**

1. **Ports:**
   - Klicke auf „Add another Port“ und füge den folgenden Port hinzu:
     - `5678` (Dies ist der Standardport für die n8n-Weboberfläche).
   - Wähle sowohl den „Host-Port“ als auch den „Container-Port“ als `5678`, damit du über deinen Webbrowser darauf zugreifen kannst.
  
2. **Volumes:**
   - Um deine n8n-Daten persistent zu speichern (z. B. Workflows, Logs):
     - Füge ein Volume hinzu, das auf einen Speicherort auf deinem Unraid-Server verweist (z. B. `/mnt/user/appdata/n8n`).
     - Mappe diesen Ordner auf den Containerpfad `/root/.n8n`.

### 3. **Umgebungsvariablen einrichten:**
   Du kannst Umgebungsvariablen setzen, um n8n anzupassen. Einige nützliche Optionen:

   - `N8N_BASIC_AUTH_ACTIVE=true` – Aktiviert die Basis-Authentifizierung.
   - `N8N_BASIC_AUTH_USER=<username>` – Setzt den Benutzernamen für die Authentifizierung.
   - `N8N_BASIC_AUTH_PASSWORD=<password>` – Setzt das Passwort für die Authentifizierung.
   - `EXECUTION_TIMEOUT=<value>` – Setzt das Timeout für die Ausführung (z. B. `60000` für 60 Sekunden).

   Diese Variablen kannst du im Docker-Container unter "Environment Variables" hinzufügen.

### 4. **Container starten:**
   - Klicke auf "Apply", um den Container zu erstellen und zu starten.
   - Der n8n-Container sollte jetzt laufen und über `http://<deine_unraid_ip>:5678` erreichbar sein.

### 5. **Zugriff auf n8n:**
   - Öffne deinen Webbrowser und gehe zu `http://<deine_unraid_ip>:5678`.
   - Du solltest nun die n8n-Weboberfläche sehen und kannst mit Workflows und Automatisierungen beginnen.

Das war’s! Dein n8n-Container läuft nun auf Unraid, und du kannst ihn über die Weboberfläche steuern.
