---
title: "Speedport einrichten Anleitung"
type: chatgpt_conversation
source: chatgpt
source_id: "68bbf0bb-1004-8328-9d3f-3de0aedbdd69"
created: 2025-09-06
tags:
  - chatgpt
  - import
  - sap
---


# Speedport einrichten Anleitung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68bbf0bb-1004-8328-9d3f-3de0aedbdd69`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Speedport als accesspoint an speedport smart 4 einrichten

### 2. Assistent

Um einen zusätzlichen Speedport‑Router hinter dem Speedport Smart 4 als reinen WLAN‑Access‑Point zu betreiben, muss das Gerät nicht routen, sondern darf nur noch als Switch mit Funkbasis arbeiten. Dafür sind im Wesentlichen zwei Dinge erforderlich: Der Access‑Point darf keine IP‑Adressen verteilen (DHCP deaktivieren) und er muss eine feste IP‑Adresse aus demselben Netz wie der Haupt‑Speedport haben. Unten sind die Schritte ausführlich beschrieben.

1. **Vorbereitungen am Speedport Smart 4 (Hauptrouter)**  
   - Melden Sie sich an der Benutzeroberfläche Ihres Smart 4 an (`speedport.ip`) und notieren Sie sich die IP‑Einstellungen: Netzwerk‑/Subnetz und den DHCP‑Adressbereich. In den Werkseinstellungen nutzt der Smart 4 das Netz `192.168.2.0/24` und der DHCP‑Server vergibt Adressen im Bereich `192.168.2.30–192.168.2.230`【642756904809548†L4703-L4731】.  
   - Prüfen Sie außerdem, welche LAN‑Ports frei sind. Der Smart 4 besitzt drei gelbe LAN‑Buchsen (LAN 2–4) sowie eine konfigurierbare „Link/LAN1“‑Buchse. Laut Bedienungsanleitung kann die blaue Link/LAN1‑Buchse bei Bedarf als LAN‑Port genutzt werden【642756904809548†L6818-L6827】.

2. **Speedport‑Access‑Point vorbereiten**  
   - Verbinden Sie sich zunächst direkt mit dem zweiten Speedport (entweder über dessen WLAN oder per Netzwerkkabel). Rufen Sie `speedport.ip` auf und melden Sie sich mit dem Gerätepasswort an.  
   - Schalten Sie den **Expertenmodus** ein („Einstellungen → Ansicht → Expertenmodus“).  
   - Navigieren Sie zu **Heimnetzwerk → WLAN‑Access‑Point** (falls das Gerät diese Option bietet). Dort vergeben Sie eine **feste IPv4‑Adresse** für den zweiten Speedport. Wichtig: Die ersten drei Oktette müssen mit dem Haupt‑Speedport übereinstimmen, die letzte Zahl darf nicht im DHCP‑Bereich liegen【571676478560971†L110-L116】. Beispiel: wenn der Smart 4 Adressen zwischen `192.168.2.30` und `192.168.2.230` verteilt, können Sie dem Access‑Point die Adresse `192.168.2.2` oder `192.168.2.250` geben. Die Subnetzmaske bleibt `255.255.255.0`.  
   - Speichern Sie die Änderung.

3. **DHCP‑Server des Access‑Points deaktivieren**  
   - Im Menü **Heimnetzwerk (LAN)** wählen Sie **Adressvergabe (DHCP)**【642756904809548†L4703-L4715】.  
   - Wählen Sie dort „DHCP **aus**“, damit der Access‑Point keine IP‑Adressen mehr verteilt【642756904809548†L4703-L4715】. Auf diese Weise erhalten alle Geräte ihre Adressen vom Smart 4.  
   - Speichern Sie die Einstellungen. Die WLAN‑Verbindung kann danach kurzzeitig unterbrochen werden; stellen Sie die Verbindung zum Access‑Point ggf. neu her.

4. **Geräte verbinden**  
   - Verbinden Sie den zweiten Speedport mit einem LAN‑Kabel mit dem Hauptrouter. Benutzen Sie dafür einen **gelben LAN‑Port** (LAN 2–4) am Smart 4 – die Community empfiehlt explizit diese Ports【733554862945145†L95-L98】. Wenn alle drei gelben Ports belegt sind, können Sie die blaue Link/LAN1‑Buchse auf „LAN“ umstellen【642756904809548†L6818-L6827】.  
   - Am Access‑Point stecken Sie das LAN‑Kabel ebenfalls in eine der LAN‑Buchsen (nicht in die DSL/WAN‑Buchse). Dadurch arbeitet er wie ein Switch und Access‑Point – NAT und Routing werden nicht genutzt.

5. **WLAN‑Einstellungen anpassen**  
   - Unter **WLAN‑Grundeinstellungen** können Sie den Netzwerk‑Namen (SSID) und den WLAN‑Schlüssel einstellen. Für ein nahtloses Roaming empfiehlt es sich, dieselbe SSID und dasselbe Passwort wie beim Smart 4 zu verwenden; die Kanäle können Sie unterschiedlich wählen, um Störungen zu minimieren.  
   - Speichern Sie die Änderungen und starten Sie den Access‑Point neu. Nach dem Neustart ist das Gerät unter der von Ihnen vergebenen IP‑Adresse erreichbar【571676478560971†L119-L124】.

6. **Hinweise und Alternativen**  
   - Nach Ansicht der Telekom‑Community ist es „Perlen vor die Säue“, den Smart 4 zu einem Access‑Point „herunterzustufen“; es funktioniert aber: Sie müssen dem Smart 4 (bzw. dem zweiten Speedport) eine feste IP geben, DHCP deaktivieren und ihn über die LAN‑Buchsen 2–4 ins Netz einbinden【733554862945145†L95-L98】.  
   - Einige Nutzer empfehlen stattdessen einen dedizierten Mesh‑Repeater (Speed Home WLAN). Dieser lässt sich einfacher einrichten und bildet zusammen mit dem Smart 4 ein echtes Mesh‑Netz【884767142869840†L232-L236】. Wenn Sie dennoch einen zweiten Speedport nutzen möchten, befolgen Sie die obigen Schritte.  
   - Denken Sie daran, dass der Access‑Point keine Router‑Funktionen mehr übernimmt; Telefonie‑Anschlüsse, Firewall‑Regeln oder Port‑Freigaben können nur noch am Smart 4 geändert werden.

Mit diesen Schritten funktioniert der zweite Speedport als reiner WLAN‑Access‑Point: Er verteilt keine IP‑Adressen mehr, hat eine feste Adresse im selben Subnetz wie der Smart 4 und stellt über seine LAN‑Ports und das WLAN lediglich den Zugang zum bestehenden Netz bereit.
