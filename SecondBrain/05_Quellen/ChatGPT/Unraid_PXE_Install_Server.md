---
title: "Unraid PXE Install Server"
type: chatgpt_conversation
source: chatgpt
source_id: "6819bc28-a324-8007-9169-00cf910e743d"
created: 2025-05-06
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# Unraid PXE Install Server

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6819bc28-a324-8007-9169-00cf910e743d`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

mit welchem plugin kann ich unter unraid einen installserver zum installieren von clients einrichten

### 2. Assistent

Unter Unraid richtest du einen Install‑ bzw. PXE‑Server heute nicht mehr als klassisches „Plugin“, sondern als Docker‑Container über das **Community‑Applications‑Plugin (CA)** ein – das ist der von Unraid empfohlene Weg, um zusätzliche Dienste bereitzustellen. citeturn9view0  

---

### 1 · netboot.xyz (linuxserver/netbootxyz)  
*Empfehlung für reine OS‑Installationen*  

* **Funktion:** Stellt ein iPXE‑Menü bereit, aus dem du Live‑/Install‑Medien zahl­loser Linux‑Distributionen, Windows‑Versionen, Hilfs­tools usw. direkt übers Netz booten kannst. citeturn8view0turn11view0  
* **Installation:**  
  1. CA‑Plugin öffnen → nach **“netbootxyz”** suchen → Container hinzufügen.  
  2. Ablagepfad für **/config** (enthält Menüs & gecachte Images) und – falls gewünscht – **/assets** vergeben.  
  3. Entweder den integrierten *dnsmasq* (TFTP + DHCP) aktivieren **oder** deinen Router/​DHCP‑Server so konfigurieren, dass Option 66 auf die Unraid‑IP und Option 67 auf `netboot.xyz.kpxe` (UEFI: `netboot.xyz.efi`) zeigt.  
  4. Container starten, Web‑GUI (`http://<IP>:3000`) öffnen, Menü anpassen, fertig.  

**Pluspunkte:** sehr schlank, kein NFS/Samba nötig, Updates via Pull‑Button in der GUI – ideal, wenn du nur installieren (nicht klonen) willst.

---

### 2 · FOG Project (fogproject)  
*Empfehlung für Imaging & Massen­deployment*  

* **Funktion:** Vollwertige Imaging‑Suite (Aufnehmen, Verteilen, Snap‑ins, Inventar) für Windows, macOS & Linux. citeturn6view0  
* **Installation:**  
  1. In CA nach **“fogproject”** suchen.  
  2. Shares für **/images** (NFS‑Export!), **/opt/fog** usw. anlegen.  
  3. Wichtige Ports freigeben: 80/443 (TCP), 69 (UDP TFTP), 2049 (NFS) u.a.  
  4. Nach dem ersten Start Web‑Installer unter `http://<IP>/fog` durchklicken.  

**Hinweis:** Weil FOG PXE + NFS nutzt, müssen Unraid‑Firewall und Docker‑Netz die NFS‑Ports durchlassen; außerdem sollte dein Switch PXE‑Broadcasts (Option 66/67) nicht filtern.

---

### 3 · iVentoy (iventoy)  
*“Drag‑&‑Drop”‑PXE für ISO‑Dateien*  

* **Funktion:** Einfach ISO‑Dateien in einen Ordner legen → iVentoy erzeugt automatisch ein grafisches PXE‑Menü, von dem mehrere Clients parallel booten können. citeturn13search0  
* **Installation:** Analog zu den obigen Containern; bei Erststart legt der Container die ISO‑Ablage (`/iso`) an.

---

## Entscheidungshilfe (Kurzfassung)

| Szenario | Geeigneter Container |
|----------|---------------------|
| Nur Betriebssysteme installieren | **netboot.xyz** |
| Betriebssysteme klonen/­wiederherstellen, Snap‑ins, Inventory | **FOG Project** |
| ISO‑Dateien flexibel übers Netz booten | **iVentoy** |

*(Tabelle dient rein der Übersicht.)*

---

## Allgemeine Tipps

1. **Community Applications zuerst aktualisieren**, damit die Vorlagen auf dem neuesten Stand sind.  
2. **DHCP‑Optionen (66/67)** immer nur von *einem* Server im Netz ausliefern, sonst booten Clients unzuverlässig.  
3. Bei UEFI‑Clients auf die korrekte Bootdatei (`*.efi`) achten.  
4. Wenn du später von Legacy‑ auf UEFI‑Boot wechselst, prüfe, ob dein Switch *Spanning Tree Fast* oder *PortFast* aktiviert hat; PXE‑Boots sind sonst langsam.  

Damit hast du die wesentlichen Varianten an der Hand – such dir im CA‑Tab einfach den Container aus, der am besten zu deinem Einsatz­zweck passt, und folge der jeweiligen Vorlage. Viel Erfolg beim Einrichten!
