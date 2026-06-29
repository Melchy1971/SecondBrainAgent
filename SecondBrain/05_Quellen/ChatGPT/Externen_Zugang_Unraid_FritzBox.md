---
title: "Externen Zugang Unraid FritzBox"
type: chatgpt_conversation
source: chatgpt
source_id: "6811f1b4-6098-8007-9ca1-67fca205c744"
created: 2025-04-30
tags:
  - chatgpt
  - code
  - import
  - ki
---


# Externen Zugang Unraid FritzBox

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6811f1b4-6098-8007-9ca1-67fca205c744`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

wie richte ich einen externen zugang auf meinen unraidserver und fritzbox ein

### 2. Assistent

Hier ein bewährter Fahrplan, wie du *ohne unnötige Löcher in der Firewall* von unterwegs sicher auf deinen Unraid-Server und (falls gewünscht) auf die Fritz!Box zugreifst.

---

## 1 Grundsatz: VPN statt blankes Port-Forwarding  
Unraid selbst weist ausdrücklich darauf hin, dass die WebGUI **niemals** ungeschützt ins Internet gestellt werden sollte; empfohlen wird eine VPN-Lösung wie WireGuard – der Dienst ist bereits in Unraid integriert citeturn8view0.  

---

## 2 Variante A – WireGuard auf Unraid als VPN-Server

| Schritt | Was du tust | Wo in Unraid/Fritz!Box |
|---------|-------------|------------------------|
| **A-1 Vorbereitung** | • Dem Server eine feste interne IP geben (z. B. 192.168.178.200).<br>• Optional DynDNS (MyFRITZ!, DuckDNS …); damit hält die Konfiguration ihre öffentliche IP aktuell citeturn8view0 | Fritz!Box → *Heimnetz > Netzwerk* |
| **A-2 WireGuard aktivieren** | *Settings > VPN Manager* öffnen, Tunnelname vergeben, **Generate Keypair**, gewünschten UDP-Port (Standard 51820) bestätigen, bei “Local endpoint” deinen DynDNS-Namen eintragen und *Apply* klicken citeturn8view0 | Unraid WebGUI |
| **A-3 Peers anlegen** | *Add Peer* → Typ “Remote access to LAN”, Keys erzeugen, QR-Code oder Config-Datei exportieren – damit kannst du Smartphone/Notebook koppeln citeturn8view0 | Unraid WebGUI |
| **A-4 Portfreigabe** | In der Fritz!Box unter *Internet > Freigaben > Gerät* = Unraid-IP: <br>• Protokoll UDP<br>• Port extern = intern = 51820<br>Speichern und übernehmen citeturn10view0 | Fritz!Box |
| **A-5 Testen** | Mobilfunk einschalten, WireGuard-App aktivieren → Browser: `https://<unraid-interne-IP>` oder `https://<dynDNS-Name>` – wenn das Dashboard erscheint, läuft alles. | – |

**Tipp:** Ist UPnP in der Fritz!Box aktiv, setzt Unraid die Freigabe sogar automatisch citeturn8view0.

---

## 3 Variante B – Fritz!Box als VPN-Server (ab FRITZ!OS 7.50 mit WireGuard)

1. *Internet > Freigaben > VPN (WireGuard)* → **Verbindung hinzufügen**  
2. Assistent “*Geräte im Heimnetz*” durchlaufen, Config-Datei exportieren/QR-Code scannen citeturn3view0  
3. Auf Smartphone/Notebook die Datei importieren und Tunnel aktivieren.  
4. Jetzt bist du per VPN im Heimnetz; der Unraid-Server ist ganz normal unter seiner LAN-IP erreichbar – keine zusätzliche Port-Weiterleitung nötig.

Diese Variante umgeht Probleme mit DS-Lite-Anschlüssen (kein öffentliches IPv4): Die Fritz!Box kümmert sich um alles, du brauchst nur einen erreichbaren IPv6-/IPv4-Endpunkt.

---

## 4 Optional: MyFRITZ!-/HTTPS-Zugriff auf die Fritz!Box selbst  
Falls du auch die Router-Oberfläche fernsteuern willst:

1. *Internet > MyFRITZ!-Konto* → **“Internetzugriff auf die Fritz!Box über HTTPS”** aktivieren.  
2. Unter *System > Fritz!Box-Benutzer* einen Account mit Recht “Zugang aus dem Internet erlauben” anlegen citeturn11view0.

Du erreichst die Box dann bequem über `https://<zufällige-ID>.myfritz.net`, abgesichert durch Let’s-Encrypt-Zertifikat.

---

## 5 Sicherheitshinweise

* **SSL für Unraid aktivieren** – *Settings > Management Access > Use SSL/TLS* und kostenloses Zertifikat anfordern.  
* **Starke Passwörter / 2-FA** sowohl in Unraid als auch in der Fritz!Box nutzen.  
* **Regelmäßige Updates** (Unraid OS, Docker-Container, FRITZ!OS).  
* Kein zusätzliches Port-Forwarding für HTTP/SSH öffnen, solange du es nicht wirklich brauchst.  
* Bei DS-Lite ohne native IPv4 kannst du alternativ Cloudflare-Tunnel oder die Fritz!Box-WireGuard-Option (Variante B) einsetzen.

---

## 6 Kurz zusammengefasst

* **Empfohlener Weg:** VPN (WireGuard) nutzen, **einzig** Port 51820/UDP (oder einen anderen) in der Fritz!Box weiterleiten.  
* **Alternativ:** Fritz!Box selbst als WireGuard-Server → gar kein Port-Forwarding.  
* **Direkte MyFRITZ!-Freigaben** nur für die Router-Oberfläche oder wirklich unkritische Dienste.

---

### Noch Fragen?  
Falls du z. B. nur DS-Lite-IPv6 bekommst oder Hilfe beim Anlegen der Peer-Config brauchst, sag Bescheid – dann gehen wir gezielt darauf ein.
