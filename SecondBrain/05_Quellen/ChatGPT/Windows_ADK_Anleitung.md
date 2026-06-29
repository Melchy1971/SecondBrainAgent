---
title: "Windows ADK Anleitung"
type: chatgpt_conversation
source: chatgpt
source_id: "688877ee-346c-832a-a7e6-c6a9fc9281a8"
created: 2025-07-29
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# Windows ADK Anleitung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `688877ee-346c-832a-a7e6-c6a9fc9281a8`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Hier ist eine **sachliche, faktenbasierte Anleitung** zur Installation und Nutzung des Windows Assessment and Deployment Kit (ADK) zur Erstellung und Bearbeitung von Antwortdateien (`unattend.xml`) für automatisierte Windows-Installationen. Die Anleitung ist für Windows 10/11 und Windows Server 2016/2019/2022 geeignet.

---

## **1. Was ist das Windows ADK?**

Das **Windows Assessment and Deployment Kit (ADK)** ist ein kostenloses Tool von Microsoft zur Vorbereitung, Automatisierung und Verteilung von Windows-Installationen. Für Antwortdateien wird hauptsächlich das Tool **Windows System Image Manager (WSIM)** genutzt, das im Paket **Windows ADK mit Windows Preinstallation Environment (WinPE)** enthalten ist.

---

## **2. Download und Installation des ADK**

### **2.1 Download**

1. Gehen Sie auf die offizielle Microsoft-Webseite:  
   [https://learn.microsoft.com/de-de/windows-hardware/get-started/adk-install](https://learn.microsoft.com/de-de/windows-hardware/get-started/adk-install)
2. Wählen Sie die zu Ihrem Windows-Betriebssystem passende Version.
3. Laden Sie die folgenden Komponenten herunter:
   - **Windows ADK**
   - **Windows PE Add-ons for ADK**  
     (WinPE ist seit Windows 10 Version 1809 ein separates Add-on)

### **2.2 Installation**

1. **ADK installieren**:
   - Führen Sie die heruntergeladene Datei (`adksetup.exe`) aus.
   - Wählen Sie als Installationsoption „Auf diesem Computer installieren“.
   - Wichtig: Aktivieren Sie **Deployment Tools** (dies beinhaltet den Windows System Image Manager).
   - Weitere Komponenten wie „User State Migration Tool (USMT)“ können optional installiert werden.

2. **WinPE-Add-on installieren**:
   - Nach Installation des ADK starten Sie die Setup-Datei des WinPE-Add-ons.
   - Bestätigen Sie den Speicherort (Standard reicht aus).
   - Optional: Sie können später WinPE-Images damit erstellen, für Antwortdateien ist dies aber **nicht zwingend nötig**.

---

## **3. Erstellen einer Antwortdatei mit dem Windows System Image Manager (WSIM)**

### **3.1 Vorbereitung**

- Sie benötigen ein **Windows-Installationsabbild** (`install.wim`) aus einer ISO-Datei (z.B. von Windows 10/11 oder Server).
  - Die Datei finden Sie auf einem Installationsmedium im Ordner `sources\install.wim`.

### **3.2 Start des WSIM**

1. Starten Sie den **Windows System Image Manager**:
   - Startmenü > „Windows Kits“ > „Windows System Image Manager“

2. **Image einbinden**:
   - Menü: **Datei → Windows-Abbild auswählen**
   - Navigieren Sie zur `install.wim`-Datei und wählen Sie das gewünschte Image (z.B. Windows 10 Pro).
   - Beim ersten Laden wird die Erstellung einer Katalogdatei (`.clg`) verlangt; bestätigen Sie dies.

3. **Neue Antwortdatei erstellen**:
   - Menü: **Datei → Neue Antwortdatei**

4. **Komponenten einfügen**:
   - Rechtsklick auf die gewünschte Konfigurationsebene (z.B. `windowsPE`, `offlineServicing`, `specialize`, `oobeSystem`).
   - Mit „Komponente einfügen“ die gewünschten Einstellungen (ProductKey, User, Computername, Sprache, Partitionierung, Autologin etc.) hinzufügen.

5. **Antwortdatei anpassen**:
   - Im unteren Bereich die Felder wie gewünscht ausfüllen.
   - Typische Einstellungen:
     - Sprache und Gebietsschema (`InputLocale`, `SystemLocale`, `UILanguage`)
     - Computername
     - Domänenbeitritt
     - Benutzerkonto, Kennwort
     - Lizenzschlüssel
     - Partitionierung und Formatierung

6. **Validierung**:
   - Menü: **Tools → Antwortdatei validieren**
   - Fehler und Warnungen werden angezeigt.

7. **Speichern**:
   - Menü: **Datei → Antwortdatei speichern unter**
   - Speichern Sie als **`unattend.xml`**.

---

## **4. Verwendung der Antwortdatei**

- Kopieren Sie die **unattend.xml** auf das Installationsmedium oder legen Sie sie z.B. im Verzeichnis `C:\` ab.
- Bei automatisierter Installation über WDS/WAIK oder andere Deployment-Tools wird die Antwortdatei automatisch eingelesen.
- Bei manueller Installation kann die Datei mit dem Setup-Parameter `/unattend:<Pfad_zur_unattend.xml>` angegeben werden.

---

## **5. Wichtige Hinweise**

- Die Antwortdatei muss **zum verwendeten Windows-Image passen** (z.B. Home/Pro/Enterprise).
- Bei Fehlern hilft meist die Validierung in WSIM oder ein Vergleich mit Beispielantwortdateien.
- **Sicherheitskritische Informationen** (wie Passwörter im Klartext) sollten mit Bedacht behandelt werden.

---

### **Praxis-Tipp**

- Es gibt viele Beispiel-`unattend.xml`-Dateien in der Microsoft-Dokumentation:
  [https://learn.microsoft.com/de-de/windows-hardware/customize/desktop/unattend/microsoft-windows-setup](https://learn.microsoft.com/de-de/windows-hardware/customize/desktop/unattend/microsoft-windows-setup)

---

**Wenn Sie eine konkrete Antwortdatei benötigen, geben Sie bitte Ihre Anforderungen an (Edition, Sprache, Domain, User, Autologin etc.).**  
Falls Sie die Anleitung als Word- oder PDF-Datei benötigen, bitte angeben – ich kann diese sofort exportieren.

**Transparenzhinweis:**  
Sollten im Einzelfall Kompatibilitätsprobleme auftreten (z.B. neuere Windows-Version, exotische Images), bitte explizit anfragen, da Details sich ändern können.

### 2. Benutzer

anleitung Windows Assessment and Deployment Kit (ADK) für Antwortdateien
