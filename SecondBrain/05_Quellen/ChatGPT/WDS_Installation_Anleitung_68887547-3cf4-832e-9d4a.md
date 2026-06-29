---
title: "WDS Installation Anleitung"
type: chatgpt_conversation
source: chatgpt
source_id: "68887547-3cf4-832e-9d4a-54a995570bba"
created: 2025-07-29
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# WDS Installation Anleitung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68887547-3cf4-832e-9d4a-54a995570bba`
- Nachrichten: 13

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Hier eine sachliche, vollständige und an aktuellen Standards orientierte Anleitung zum Einrichten eines Windows-Installationsservers (WDS) auf Basis von **Windows Server 2016 Essentials**. Beachte, dass Essentials im Vergleich zu Standard und Datacenter einige Einschränkungen hat (z.B. kein AD DS-Betrieb als Host von Domänencontroller neben anderen Rollen). Der Betrieb von WDS ist aber **grundsätzlich möglich**.

---

# Anleitung: Windows-Installationsserver (WDS) auf Windows Server 2016 Essentials

## **1. Voraussetzungen prüfen**

- Mindestens 1 Netzwerkkarte (für PXE-Clients erreichbar)
- Statische IP-Adresse für den Server
- Ausreichend Speicherplatz für die Images (min. 20 GB empfohlen)
- Administrative Berechtigungen auf dem Server
- Optional: DHCP-Server (kann auf dem gleichen Server laufen, aber ist im Netzwerk zwingend erforderlich)
- **Wichtig:** Essentials ist auf 25 Benutzer/50 Geräte limitiert.

---

## **2. WDS-Rolle installieren**

1. **Server-Manager öffnen**  
   `Start` → `Server-Manager`

2. **Rolle hinzufügen**  
   - Klicke auf **"Verwalten"** → **"Rollen und Features hinzufügen"**
   - Weiter bis zu **"Serverrollen"**
   - **"Windows-Bereitstellungsdienste"** auswählen (Hauptknoten), beide Unterkomponenten (**Bereitstellungsserver** und **Transportserver**) aktivieren
   - Weiter und Installation abschließen

---

## **3. WDS initial konfigurieren**

1. **WDS-Konsole starten**  
   `Start` → `Windows-Bereitstellungsdienste`

2. **Server konfigurieren**  
   - Rechtsklick auf den Servernamen (links im Baum) → **"Server konfigurieren"**
   - Assistent durchlaufen:
     - **Integrierte AD-Umgebung:** *Essentials kann als DC laufen – falls vorhanden, AD nutzen. Sonst im Standalone-Modus.*
     - **Verzeichnis für Remoteinstallationsimages:** z.B. `D:\RemoteInstall`
     - **DHCP-Konfiguration:**  
       - Falls DHCP auf **demselben Server** läuft, **beide Haken setzen** ("DHCP-Optionen nicht anhören" und "DHCP-Option 60 setzen").
       - Falls DHCP **auf einem anderen Server**, keine Optionen anpassen.
     - **Antwortverhalten:** Anfangs auf **"Nur bekannten Clients antworten"** stellen (später ggf. anpassen).

3. Abschluss abwarten

---

## **4. Boot- und Installationsabbilder bereitstellen**

1. **Windows-Installationsmedium einlegen** (ISO mounten oder DVD einlegen)
2. **Boot- und Installationsabbilder hinzufügen:**
   - In der WDS-Konsole unter **"Bootabbilder"** → Rechtsklick → **"Bootabbild hinzufügen"**
     - Datei auswählen:  
       `<Laufwerk>:\sources\boot.wim`
     - Eindeutigen Namen vergeben (z.B. "Windows 10 Boot PE")
   - Unter **"Installationsabbilder"** → Rechtsklick auf "Installationsabbilder" → **"Neuer Abbildgruppe"** → Namen vergeben
     - Rechtsklick auf die Abbildgruppe → **"Installationsabbild hinzufügen"**
     - Datei auswählen:  
       `<Laufwerk>:\sources\install.wim`
     - Gewünschte Edition auswählen

---

## **5. Optional: Unbeaufsichtigte Installation (unattend.xml) einbinden**

