---
title: "Docker Immich Einrichtung"
type: chatgpt_conversation
source: chatgpt
source_id: "6811ea9e-34ec-8007-9c3a-514850f1b596"
created: 2025-04-30
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
---


# Docker Immich Einrichtung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6811ea9e-34ec-8007-9c3a-514850f1b596`
- Nachrichten: 8

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

wie richte ich den docker immich ein

### 2. Assistent

Hier eine kompakte Schritt-für-Schritt-Anleitung, wie du Immich per Docker Compose (empfohlene Methode) auf einem Unraid-Server einrichtest. Ich orientiere mich am aktuellen Stand der offiziellen Doku (Stand 25 April 2025).

---

### 1 • Voraussetzungen

| Komponente | Mindest­version | Unraid-Hinweis |
|------------|----------------|----------------|
| **Docker Engine** | 24.x | Ist in Unraid bereits integriert |
| **Docker Compose v2** | ≥ 2.24 | Einfachstes Setup: *Compose Manager*-Plugin oder das offizielle **docker-compose_manager** Slack-Plugin installieren |
| **Hardware** | x86-64 oder ARM64 | GPU-Transcoding optional über Compose-Overrides |

---

### 2 • Projekt­verzeichnis anlegen

```bash
mkdir -p /mnt/user/docker/immich
cd /mnt/user/docker/immich
```

*(Nutze einen beliebigen Pfad auf deiner Cache- oder Pool-SSD; die Bibliothek kann natürlich auf dem Array liegen.)*

---

### 3 • Original-Dateien holen

```bash
# aktuelles Compose-File
curl -L https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml -o docker-compose.yml

# Beispiel-Environment
curl -L https://github.com/immich-app/immich/releases/latest/download/.env.example -o .env
```

Die YAML-Datei wird bei jedem Release mitgepflegt; so vermeidest du veraltete Optionen. citeturn0search1

---

### 4 • `.env` anpassen

| Variable | Bedeutung | Beispiel für Unraid |
|----------|-----------|---------------------|
| `UPLOAD_LOCATION` | Ablage der Fotos/Videos | `/mnt/user/photos` |
| `DB_DATA_LOCATION` | PostgreSQL-Daten | `/mnt/cache/appdata/immich/postgres` |
| `TZ` | Zeitzone | `Europe/Berlin` |
| `IMMICH_PORT` | Externer Port | `2283` (Standard) |
| `DB_PASSWORD` u. a. | sichere Passwörter | mit `openssl rand -base64 24` erzeugen |

Alle verfügbaren Variablen findest du in der Immich-Doku. citeturn7search0

---

### 5 • Container starten

```bash
docker compose pull        # Images laden
docker compose up -d       # im Hintergrund starten
```

---

### 6 • Erst­einrichtung im Browser

Rufe `http://<Unraid-IP>:2283` auf. Der **erste registrierte Account wird automatisch Administrator**. citeturn8search3

---

### 7 • Updates einspielen

```bash
docker compose down
docker compose pull
docker compose up -d
```

Dadurch erhältst du die neueste Immich-Version ohne Datenverlust. (Daten liegen persistent in den oben gemounteten Volumes.)

---

### 8 • Optionen & Best Practices  

* **Reverse-Proxy**: Leite Port 2283 nie ungeschützt ins Internet weiter. Nutze z. B. Nginx-Proxy-Manager oder Traefik mit TLS. citeturn8search6  
* **GPU-Transcoding**: Für Intel QuickSync, NVENC etc. gibt es fertige `hwaccel.*.yml`-Overrides im Repo.  
* **Backup**: Sichere sowohl `UPLOAD_LOCATION` als auch `DB_DATA_LOCATION`.  
* **Unraid-Compose-Manager**: Der Plugin-Button „Update Stack“ übernimmt die Befehle aus Schritt 7 für dich. citeturn0search4

---

#### Häufige Stolpersteine

| Problem | Ursache / Lösung |
|---------|------------------|
| **Seite nicht erreichbar** | Prüfe, ob Port 2283 in der YAML wirklich nach außen gemappt wird und keine Firewall blockt. citeturn8search0 |
| **Uploads landen im Container statt auf Share** | `UPLOAD_LOCATION` in der `.env` und die entsprechende Volume-Zeile in `docker-compose.yml` müssen identisch sein. citeturn7search2 |
| **Änderungen in `.env` greifen nicht** | `docker compose up -d --force-recreate` nutzen, damit Compose die Container neu erstellt. citeturn7search0 |

---

### 9 • Nächste Schritte

* Mobile-App koppeln (Android/iOS → Immich App Store)  
* Feintuning der Worker-Jobs (Thumb-Generation, Machine-Learning)  
* Optional: S3- bzw. object-storage-Backend für Medien

---

