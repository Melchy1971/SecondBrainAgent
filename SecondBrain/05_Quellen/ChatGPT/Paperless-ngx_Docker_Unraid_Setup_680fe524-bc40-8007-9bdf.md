---
title: "Paperless-ngx Docker Unraid Setup"
type: chatgpt_conversation
source: chatgpt
source_id: "680fe524-bc40-8007-9bdf-1b561b402f5e"
created: 2025-04-28
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# Paperless-ngx Docker Unraid Setup

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `680fe524-bc40-8007-9bdf-1b561b402f5e`
- Nachrichten: 8

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Erstelle mir eineinstallations Anleitung inklusive Konfiguration zu Papierless nix als docker on unraid

### 2. Assistent

Hier ist eine detaillierte Anleitung zur Installation und Konfiguration von Paperless-ngx als Docker-Container auf einem Unraid-Server. Diese Anleitung basiert auf bewährten Methoden aus der Unraid-Community und offiziellen Dokumentationen.

---

## 🧰 Voraussetzungen

- Unraid-Server mit installiertem Community Applications Plugin
- Aktiviertes Docker-Subsystem
- Optional: Docker Compose Manager Plugin für erweiterte Docker-Verwaltung

---

## 📁 Schritt 1: Shares und Ordnerstruktur einrichten

1. Navigiere in Unraid zu `Shares` und erstelle einen neuen Share, z. B. `Paperless`.
2. Innerhalb dieses Shares erstelle folgende Unterordner:
   - `consume` – für den automatischen Dokumentenimport
   - `media` – zur Speicherung der Originaldokumente
   - `export` – für Backups und Exporte
   - `data` – für interne Daten wie OCR-Modelle
   - `db` – für die PostgreSQL-Datenbank (optional, falls verwendet)
   - `redis` – für Redis-Daten (optional, falls verwendet)

---

## 🧱 Schritt 2: Redis installieren

1. Öffne den `Apps`-Tab in Unraid.
2. Suche nach „Redis“ und installiere den Container von `jj9987`.
3. Standardkonfiguration ist ausreichend.
4. Notiere die IP-Adresse des Unraid-Servers (z. B. `192.168.1.100`).

---

## 📦 Schritt 3: Paperless-ngx installieren

1. Im `Apps`-Tab suche nach „paperless-ngx“ und installiere den Container von `Selfhosters`.
2. Konfiguriere die Pfade wie folgt:
   - `/mnt/user/Paperless/consume` → `/usr/src/paperless/consume`
   - `/mnt/user/Paperless/media` → `/usr/src/paperless/media`
   - `/mnt/user/Paperless/export` → `/usr/src/paperless/export`
   - `/mnt/user/Paperless/data` → `/usr/src/paperless/data`
   - (Optional) `/mnt/user/Paperless/db` → `/var/lib/postgresql/data`
   - (Optional) `/mnt/user/Paperless/redis` → `/data`
3. Setze folgende Umgebungsvariablen:
   - `PAPERLESS_REDIS=redis://192.168.1.100:6379`
   - `PAPERLESS_OCR_LANGUAGE=deu+eng`
   - `PAPERLESS_TIME_ZONE=Europe/Berlin`
   - `PAPERLESS_ADMIN_USER=admin`
   - `PAPERLESS_ADMIN_PASSWORD=deinPasswort`
   - `USERMAP_UID=99`
   - `USERMAP_GID=100`

---

## 🔑 Schritt 4: Admin-Benutzer erstellen

Falls du `PAPERLESS_ADMIN_USER` und `PAPERLESS_ADMIN_PASSWORD` nicht gesetzt hast:

1. Öffne die Konsole des Paperless-ngx-Containers.
2. Führe folgenden Befehl aus:
   ```bash
   python manage.py createsuperuser
   ```


---

## 🧪 Schritt 5: Testen und Zugriff

1. Starte den Paperless-ngx-Container.
2. Öffne deinen Browser und navigiere zu `http://<Unraid-IP>:8000`.
3. Melde dich mit den Admin-Zugangsdaten an.
4. Lege ein Dokument in den `consume`-Ordner, um den automatischen Import zu testen.

---

## 🧩 Optional: Erweiterte Funktionen