- **Unattend.xml** (Antwortdatei) vorbereiten (z.B. mit dem Windows System Image Manager – im Windows ADK enthalten)
- In den Eigenschaften des jeweiligen Images in WDS → Registerkarte **"Unbeaufsichtigte Installation"** → Antwortdatei hochladen  
- Siehe Microsoft-Doku zur [Antwortdatei-Syntax](https://learn.microsoft.com/de-de/windows-hardware/customize/desktop/unattend/)  
- Beispiel-Inhalt für Autologin und Domänenbeitritt siehe [hier](https://docs.microsoft.com/de-de/windows-hardware/customize/desktop/unattend/microsoft-windows-shell-setup-autologon).

---

## **6. PXE-Clients testen**

1. Client-PC per LAN verbinden, im BIOS/PXE-Boot aktivieren
2. Von Netzwerk starten (F12, ESC, o.ä., je nach Hersteller)
3. WDS-Bootmenü erscheint
4. Auswahl des Bootabbilds, Installation beginnt

---

## **7. Wichtige Hinweise**

- **Firewall:** Ggf. eingehende Ports für WDS öffnen (UDP 67, 68, 69, 4011, TCP 135, 137, 138, 139, 445)
- **DHCP:** PXE-Optionen (66/67) auf die WDS-IP und boot\x64\wdsnbp.com setzen, falls WDS und DHCP getrennt laufen.
- **Essentials-Einschränkungen:**  
  Essentials kann nicht als „Member Server“ in einer anderen Domäne arbeiten und ist auf maximal 25 Benutzer/50 Geräte beschränkt.

---

## **Download: Anleitung als DOC**

Möchtest du die komplette Anleitung als **.doc** (Word-Datei)?  
Wenn ja, einfach kurz bestätigen – ich stelle die Datei dann direkt zum Download bereit.

---

**Bei Rückfragen zu unattend.xml, DHCP-Konfiguration oder spezifischen Fehlern bitte konkrete Infos/Fehlermeldungen angeben – dann kann ich gezielt weiterhelfen.**

---

**Transparenz:**  
Solltest du während der Einrichtung auf Einschränkungen stoßen, die speziell Essentials betreffen, bitte die konkrete Fehlermeldung mitteilen.  
Nicht alle Features aus Standard/Datacenter sind in Essentials verfügbar (z.B. erweiterte AD-Funktionen, manche Gruppenrichtlinien).

---

**Soll ich die Anleitung jetzt als Word-Dokument (.docx) exportieren und bereitstellen?**

### 2. Benutzer

Ich besitze ms Server 2016 Essentails und möchte eine Installationsserver aufsetzen. Erstelle mir eine detaillierte Anleitung

### 3. Benutzer

ja

### 4. Assistent

Die Anleitung wurde erstellt und in ein Word-kompatibles Format (strukturierte Dokumentenvorlage) überführt.

**Nächster Schritt:**  
Ich exportiere dir das Dokument jetzt als `.docx`-Datei. Du erhältst im Anschluss einen direkten Download-Link.

Einen Moment bitte… Die Datei wird vorbereitet.

### 5. Benutzer

erstelle ein pdf

### 6. Assistent

Beim ersten Versuch gab es ein Problem mit Sonderzeichen (wie „→“ und „“). Ich bereinige den Text und erstelle das PDF nochmals ohne diese Sonderzeichen. Einen Moment bitte.

### 7. Assistent

Hier ist die Anleitung als PDF-Datei:

[WDS_Server2016Essentials_Anleitung.pdf herunterladen](sandbox:/mnt/data/WDS_Server2016Essentials_Anleitung.pdf)

### 8. Benutzer

erstelle eine word

### 9. Assistent

Hier ist die Anleitung als Word-Datei (.docx):

[WDS_Server2016Essentials_Anleitung.docx herunterladen](sandbox:/mnt/data/WDS_Server2016Essentials_Anleitung.docx)

### 10. Benutzer

unattend.xml

### 11. Assistent

Hier ein Beispiel für eine typische **unattend.xml** zur automatisierten Windows-Installation mit Domänenbeitritt und Autologin. Das Muster ist bewusst auf Windows 10/11 bzw. Server 2016 zugeschnitten. Die Datei sollte im UTF-8-Format gespeichert werden.

---

```xml
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <InputLocale>de-DE</InputLocale>
      <SystemLocale>de-DE</SystemLocale>
      <UILanguage>de-DE</UILanguage>
      <UserLocale>de-DE</UserLocale>
    </component>
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <ImageInstall>
        <OSImage>
          <InstallFrom>
            <MetaData wcm:action="add">
              <Key>/IMAGE/INDEX</Key>
              <Value>1</Value>
            </MetaData>
          </InstallFrom>
          <WillShowUI>OnError</WillShowUI>
        </OSImage>
      </ImageInstall>
      <UserData>
        <ProductKey>
          <WillShowUI>OnError</WillShowUI>
        </ProductKey>
        <AcceptEula>true</AcceptEula>
        <FullName>Administrator</FullName>
        <Organization>Firma</Organization>
      </UserData>
      <DiskConfiguration>
        <Disk wcm:action="add">
          <DiskID>0</DiskID>
          <WillWipeDisk>true</WillWipeDisk>
          <CreatePartitions>
            <CreatePartition wcm:action="add">
              <Order>1</Order>
              <Type>Primary</Type>
              <Size>100000</Size>
            </CreatePartition>
          </CreatePartitions>
        </Disk>
        <WillShowUI>OnError</WillShowUI>
      </DiskConfiguration>
      <PartitionConfiguration>
        <DiskConfiguration>
          <Disk wcm:action="add">
            <DiskID>0</DiskID>
            <WillWipeDisk>true</WillWipeDisk>
          </Disk>
        </DiskConfiguration>
      </PartitionConfiguration>
    </component>
  </settings>
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-International-Core" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <InputLocale>de-DE</InputLocale>
      <SystemLocale>de-DE</SystemLocale>
      <UILanguage>de-DE</UILanguage>
      <UserLocale>de-DE</UserLocale>
    </component>
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <TimeZone>W. Europe Standard Time</TimeZone>
      <RegisteredOrganization>Firma</RegisteredOrganization>
      <RegisteredOwner>Administrator</RegisteredOwner>
      <AutoLogon>
        <Password>
          <Value>DeinPasswort123!</Value>
          <PlainText>true</PlainText>
        </Password>
        <Enabled>true</Enabled>
        <Username>Administrator</Username>
        <LogonCount>1</LogonCount>
      </AutoLogon>
      <FirstLogonCommands>
        <SynchronousCommand wcm:action="add">
          <Order>1</Order>
          <CommandLine>cmd /c echo Installation abgeschlossen</CommandLine>
          <Description>Installation abgeschlossen</Description>
        </SynchronousCommand>
      </FirstLogonCommands>
      <DoNotCleanTaskBar>true</DoNotCleanTaskBar>
      <OEMInformation>
        <Manufacturer>Firma</Manufacturer>
      </OEMInformation>
    </component>
    <component name="Microsoft-Windows-UnattendedJoin" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <Identification>
        <JoinDomain>melchy1971.de</JoinDomain>
        <Credentials>
          <Domain>melchy1971.de</Domain>
          <Username>Diggi</Username>
          <Password>DeinDomänenPasswort!</Password>
        </Credentials>
      </Identification>
    </component>
  </settings>
</unattend>
```

---

**Wichtige Hinweise:**

- Ersetze die Platzhalter für Passwörter unbedingt durch sichere, reale Werte!
- Die Einstellungen `<JoinDomain>`, `<Username>`, `<Password>`, `<RegisteredOrganization>`, etc. anpassen.
- Die Partitionierung (Größe, DiskID) kann auf deine Hardware und Anforderungen angepasst werden.
- Die Datei sollte im Root des Installationsimages oder direkt in WDS beim Image als Antwortdatei eingebunden werden.

**Möchtest du die Datei als `.xml` zum Download?** (Falls ja, stelle ich sie sofort bereit.)

### 12. Benutzer

ja

### 13. Assistent

Hier kannst du die gewünschte Beispiel-unattend.xml direkt herunterladen:

[unattend.xml herunterladen](sandbox:/mnt/data/unattend.xml)

**Wichtige Hinweise:**  
- Bitte vor Einsatz die Werte für Passwörter und ggf. weitere Angaben individuell und sicher anpassen!
- Bei Fragen zu Parametern oder für Anpassungen an deine Umgebung bitte melden.
