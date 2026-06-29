---
title: "Unraid Server Installation Guide"
type: chatgpt_conversation
source: chatgpt
source_id: "680fe35c-7224-8007-aca5-6b86edf59431"
created: 2025-04-28
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
  - verein
---


# Unraid Server Installation Guide

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `680fe35c-7224-8007-aca5-6b86edf59431`
- Nachrichten: 10

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Ich möchte einen Unraid Server installieren mit 1 ssd und 4 nas hdd. Erstelle mir ein detaillierte Installationsanleitung inklusive Konfiguration

### 2. Assistent

iturn0image0turn0image1turn0image4turn0image6Hier ist eine detaillierte Schritt-für-Schritt-Anleitung zur Installation und Konfiguration eines Unraid-Servers mit 1 SSD und 4 NAS-HDDs, ideal für den Einsatz als Heimserver oder NAS-System:

---

## 🧰 Voraussetzungen

- **Hardware**:
  - 1x SSD (z. B. 500 GB oder größer) für den Cache
  - 4x NAS-HDDs (z. B. 4–18 TB) für das Datenarray
  - Optional: 1x zusätzliche HDD für die Parität (empfohlen)
  - USB-Stick (8–32 GB, USB 2.0 empfohlen für Stabilität)
  - Internetzugang für die Lizenzaktivierung