- **Tika & Gotenberg**: Für die Verarbeitung von Office-Dokumenten und E-Mails kannst du zusätzliche Container für Tika und Gotenberg einrichten. Aktiviere diese Funktionen mit den Umgebungsvariablen `PAPERLESS_TIKA_ENABLED=1`, `PAPERLESS_TIKA_ENDPOINT=http://tika:9998` und `PAPERLESS_TIKA_GOTENBERG_ENDPOINT=http://gotenberg:3000`.
- **E-Mail-Import**: Aktiviere `PAPERLESS_ENABLE_MAIL_CONSUMER=1` und konfiguriere die entsprechenden E-Mail-Einstellungen.
- **Backup**: Nutze den `export`-Ordner für regelmäßige Backups. Ein Beispielskript könnte wie folgt aussehen:
   ```bash
   docker exec -t paperless-ngx document_exporter /usr/src/paperless/export
   ```


---

## 🧠 Tipps & Hinweise

- **Pfadkonventionen**: Vermeide die Verwendung von NFS-Shares für den `consume`-Ordner, da `inotify` dort nicht funktioniert. Verwende stattdessen lokale Pfade oder SMB-Shares.
- **Docker Compose**: Für komplexere Setups kannst du den Docker Compose Manager in Unraid verwenden, um mehrere Container wie PostgreSQL, Redis, Tika und Gotenberg gemeinsam zu verwalten.
- **Fehlersuche**: Bei Startproblemen überprüfe die Logs des Containers über die Unraid-Oberfläche oder mit `docker logs paperless-ngx`.

---

## 📚 Weitere Ressourcen

- [Offizielle Paperless-ngx Dokumentation](https://docs.paperless-ngx.com/)
- [Unraid Community Forum – Paperless-ngx Support](https://forums.unraid.net/topic/121075-support-paperless-ngx-docker/)
- [YouTube-Tutorial zur Installation auf Unraid](https://www.youtube.com/watch?v=qfNtIeOeKYU)

---

Wenn du Unterstützung bei der Einrichtung von Tika, Gotenberg oder dem E-Mail-Import benötigst, stehe ich dir gerne zur Verfügung.

### 3. Benutzer

Erstelle eine worddatei aus der Anleitung

### 4. Assistent

Hier kannst du die Word-Datei mit der Installationsanleitung herunterladen:

[Paperless-ngx Unraid Installationsanleitung.docx](sandbox:/mnt/data/Paperless_ngx_Unraid_Anleitung.docx)

### 5. Benutzer

Gotenberg und email Import noch bitte

### 6. Assistent

Hier ist die erweiterte Word-Datei mit zusätzlichen Anleitungen zu Gotenberg und dem E-Mail-Import:

[Erweiterte Paperless-ngx Unraid Installationsanleitung.docx](sandbox:/mnt/data/Paperless_ngx_Unraid_Anleitung_erweitert.docx)

### 7. Benutzer

wie kann ich den superuser einrichten

### 8. Assistent

Den **Superuser** (Administrator-Benutzer) für Paperless-ngx kannst du wie folgt einrichten:

---

### 📌 Methode 1: Über Umgebungsvariablen (einfachste Methode):

Beim Erstellen oder Bearbeiten des Containers setzt du diese Umgebungsvariablen:

- **`PAPERLESS_ADMIN_USER`**: Dein gewünschter Benutzername (z. B. `admin`)
- **`PAPERLESS_ADMIN_PASSWORD`**: Dein gewünschtes Passwort (z. B. `meinPasswort`)

**Beispiel-Konfiguration in Unraid:**
```
PAPERLESS_ADMIN_USER=admin
PAPERLESS_ADMIN_PASSWORD=meinPasswort
```

Nach Container-Start kannst du dich unter `http://<Unraid-IP>:8000` anmelden.

---

### 📌 Methode 2: Über die Konsole im Container (manuell):

1. Gehe in Unraid zu **Docker → Paperless-ngx Container → Konsole öffnen**.

2. Führe dort folgenden Befehl aus:
```bash
python manage.py createsuperuser
```

3. Folge den Aufforderungen in der Konsole:
- Gewünschten Benutzernamen eingeben
- E-Mail (optional, kann leer bleiben)
- Passwort eingeben und bestätigen

Anschließend kannst du dich im Webinterface (`http://<Unraid-IP>:8000`) mit den erstellten Zugangsdaten anmelden.

---

**✅ Empfehlung:**
Nutze Methode 1 (Umgebungsvariablen), da sie einfacher und dauerhaft ist.
