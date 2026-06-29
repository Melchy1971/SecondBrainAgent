---
title: "Installationsserver einrichten WDS"
type: chatgpt_conversation
source: chatgpt
source_id: "6887d997-24c8-8324-8f58-14b0152cc8b6"
created: 2025-07-28
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# Installationsserver einrichten WDS

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6887d997-24c8-8324-8f58-14b0152cc8b6`
- Nachrichten: 9

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Ich besitze ms Server 2016 und möchte eine Installationsserver aufsetzen. Erstelle mir eine detaillierte Anleitung

### 2. Assistent

Gerne, hier findest du eine sachliche und detaillierte Schritt-für-Schritt-Anleitung, wie du unter **Windows Server 2016** einen **Installationsserver** (Windows Deployment Services, WDS) einrichtest, um Windows-Betriebssysteme im Netzwerk bereitzustellen (PXE-Boot/Netzwerkinstallation).

---

## Voraussetzungen

- Windows Server 2016 installiert (möglichst mit allen Updates).
- Statische IP-Adresse für den Server empfohlen.
- Active Directory-Domäne ist nicht zwingend, aber empfohlen (für vollautomatisierte Deployments erforderlich).
- Zugriff auf Installationsmedien (ISO/Datenträger) der zu installierenden Windows-Versionen.
- Optional: Separater DHCP-Server (empfohlen, wenn DHCP nicht auf demselben Server läuft).

---

## 1. Rolle „Windows-Bereitstellungsdienste (WDS)“ installieren

1. **Server-Manager** öffnen.
2. Auf **„Rollen und Features hinzufügen“** klicken.
3. „**Rollenbasierte oder featurebasierte Installation**“ wählen, weiter.
4. Den passenden Server auswählen.
5. Rolle **„Windows-Bereitstellungsdienste“** auswählen.  
   - Unterrollen: „**Bereitstellungsserver**“ und „**Transportserver**“ beide anhaken.
6. Weiterklicken, bis zur Bestätigung, dann **installieren**.
7. Nach Abschluss ggf. **Server neu starten**.

---

## 2. WDS initial konfigurieren

1. **Server-Manager** > **Tools** > **Windows-Bereitstellungsdienste** starten.
2. Im linken Bereich den Server **rechtsklicken** → **Konfigurieren**.
3. **Installationsordner** angeben (z.B. `D:\RemoteInstall`). Standard ist `C:\RemoteInstall`.
4. **Antworten auf Clientanforderungen**:  
   - Für die meisten Umgebungen: „Nur bekannten Clients antworten“ (sicherer), alternativ „Allen Clients antworten“ (einfacher Testbetrieb).
5. Häkchen setzen, falls WDS auch als DHCP-Server fungieren soll.
6. Assistent abschließen.

---

## 3. Boot- und Installationsabbilder hinzufügen

**Boot-Image**: Wird für den PXE-Boot genutzt (i.d.R. die `boot.wim` der Windows-Installations-DVD).

**Installationsimage**: Das eigentliche Windows-Setup (`install.wim` der DVD).

### Schritt-für-Schritt:

1. **Im WDS-Manager** → Rechtsklick auf „**Bootabbilder**“ → „Abbild hinzufügen“.
2. Pfad zu `\sources\boot.wim` auf der Windows-DVD/ISO auswählen.
   - Abbildname sinnvoll benennen (z.B. „Windows 10 PE 64-bit“).
3. Wiederholen für alle benötigten Bootabbilder.
4. Rechtsklick auf „**Installationsabbilder**“ → „Abbildgruppe hinzufügen“ (z.B. „Windows 10“).
5. Rechtsklick auf neue Abbildgruppe → „Abbild hinzufügen“.
6. Pfad zu `\sources\install.wim` auf der DVD/ISO.
   - Auswahl der zu installierenden Editionen (z.B. Pro, Enterprise).
7. Vorgang ggf. mit weiteren Windows-Versionen wiederholen.

---

## 4. DHCP-Konfiguration prüfen

- **DHCP und WDS auf demselben Server**:  
  - WDS-Server → Eigenschaften → Registerkarte **DHCP** → Haken setzen bei  
    „DHCP-Optionen 60, 66, 67 nicht verwenden“.
- **DHCP auf anderem Server**:  
  - Stelle sicher, dass die Optionen 66 (PXE-Serveradresse, IP des WDS-Servers) und 67 (Bootfile Name, z.B. `boot\x64\wdsnbp.com`) im DHCP-Server konfiguriert sind.

---

## 5. PXE-Boot testen

1. Einen Client im gleichen Netzwerk per Netzwerk-Boot (PXE) starten.
2. Überprüfen, ob der PXE-Boot gelingt und das Windows-Installationsmenü erscheint.
3. Installation durchführen.

---

## 6. (Optional) Unbeaufsichtigte Installationen/Automatisierung

- Für automatisierte Installationen kann eine **unattend.xml** (Antwortdatei) genutzt werden.
- Diese kann per WDS integriert oder direkt beim Image hinterlegt werden.
- Für komplexere Szenarien empfiehlt sich das Windows System Image Manager (WSIM), Bestandteil des [Windows ADK](https://docs.microsoft.com/de-de/windows-hardware/get-started/adk-install).

---

## Troubleshooting/Tipps

- Firewall auf dem Server prüfen (Ports UDP 67, 68, 69, 4011).
- WDS-Dienst muss gestartet sein.
- Netzwerk muss Layer-2-Broadcasts für PXE unterstützen (VLAN/Netzwerkstruktur beachten).
- Images sollten von einer **originalen Microsoft-DVD/ISO** stammen, keine veränderten Quellen.

---

### Quellen/Weitere Infos:

- [Microsoft Docs: WDS](https://learn.microsoft.com/de-de/windows/deployment/wds/)
- [WDS Grundlagen und Best Practices (heise)](https://www.heise.de/ratgeber/Windows-Deployment-Services-im-Unternehmen-einsetzen-4112503.html)

---

Falls du zu bestimmten Schritten eine **ausführlichere Erklärung** oder ein konkretes Beispiel brauchst (z.B. unattend.xml, DHCP-Optionen, Integration von Treibern, etc.), gib einfach Bescheid.

### 3. Benutzer

Als doc bereit stellen

### 4. Assistent

Hier ist die detaillierte Anleitung als DOCX-Datei:

[Installationsserver_Windows_Server_2016_WDS.docx herunterladen](sandbox:/mnt/data/Installationsserver_Windows_Server_2016_WDS.docx)

### 5. Benutzer

Erstelle mir unattend.xml

### 6. Assistent

Natürlich, ich kann dir eine **Beispiel-unattend.xml** (Antwortdatei) für eine automatisierte Windows-Installation bereitstellen. Diese Datei ist eine Vorlage, die angepasst werden muss (z.B. Sprache, Lizenzschlüssel, Benutzer, Partitionierung).  
Sie eignet sich für die meisten Standard-Deployments (z.B. Windows 10 oder 11, auch Windows Server möglich).

**Hinweis:**  
- Diese Vorlage ist für eine „typische“ unbeaufsichtigte Installation ohne Domänenbeitritt, mit automatischer Partitionierung, Sprache Deutsch (Deutschland) und lokaler Anmeldung.
- **Lizenzschlüssel und Benutzerdaten musst du selbst ergänzen** (Platzhalter beachten).
- Die Datei kann mit dem [Windows System Image Manager (WSIM)](https://learn.microsoft.com/de-de/windows-hardware/get-started/adk-install) validiert und individuell erweitert werden.

---

### unattend.xml Vorlage (Minimalkonfiguration, deutsch, lokale Anmeldung, Auto-Partition)

```xml
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <SetupUILanguage>
        <UILanguage>de-DE</UILanguage>
      </SetupUILanguage>
      <InputLocale>0407:00000407</InputLocale>
      <SystemLocale>de-DE</SystemLocale>
      <UILanguage>de-DE</UILanguage>
      <UILanguageFallback>de-DE</UILanguageFallback>
      <UserLocale>de-DE</UserLocale>
    </component>
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
        <AcceptEula>true</AcceptEula>
        <FullName>Administrator</FullName>
        <Organization>Organisation</Organization>
        <!-- <ProductKey>XXXXX-XXXXX-XXXXX-XXXXX-XXXXX</ProductKey>  -->
      </UserData>
      <DiskConfiguration>
        <Disk wcm:action="add">
          <DiskID>0</DiskID>
          <WillWipeDisk>true</WillWipeDisk>
          <CreatePartitions>
            <CreatePartition wcm:action="add">
              <Order>1</Order>
              <Type>Primary</Type>
              <Size>100</Size>
            </CreatePartition>
            <CreatePartition wcm:action="add">
              <Order>2</Order>
              <Type>Primary</Type>
              <Extend>true</Extend>
            </CreatePartition>
          </CreatePartitions>
          <ModifyPartitions>
            <ModifyPartition wcm:action="add">
              <Order>1</Order>
              <PartitionID>1</PartitionID>
              <Format>NTFS</Format>
              <Label>System-reserviert</Label>
              <Active>true</Active>
            </ModifyPartition>
            <ModifyPartition wcm:action="add">
              <Order>2</Order>
              <PartitionID>2</PartitionID>
              <Format>NTFS</Format>
              <Label>Windows</Label>
              <Letter>C</Letter>
            </ModifyPartition>
          </ModifyPartitions>
        </Disk>
        <WillShowUI>OnError</WillShowUI>
      </DiskConfiguration>
    </component>
  </settings>
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-International-Core" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <InputLocale>de-DE</InputLocale>
      <SystemLocale>de-DE</SystemLocale>
      <UILanguage>de-DE</UILanguage>
      <UserLocale>de-DE</UserLocale>
    </component>
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <OOBE>
        <HideEULAPage>true</HideEULAPage>
        <NetworkLocation>Work</NetworkLocation>
        <ProtectYourPC>3</ProtectYourPC>
      </OOBE>
      <RegisteredOrganization>Organisation</RegisteredOrganization>
      <RegisteredOwner>Administrator</RegisteredOwner>
      <TimeZone>W. Europe Standard Time</TimeZone>
      <AutoLogon>
        <Password>
          <Value>Passwort123!</Value>
          <PlainText>true</PlainText>
        </Password>
        <Enabled>true</Enabled>
        <LogonCount>1</LogonCount>
        <Username>Administrator</Username>
      </AutoLogon>
      <UserAccounts>
        <AdministratorPassword>
          <Value>Passwort123!</Value>
          <PlainText>true</PlainText>
        </AdministratorPassword>
      </UserAccounts>
      <DoNotCleanTaskBar>true</DoNotCleanTaskBar>
      <ShowWindowsLive>false</ShowWindowsLive>
      <FirstLogonCommands>
        <!-- Beispiel für ein Startskript, kann gelöscht werden -->
        <!--
        <SynchronousCommand wcm:action="add">
          <Order>1</Order>
          <CommandLine>cmd.exe /c echo Windows-Installation abgeschlossen > C:\install.txt</CommandLine>
          <Description>Test</Description>
        </SynchronousCommand>
        -->
      </FirstLogonCommands>
    </component>
  </settings>