- **Software**:
  - [Unraid USB Creator Tool](https://unraid.net/download)
  - Unraid OS (Testversion oder Lizenz)

---

## 🖥️ Schritt 1: USB-Stick vorbereiten

1. **USB-Stick anschließen**: Verbinde den USB-Stick mit deinem PC.
2. **Unraid OS installieren**:
   - Lade das [Unraid USB Creator Tool](https://unraid.net/download) herunter und starte es.
   - Wähle die gewünschte Unraid-Version aus.
   - Gib einen Servernamen ein (z. B. `tower`).
   - Aktiviere die Option „UEFI boot“ bei modernen Systemen.
   - Klicke auf „Write“ und warte, bis der Vorgang abgeschlossen ist.
3. **USB-Stick sicher entfernen**: Trenne den USB-Stick sicher vom PC.

---

## 🔧 Schritt 2: BIOS konfigurieren & Unraid starten

1. **USB-Stick einstecken**: Stecke den vorbereiteten USB-Stick in den Server.
2. **BIOS aufrufen**: Starte den Server und öffne das BIOS/UEFI.
3. **Boot-Reihenfolge festlegen**:
   - Setze den USB-Stick als primäres Bootmedium.
   - Aktiviere ggf. Virtualisierungsfunktionen wie VT-x/AMD-V und IOMMU.
4. **Änderungen speichern & neu starten**: Speichere die Einstellungen und starte den Server neu.

---

## 🌐 Schritt 3: Unraid WebGUI einrichten

1. **Unraid starten**: Der Server bootet Unraid und zeigt eine IP-Adresse an.
2. **WebGUI aufrufen**:
   - Öffne einen Browser auf einem anderen Gerät im selben Netzwerk.
   - Gib `http://tower.local` oder die angezeigte IP-Adresse ein.
3. **Root-Passwort festlegen**: Vergib ein sicheres Passwort für den Benutzer `root`.
4. **Lizenz aktivieren**:
   - Melde dich mit einem Unraid.net-Konto an oder erstelle eines.
   - Aktiviere die 30-Tage-Testlizenz oder füge eine gekaufte Lizenz hinzu.

---

## 💾 Schritt 4: Laufwerke zuweisen

1. **WebGUI öffnen**: Navigiere zum Tab „Main“.
2. **Paritätslaufwerk zuweisen**:
   - Wähle die größte HDD als Paritätslaufwerk aus.
   - Hinweis: Die Parität schützt vor Datenverlust bei Ausfall einer Festplatte.
3. **Datenlaufwerke zuweisen**:
   - Weise die verbleibenden 3 HDDs als Datenlaufwerke (`Disk 1`, `Disk 2`, `Disk 3`) zu.
4. **Cache-Laufwerk zuweisen**:
   - Weise die SSD als Cache-Laufwerk zu.
   - Vorteil: Schnellere Schreib-/Lesezugriffe für temporäre Daten.
5. **Array starten**:
   - Klicke auf „Start“ unter „Array Operation“.
   - Bestätige ggf. das Formatieren der neuen Laufwerke.

---

## 📁 Schritt 5: Shares & Cache konfigurieren

1. **Shares erstellen**:
   - Navigiere zum Tab „Shares“.
   - Erstelle neue Shares für z. B. `appdata`, `isos`, `backups`, `media`.
2. **Cache-Nutzung festlegen**:
   - Für performancekritische Shares (z. B. `appdata`, `system`):
     - Setze „Use cache pool“ auf „Only“ oder „Prefer“.
   - Für große Mediendateien:
     - Setze „Use cache pool“ auf „No“, um direkt auf die HDDs zu schreiben.
3. **Mover planen**:
   - Der Mover verschiebt Daten vom Cache ins Array.
   - Standardmäßig läuft dieser täglich um 03:40 Uhr.
   - Anpassungen sind unter „Settings“ > „Scheduler“ möglich.

---

## ⚙️ Schritt 6: Docker & VMs einrichten (optional)

1. **Docker aktivieren**:
   - Navigiere zu „Settings“ > „Docker“.
   - Aktiviere den Docker-Dienst und wähle das Verzeichnis (z. B. `/mnt/cache/appdata`).
2. **Community Applications installieren**:
   - Gehe zu „Apps“ und installiere das Plugin „Community Applications“.
   - Ermöglicht einfachen Zugriff auf zahlreiche Docker-Container.
3. **VMs einrichten**:
   - Navigiere zu „Settings“ > „VM Manager“.
   - Aktiviere den VM-Dienst und konfiguriere den Pfad für virtuelle Maschinen.

---

## 🧪 Schritt 7: System testen & überwachen

1. **SMART-Werte prüfen**:
   - Überwache die Gesundheit der Festplatten regelmäßig.
2. **Benachrichtigungen einrichten**:
   - Konfiguriere E-Mail-Benachrichtigungen unter „Settings“ > „Notifications“.
3. **Backup-Strategie planen**:
   - Denke daran: Parität ersetzt kein Backup!
   - Plane regelmäßige Backups auf externe Medien oder in die Cloud.

---

## 🔐 Lizenzmodelle

- **Basic**: $59 – bis zu 6 Geräte
- **Plus**: $89 – bis zu 12 Geräte
- **Pro**: $129 – unbegrenzte Geräte

Weitere Informationen findest du auf der [Unraid-Website](https://unraid.net/pricing).

---

## 📺 Video-Tutorial

Für eine visuelle Anleitung empfehle ich folgendes Video:

videoComplete Guide: Unraid Home Server Installation & Setupturn0search8

---

Wenn du weitere Fragen hast oder Unterstützung bei spezifischen Konfigurationen benötigst, stehe ich gerne zur Verfügung!

### 3. Benutzer

Erstelle mir aus der Anleitung eine Worddatei

### 4. Assistent

Die Word-Datei mit der detaillierten Anleitung zur Installation und Konfiguration des Unraid-Servers wurde erstellt. Du kannst sie hier herunterladen:

[**Unraid_Installation_Anleitung.docx**](sandbox:/mnt/data/Unraid_Installation_Anleitung.docx)

### 5. Benutzer

wie richte ich die share im detail ein inkl. config

### 6. Assistent

Hier ist eine detaillierte Anleitung zur Erstellung und Konfiguration von Shares auf deinem Unraid-Server, inklusive empfohlener Einstellungen und Tipps:

---

## 🚀 Schritt-für-Schritt: Shares auf Unraid einrichten

### 🔹 Schritt 1: Share erstellen
1. Melde dich in der **WebGUI** deines Unraid-Servers an (`http://tower.local` oder IP-Adresse).
2. Navigiere zu **„Shares“** und klicke auf **„Add Share“**.
3. Gib einen Namen für den Share ein, z. B.:
   - `appdata` (für Docker/VM-Daten)
   - `media` (für Filme, Serien, Musik)
   - `isos` (für ISO-Dateien, Betriebssystem-Images)
   - `backup` (für Sicherungen)

---

### 🔹 Schritt 2: Share-Einstellungen (im Detail erklärt)

Für jeden Share kannst du spezifische Einstellungen festlegen. Hier eine empfohlene Konfiguration am Beispiel des Shares `appdata`:

| Einstellung               | Empfehlung                | Erklärung                                       |
|---------------------------|---------------------------|--------------------------------------------------|
| **Name**                  | `appdata`                 | Name des Shares                                  |
| **Comments**              | „Docker- und VM-Daten“    | (Optional) kurze Beschreibung des Shares         |
| **Allocation method**     | High-water                | Optimal zur gleichmäßigen Nutzung der HDDs       |
| **Minimum free space**    | 10GB                      | Reserviert Platz, um Überlauf zu verhindern      |
| **Split level**           | Automatically split any directory | Freie Verteilung der Unterordner auf HDDs    |
| **Included disk(s)**      | All                       | Freie Nutzung aller Festplatten                  |
| **Excluded disk(s)**      | Keine                     | Nutzt standardmäßig alle verfügbaren HDDs        |
| **Use cache pool**        | Prefer / Only             | - **Prefer:** Standard, wenn SSD vorhanden ist (Mover aktiviert).<br>- **Only:** Falls Daten dauerhaft auf Cache-SSD liegen sollen (z. B. appdata).  |
| **Export**                | Yes                       | Share sichtbar im Netzwerk                       |
| **Security**              | Public / Secure / Private | - **Public:** Jeder Zugriff erlaubt<br>- **Secure:** Jeder sieht Dateien, aber Schreiben nur mit Passwort<br>- **Private:** Zugriff nur mit Passwort |
| **SMB User Access**       | Leserechte/Schreibrechte nach Bedarf | Individuelle Rechte, falls benötigt          |

---

### 🔹 Schritt 3: Beispiel-Konfiguration für spezifische Shares

Hier eine empfohlene Grundeinstellung:

| Share-Name | Cache-Einstellung | Export | Security |
|------------|-------------------|--------|----------|
| appdata    | Only/Prefer       | Yes    | Private  |
| system     | Prefer            | Yes    | Private  |
| media      | No                | Yes    | Public   |
| backups    | No                | Yes    | Secure   |
| isos       | No                | Yes    | Public   |

**Erklärung der Cache-Einstellungen:**
- `Only`: Daten ausschließlich auf Cache (SSD) – ideal für Docker-Daten.
- `Prefer`: Vorrangig SSD, aber bei Bedarf auch auf HDD – ideal für VM-Daten.
- `No`: Direktes Schreiben auf das HDD-Array – ideal für große Mediendateien, Backups und ISOs.

---

## 🛠️ Schritt 4: Cache und Mover detailliert konfigurieren

- Der **Cache** verbessert die Geschwindigkeit für häufig genutzte Daten.
- Der **Mover** verschiebt automatisch Daten vom Cache auf das HDD-Array.

1. Öffne die Einstellungen unter **Settings → Scheduler → Mover Settings**:
   - **Mover logging**: optional aktivieren.
   - **Mover schedule**: idealerweise täglich nachts, z. B. um **03:40 Uhr**.

---

## 🔐 Schritt 5: Zugriffsbeschränkung konfigurieren (optional)

Falls du „Private“ oder „Secure“ Shares nutzt:

1. Gehe zu **Users** → **Add User**:
   - Lege neue Benutzer an (z. B. „admin“, „family“).
2. Gehe zum **Shares** → Wähle deinen Share aus:
   - Stelle bei „Security“ auf **Secure** oder **Private** um.
   - Weise die Zugriffsrechte (read-only/read-write) individuell zu.

---

## 🖥️ Schritt 6: Share-Zugriff im Netzwerk

- **Windows**: Zugriff über Explorer via `\\tower\sharename`
- **macOS**: Zugriff via Finder → Gehe zu → `smb://tower/sharename`
- **Linux**: Zugriff via Dateimanager (z. B. Nautilus) → `smb://tower/sharename`

---

## 📝 Beispielkonfiguration (config-Auszug)

Beispielhafte Konfiguration für `appdata` in Unraid (zur Orientierung):

```
Share name: appdata
Comments: Docker- und VM-Daten
Allocation method: High-water
Minimum free space: 10GB
Split level: Automatically split any directory
Included disk(s): All
Excluded disk(s): None
Use cache pool: Only
Export: Yes
Security: Private
User access: admin (Read/Write), user (No access)
```

---

## 🚧 Zusätzliche Tipps

- Nutze „Community Applications“ zur schnellen Installation von Docker-Containern.
- Plane regelmäßige Backups kritischer Shares (insbesondere `appdata`, `system`).

---

## 📺 Ergänzendes Video zur Vertiefung:
- [**Unraid Share Setup Tutorial (Youtube)**](https://www.youtube.com/watch?v=9TTMUKj60K4)

Falls du weitere Unterstützung brauchst oder spezifische Einstellungen anpassen möchtest, lass es mich wissen!

### 7. Benutzer

Docker & VM einrichten detail anleitung

### 8. Assistent

Hier findest du eine detaillierte Schritt-für-Schritt-Anleitung, um **Docker und virtuelle Maschinen (VMs)** auf deinem Unraid-Server einzurichten und optimal zu konfigurieren:

---

## 🚀 Docker auf Unraid einrichten (im Detail)

Docker erlaubt die einfache Verwaltung von Anwendungen durch Container.

### 🔹 Schritt 1: Docker aktivieren

1. Öffne die **Unraid WebGUI**.
2. Gehe zu **Settings → Docker**.
3. Stelle den Status auf **Enabled**.
4. Konfiguriere die folgenden Einstellungen:
   - **Docker vDisk location:**  
     Empfehlung:  
     ```
     /mnt/cache/appdata/docker.img
     ```
     (liegt idealerweise auf deiner SSD für Performance)
   - **Default appdata storage:**  
     Empfehlung:  
     ```
     /mnt/user/appdata/
     ```
   - **Docker image size:**  
     Standard: 20GB (25–50GB empfohlen, falls viele Container)
5. Klicke auf **Apply**.

---

### 🔹 Schritt 2: „Community Applications“ Plugin installieren

1. Öffne den Tab **Apps**.
   - Wenn „Apps“ nicht sichtbar ist:
     - Gehe zu **Plugins → Install Plugin**.
     - Füge diese URL ein:
       ```
       https://raw.githubusercontent.com/Squidly271/community.applications/master/plugins/community.applications.plg
       ```
   - Bestätige mit **Install**.
2. Der Tab **„Apps“** erscheint nun automatisch.

---

### 🔹 Schritt 3: Docker-Anwendungen installieren

1. Öffne **Apps** → suche nach gewünschtem Docker-Container (z. B. „Plex“, „Nextcloud“).
2. Klicke auf den Container und wähle **Install**.
3. Passe Container-Einstellungen an (z. B. Pfade, Ports):
   - Beispiel Plex:
     - **Host Path 1:** `/mnt/user/media` → Container-Pfad `/media`
     - **Host Path 2:** `/mnt/user/appdata/plex` → Container-Pfad `/config`
4. Bestätige mit **Apply**.
5. Container startet automatisch; Zugriff über angegebene URL.

---

### 🔹 Docker: Best-Practices

- **Appdata immer auf Cache-SSD speichern** (optimaler I/O-Durchsatz).
- Regelmäßige **Backups der appdata** machen (z. B. Plugin: „CA Backup / Restore Appdata“).

---

## 🚀 Virtuelle Maschinen (VMs) einrichten (im Detail)

VMs erlauben die Nutzung kompletter Betriebssysteme (Windows, Linux, macOS).

### 🔹 Schritt 1: VM Manager aktivieren

1. Öffne die **Unraid WebGUI**.
2. Gehe zu **Settings → VM Manager**.
3. Stelle den Status auf **Enabled**.
4. Empfohlene Konfiguration:
   - **Libvirt storage location:**  
     ```
     /mnt/cache/system/libvirt.img
     ```
   - **Default VM storage path:**  
     ```
     /mnt/user/domains/
     ```
   - **VirtIO drivers ISO:**  
     (automatischer Download bei Aktivierung, empfohlen)

5. Klicke auf **Apply**.

---

### 🔹 Schritt 2: VM erstellen

1. Navigiere zum Tab **VMs → Add VM**.
2. Wähle das gewünschte Betriebssystem (z. B. Windows 11, Ubuntu, Debian).

Beispielkonfiguration für Windows 11:

- **Name:** z. B. `Windows11`
- **CPU:** z. B. 4 Kerne zuweisen (je nach Serverleistung)
- **RAM:** 4–8 GB+
- **Maschinentyp:** Q35 (empfohlen für Windows)
- **BIOS:** OVMF (UEFI empfohlen)
- **vDisk size:** z. B. 100 GB
- **vDisk location:**  
  ```
  /mnt/user/domains/Windows11/vdisk1.img
  ```
- **vDisk Bus:** VirtIO (beste Performance)
- **Grafikkarte:** VNC (für Remote-Zugriff) oder GPU-Passthrough (falls GPU vorhanden)
- **Netzwerk:** br0 für Bridge (direkter Netzwerkzugriff)

3. OS-ISO auswählen:
   - ISO-Dateien vorher auf Share `isos` hochladen (z. B. `/mnt/user/isos/`).
   - Wähle ISO aus Dropdown aus.
   - Für Windows: „VirtIO drivers ISO“ zusätzlich mounten.
4. Speichern mit **Create**.
5. VM startet und OS-Installation durchführen.

---

### 🔹 Schritt 3: Treiberinstallation (Windows-VM)

- Während der Windows-Installation:
  - VirtIO Treiber (Netzwerk, Festplatte etc.) aus ISO einbinden.
  - Pfad: `E:\viostor\w11\amd64\` (VirtIO-Treiberverzeichnis).
- Nach Installation: Restliche VirtIO-Treiber installieren (Balloon-Treiber für RAM-Optimierung, Ethernet, etc.).

---

## 🔹 VM: Zusätzliche Tipps (Performanceoptimierung)

- Aktiviere „CPU-Pinning“ (feste CPU-Zuweisung).
- Nutze „Hugepages“ zur Verbesserung der Performance:
  - Unter **Settings → VM Manager** → „Hugepages“ auf z. B. 2048 setzen.
- GPU-Passthrough:
  - Prüfe BIOS-Einstellungen für IOMMU.
  - Stelle sicher, dass GPU nicht gleichzeitig von Unraid genutzt wird.

---

## 🔹 Zugriff auf deine VMs

- **VNC-Zugriff**: Direkt über Unraid-WebGUI oder mit VNC-Client (z. B. RealVNC).
- **Remote Desktop (Windows)** aktivieren und nutzen:
  - Einstellungen → System → Remote Desktop aktivieren.
  - Zugriff per RDP (Remotedesktopverbindung) von anderen PCs im Netzwerk.

---

## 📝 Beispielhafte Docker-Config (Plex-Container)

```
docker run -d \
--name='plex' \
--net='host' \
-e TZ="Europe/Berlin" \
-e HOST_OS="Unraid" \
-v '/mnt/user/appdata/plex':'/config':'rw' \
-v '/mnt/user/media':'/media':'ro' \
'plexinc/pms-docker:latest'
```

---

## 📝 Beispielhafte VM-Config (Libvirt XML)

Automatisch generiert (vereinfachtes Beispiel):

```xml
<domain type='kvm'>
  <name>Windows11</name>
  <memory unit='KiB'>8388608</memory>
  <vcpu placement='static'>4</vcpu>
  <os>
    <type arch='x86_64' machine='pc-q35-8.2'>hvm</type>
  </os>
  <devices>
    <disk type='file' device='disk'>
      <source file='/mnt/user/domains/Windows11/vdisk1.img'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <interface type='bridge'>
      <source bridge='br0'/>
    </interface>
  </devices>
</domain>
```

---

### 📺 Hilfreiches Video:

- [Docker-Einrichtung auf Unraid (Youtube)](https://youtu.be/T8cH3W0m3lc)
- [VM-Einrichtung auf Unraid (Youtube)](https://youtu.be/GrIT-pj-zpA)

---

Falls du zusätzliche Fragen oder individuelle Unterstützung benötigst, melde dich gerne!

### 9. Benutzer

wie komme ich auf die konsole des paperless-ngx-containers

### 10. Assistent

Um auf die Konsole (Shell) eines Docker-Containers wie z.B. **Paperless-ngx** in deinem Unraid-System zuzugreifen, kannst du folgenden Weg nutzen:

---

## 🖥️ Zugriff auf die Container-Konsole via Unraid-WebGUI:

1. **Öffne Unraid-WebGUI:**
   - Gehe auf `http://tower.local` oder deine IP-Adresse.

2. **Navigiere zum Docker-Tab:**
   - Klicke oben auf **Docker**.

3. **Paperless-ngx-Container auswählen:**
   - Suche den Container „**paperless-ngx**“ in der Liste.

4. **Container-Konsole öffnen:**
   - Klicke auf das Container-Icon oder den Containernamen.
   - Wähle aus dem Kontextmenü **"Console" → "bash" oder "sh"**.

---

## 🛠️ Alternativer Zugriff per SSH (Terminal):

Falls du per Terminal (z. B. SSH) auf deinen Unraid-Server verbunden bist, geht es so:

```bash
docker exec -it paperless-ngx bash
```

**Falls `bash` nicht verfügbar ist, nutze:**

```bash
docker exec -it paperless-ngx sh
```

**Erklärung:**
- `docker exec` führt einen Befehl in einem laufenden Container aus.
- `-it` öffnet eine interaktive Shell.
- `paperless-ngx` ist der Containername (ersetze ggf. durch exakten Namen).

---

## 📌 Hinweise:

- Achte darauf, dass dein Container läuft, bevor du auf die Konsole zugreifst.
- Du kannst mit dem Befeck `exit` die Container-Konsole verlassen.

---

Falls du weitere Fragen hast, melde dich gerne!