**Frage an dich:** Hast du den *Compose Manager* auf deinem Unraid schon installiert, oder möchtest du lieber eine klassische Unraid-Docker-Vorlage nutzen? Dann kann ich dir das Setup darauf zuschneiden.

### 3. Benutzer

wie bekomme ich eine Server API Key:

### 4. Assistent

So bekommst du in Immich einen **Server- bzw. Nutzer-API-Key**

1. **Als (Admin-)Benutzer anmelden**  
   – Öffne deine Immich-Weboberfläche im Browser und logge dich mit dem Benutzer ein, für den der Schlüssel gelten soll (für Automationen meist der Admin).  

2. **Zu den API-Schlüsseln navigieren**  
   – Klick oben rechts auf dein Avatar-Bild  
   – **Kontoeinstellungen → API Keys** auswählen. citeturn9search1  

3. **Neuen Schlüssel anlegen**  
   – Button **“New API Key”** anklicken  
   – *Name* vergeben (z. B. “Unraid-Automationen”)  
   – *(Falls deine Version ≥ v1.118)* kannst du hier bereits Scopes einschränken.  

4. **Schlüssel kopieren & sicher ablegen**  
   – Der Key wird **nur einmal** vollständig angezeigt – sofort kopieren!  
   – Hinterlege ihn in einer sicheren Passwort-/Secret-Verwaltung oder in deiner Unraid-`docker-compose.yml` bzw. `.env`, z. B.  
     ```env
     IMMICH_API_KEY=PASTE_YOUR_KEY_HERE
     IMMICH_INSTANCE_URL=https://immich.example.com/api
     ```  

5. **Benutzung in Skripten / CLI / Integrationen**  
   ```bash
   curl -H "x-api-key: $IMMICH_API_KEY" \
        https://immich.example.com/api/server-info
   ```  
   oder im Immich-CLI:  
   ```bash
   immich login-key https://immich.example.com/api $IMMICH_API_KEY
   ``` citeturn7search0turn8search3  

6. **Schlüssel verwalten**  
   – In derselben Liste lassen sich Keys jederzeit **deaktivieren** oder **löschen** (z. B. wenn ein Gerät verloren geht). citeturn0search5  

---

### Häufige Fragen & Tipps  

| Thema | Kurz­antwort |
|-------|-------------|
| **Server- vs. persönlicher Key** | Immich kennt bislang nur benutzergebundene Keys; benutze dafür einfach dein Admin-Konto. Granulare Server-Keys sind laut Roadmap in Arbeit. citeturn8search1 |
| **Sicher speichern** | In Unraid am einfachsten als Umgebungs­variable in `docker-compose.yml` oder über das *Compose-Manager*-Plugin hinterlegen; niemals im Klartext in Skripten committen. |
| **Key verloren?** | Erstelle in den API-Einstellungen einen neuen und lösche den alten Schlüssel. |
| **Fehler 401/“unauthorized”** | Prüfe, ob du wirklich den **x-api-key**-Header mitsendest und der Key zu einem Benutzer gehört, der genügend Rechte hat. citeturn7search1 |

Wenn du den Key für ein konkretes Tool (z. B. Home Assistant, ein Bash-Backup-Skript oder eine TV-App) brauchst, sag Bescheid – dann zeige ich dir das genaue Vorgehen.

### 5. Benutzer

leider kann ich immich ohne key nicht starten wie bekomme ich einen key dafür

### 6. Assistent

**Wichtiges vorweg:**  
Das „Server API Key“, nach dem Immich beim Start meckert, ist **kein** Benutzer-API-Schlüssel aus der Web-Oberfläche. Es handelt sich um _einen oder mehrere geheime Umgebungs­variablen_, die du schon **vor** dem ersten Hochfahren im `.env` hinterlegen musst. Ohne sie bricht der Start mit Meldungen wie

```
Error: Config validation error: "JWT_SECRET" is required
Error: Config validation error: "TYPESENSE_API_KEY" is required
```

ab.

---

## 1 | Welche „Keys“ Immich zum Start braucht

| Variable              | Zweck                                                         | Muss identisch sein in … |
|-----------------------|--------------------------------------------------------------|--------------------------|
| **`JWT_SECRET`**      | signiert alle Login-Tokens                                    | `immich-server`, `immich-microservices`, `immich-machine-learning` |
| **`TYPESENSE_API_KEY`** | sichert die interne Such­engine **Typesense** (ab v1.51) citeturn22search1 | `immich-server`, `typesense` |

*(Weitere Secrets wie `DB_PASSWORD` oder `REDIS_PASSWORD` brauchst du nur, wenn du sie schon in `docker-compose.yml` nutzt.)*

---

## 2 | Starken Schlüssel erzeugen

Auf deinem Unraid-Terminal (oder jedem Linux/Mac/WSL-Prompt):