</unattend>
```

---

**Wichtige Hinweise:**
- **Passwort und Namen** bitte anpassen (`Passwort123!`, `Administrator` etc.).
- Optional: `<ProductKey>`-Zeile aktivieren und deinen Lizenzschlüssel eintragen.
- Für Domänenbeitritt, spezielle Treiber oder weitere Einstellungen muss die Datei erweitert werden.
- Datei als **unattend.xml** speichern (UTF-8) und im WDS dem Installationsimage zuweisen.

---

Möchtest du die Datei als Download (z.B. ZIP oder XML), oder hast du spezielle Anforderungen (Domäne, Benutzer, Sprache, Partitionierung, Autologin deaktivieren etc.)?

### 7. Benutzer

Domäne melchy1971.de, Benutzer Diggi, De, autologin on

### 8. Assistent

Hier die **angepasste unattend.xml** für deine Anforderungen:

- **Domäne:** melchy1971.de  
- **Benutzer:** Diggi  
- **Sprache/Region:** Deutsch (Deutschland)  
- **Autologin:** aktiviert für Benutzer Diggi  
- **Administrator-Kennwort:** „Passwort123!“ (bitte ggf. anpassen)  
- **Domänenbeitritt:** Automatisch mit Domänen-Benutzer „Diggi“  
- **Partitionierung:** Standard wie oben

**Hinweis:**  
Für den Domänenbeitritt muss ein Benutzerkonto mit Join-Rechten hinterlegt werden (üblicherweise ein Dienst-User oder Domänen-Admin). Die Zugangsdaten liegen im Klartext in der XML-Datei.  
Der Autologin ist für „Diggi“ gesetzt, das Passwort ebenfalls als Beispiel.

---

```xml
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <SetupUILanguage>
        <UILanguage>de-DE</UILanguage>
      </SetupUILanguage>
      <InputLocale>0407:00000407</InputLocale>
      <SystemLocale>de-DE</SystemLocale>
      <UILanguage>de-DE</UILanguage>
      <UILanguageFallback>de-DE</UILanguageFallback>
      <UserLocale>de-DE</UserLocale>
    </component>
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
        <AcceptEula>true</AcceptEula>
        <FullName>Diggi</FullName>
        <Organization>melchy1971.de</Organization>
        <!-- <ProductKey>XXXXX-XXXXX-XXXXX-XXXXX-XXXXX</ProductKey> -->
      </UserData>
      <DiskConfiguration>
        <Disk wcm:action="add">
          <DiskID>0</DiskID>
          <WillWipeDisk>true</WillWipeDisk>
          <CreatePartitions>
            <CreatePartition wcm:action="add">
              <Order>1</Order>
              <Type>Primary</Type>
              <Size>100</Size>
            </CreatePartition>
            <CreatePartition wcm:action="add">
              <Order>2</Order>
              <Type>Primary</Type>
              <Extend>true</Extend>
            </CreatePartition>
          </CreatePartitions>
          <ModifyPartitions>
            <ModifyPartition wcm:action="add">
              <Order>1</Order>
              <PartitionID>1</PartitionID>
              <Format>NTFS</Format>
              <Label>System-reserviert</Label>
              <Active>true</Active>
            </ModifyPartition>
            <ModifyPartition wcm:action="add">
              <Order>2</Order>
              <PartitionID>2</PartitionID>
              <Format>NTFS</Format>
              <Label>Windows</Label>
              <Letter>C</Letter>
            </ModifyPartition>
          </ModifyPartitions>
        </Disk>
        <WillShowUI>OnError</WillShowUI>
      </DiskConfiguration>
    </component>
  </settings>
  <settings pass="specialize">
    <component name="Microsoft-Windows-UnattendedJoin" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <Identification>
        <JoinDomain>melchy1971.de</JoinDomain>
        <Credentials>
          <Domain>melchy1971.de</Domain>
          <Password>Passwort123!</Password>
          <Username>Diggi</Username>
        </Credentials>
      </Identification>
    </component>
  </settings>
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-International-Core" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <InputLocale>de-DE</InputLocale>
      <SystemLocale>de-DE</SystemLocale>
      <UILanguage>de-DE</UILanguage>
      <UserLocale>de-DE</UserLocale>
    </component>
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <OOBE>
        <HideEULAPage>true</HideEULAPage>
        <NetworkLocation>Work</NetworkLocation>
        <ProtectYourPC>3</ProtectYourPC>
      </OOBE>
      <RegisteredOrganization>melchy1971.de</RegisteredOrganization>
      <RegisteredOwner>Diggi</RegisteredOwner>
      <TimeZone>W. Europe Standard Time</TimeZone>
      <AutoLogon>
        <Password>
          <Value>Passwort123!</Value>
          <PlainText>true</PlainText>
        </Password>
        <Enabled>true</Enabled>
        <LogonCount>1</LogonCount>
        <Username>Diggi</Username>
        <Domain>melchy1971.de</Domain>
      </AutoLogon>
      <UserAccounts>
        <DomainAccounts>
          <DomainAccountList wcm:action="add">
            <Domain>melchy1971.de</Domain>
            <Name>Diggi</Name>
            <Group>Administrators</Group>
          </DomainAccountList>
        </DomainAccounts>
      </UserAccounts>
      <DoNotCleanTaskBar>true</DoNotCleanTaskBar>
      <ShowWindowsLive>false</ShowWindowsLive>
    </component>
  </settings>
</unattend>
```

---

### Download als Datei

Ich stelle dir die Datei als Download zur Verfügung.  
Hinweis: **Passwörter werden im Klartext gespeichert. Das ist aus Sicherheitsgründen nur für Testumgebungen empfehlenswert!**

Die Datei ist als `unattend.xml` gespeichert.

```python
unattend_content = '''<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  ...[hier wie oben, komplett]...
</unattend>
'''

with open("/mnt/data/unattend.xml", "w", encoding="utf-8") as f:
    f.write(unattend_content)
```

Ich übernehme den Vorgang und stelle die Datei bereit. Einen Moment bitte.

### 9. Assistent

Hier ist deine angepasste unattend.xml als Download:

[unattend.xml herunterladen](sandbox:/mnt/data/unattend.xml)

Bitte prüfe die Datei und passe ggf. das Passwort und die Domänenrechte an, falls notwendig. Beachte auch die Hinweise zu Klartextpasswörtern in solchen Automatisierungsdateien.