```bash
# 64-stelligen Hex-String
openssl rand -hex 32

# oder fast rfc-konform base64-String
openssl rand -base64 64 | tr -d '\n'
```

Beispiel-Ausgabe (gekürzt):

```
3aa71b4b97d64f2ee0fede4d0b9a6a02…
```

---

## 3 | `.env` befüllen

```env
# ----- Pfade -----
UPLOAD_LOCATION=/mnt/user/photos
DB_DATA_LOCATION=/mnt/cache/appdata/immich/postgres

# ----- Secrets -----
JWT_SECRET=3aa71b4b97d64f2ee0fede4d0b9a6a02…
TYPESENSE_API_KEY=3aa71b4b97d64f2ee0fede4d0b9a6a02…   # darf derselbe Wert sein
DB_PASSWORD=SicherePostgresParole

# Zeitzone
TZ=Europe/Berlin
```

> **Tipp:** Für Tests genügt es, `JWT_SECRET` und `TYPESENSE_API_KEY` beide auf denselben zufälligen String zu setzen – Hauptsache lang und geheim. citeturn19search2

---

## 4 | Stack neu bauen

```bash
cd /mnt/user/docker/immich          # dort, wo docker-compose.yml liegt
docker compose pull                 # Images aktualisieren (falls nötig)
docker compose up -d --force-recreate
```

Immich sollte jetzt ohne Fehlermeldung starten; die Web-Oberfläche ist unter `http://<host>:2283` erreichbar.

---

## 5 | Erst *danach* Benutzer-API-Keys anlegen

Sobald der Server läuft, meldest du dich an und erstellst pro Benutzer die persönlichen API-Keys (siehe vorige Antwort). Diese haben **nichts** mit den obigen Secrets zu tun und können beliebig oft neu erzeugt oder gelöscht werden.

---

### Häufige Stolpersteine nach dem Start

| Symptom | Ursache / Lösung |
|---------|------------------|
| *Typesense-Container crashed* | `TYPESENSE_API_KEY` fehlt oder in `.env` ≠ Wert im Compose-Abschnitt **typesense**. |
| *“JWT expired” beim Login* | Zeit stimmt im Host nicht. Uhren (NTP) synchronisieren. |
| *Server beendet sich sofort* | `.env` nicht im selben Verzeichnis wie `docker-compose.yml` oder nicht per `env_file:` eingebunden. |

---

**Passt es jetzt?**  
Wenn der Stack immer noch abbricht, poste bitte die **genaue Fehlermeldung aus `docker compose logs immich-server`** – dann finden wir den Haken.

### 7. Benutzer

wie finde ich die .env datei

### 8. Assistent

**Kurz & knapp:**  
Die `.env`-Datei liegt normalerweise im **gleichen Ordner** wie deine `docker-compose.yml`. Auf einem typischen Unraid-Setup findest du sie also unter:

```
/mnt/user/docker/immich/.env
```

---

## Drei Wege, sie zu finden / öffnen

| Methode | Schritte |
|---------|----------|
| **Unraid-Web-GUI** | 1. *Shares* → deinen Cache- oder Pool-Share → `docker/immich` öffnen<br>2. Oben rechts auf **„Versteckte Dateien anzeigen“** klicken (dotfiles werden sonst ausgeblendet). |
| **Terminal / SSH** | ```bash<br># WebTerminal im Unraid-GUI öffnen oder per ssh einloggen<br>cd /mnt/user/docker/immich<br>ls -a        # -a zeigt auch versteckte Dateien<br>```<br>Du solltest `.env` in der Ausgabe sehen. Öffnen z. B. mit `nano .env`. |
| **Compose-Manager-Plugin** | 1. Plugin → Stack „immich“ auswählen → **Edit**<br>2. Tab **Environment / Secrets** → **Open in Editor** – dort wird die aktuell eingelesene `.env` angezeigt. |

---

### Was, wenn keine `.env` da ist?

1. **Prüfen, ob du die Beispiel-Datei geladen hast**  
   ```bash
   ls /mnt/user/docker/immich/.env.example
   ```
2. **Falls vorhanden, kopieren:**
   ```bash
   cp /mnt/user/docker/immich/.env.example /mnt/user/docker/immich/.env
   nano /mnt/user/docker/immich/.env    # Werte anpassen
   ```
3. **Falls nicht vorhanden, neu anlegen:**
   ```bash
   cd /mnt/user/docker/immich
   nano .env            # Datei neu schreiben, speichern (Ctrl-O), schließen (Ctrl-X)
   ```

> **Tipp:** `ls -la | grep env` zeigt dir schnell alle Dateien, deren Name „env“ enthält.

---

### Noch unsicher?

Sag mir einfach, in welchem Pfad deine `docker-compose.yml` liegt oder welche Fehlermeldung du bekommst – dann kann ich dir einen präzisen Befehl für dein Setup nennen.
