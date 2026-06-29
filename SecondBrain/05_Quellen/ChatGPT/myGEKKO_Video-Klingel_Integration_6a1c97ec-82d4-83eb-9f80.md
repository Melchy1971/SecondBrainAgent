---
title: "myGEKKO Video-Klingel Integration"
type: chatgpt_conversation
source: chatgpt
source_id: "6a1c97ec-82d4-83eb-9f80-6674c0cd7acb"
created: 2026-05-31
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# myGEKKO Video-Klingel Integration

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6a1c97ec-82d4-83eb-9f80-6674c0cd7acb`
- Nachrichten: 35

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

MyGEKKO Video Klingel

### 2. Assistent

Ich prüfe die aktuelle myGEKKO-Logik für Türkommunikation und trenne dabei drei Ebenen: kompatible Hardware, technische Einbindung und sinnvolle Systemarchitektur mit PV/Smart-Home-Folgen.

### 3. Assistent

Für **myGEKKO Video-Klingel** ist die robuste Lösung keine klassische WLAN-Consumer-Doorbell, sondern eine **IP-Video-Türstation mit SIP/VoIP**.

## Zielarchitektur

```text
Video-Türstation
   │ LAN / PoE
   ▼
Netzwerk / Switch
   │
   ├─ myGEKKO Slide 2 / Gebäuderegler als VoIP-Videotelefon
   ├─ Kameraansicht im myGEKKO System „Video“
   └─ optional SIP-Server / FritzBox für Weiterleitung aufs Smartphone
```

## Geeignete Systeme

### 1. 2N Türstationen

myGEKKO dokumentiert 2N explizit als kompatible VoIP-Haussprechstelle. Die Anbindung läuft über LAN; myGEKKO kann die Haussprechstelle konfigurieren, steuern und die Türöffnerfunktion nutzen. citeturn369409search3

Geeignet, wenn:
- stabile professionelle Installation gewünscht ist
- Türöffner integriert werden soll
- PoE/LAN vorhanden oder nachrüstbar ist
- lokale Smart-Home-Integration wichtiger ist als reine App-Nutzung

### 2. DoorBird

DoorBird ist ebenfalls dokumentiert und hat eine myGEKKO-Integration. Laut DoorBird-Connect-Dokumentation von 01/2026 wird eine DoorBird IP Video Door Station mit einem myGEKKO Display Controller integriert. citeturn369409search20  
myGEKKO nennt DoorBird außerdem als Partner für IP-Video-Türsprechanlagen. citeturn369409search12

Geeignet, wenn:
- App-Nutzung wichtig ist
- bestehende DoorBird-Komponenten vorhanden sind
- Kombination aus Cloud/App und myGEKKO akzeptiert wird

## Technische Mindestanforderungen

Die Türstation sollte erfüllen:

| Bereich | Mindestanforderung |
|---|---|
| Netzwerk | LAN, ideal PoE |
| Telefonie | SIP / VoIP |
| Audio | G.711 a-law/u-law |
| Gespräch | Full Duplex |
| Echo | Echounterdrückung |
| Video | JPG/JPEG Snapshot, MJPEG oder kompatibler Stream |
| myGEKKO Video | JPG-Stream, MJPEG, CGI, H.264 über RTSP oder H.265 über RTSP |

myGEKKO beschreibt den Slide 2 als VoIP-Videotelefon für VoIP-fähige Geräte; Hauptzweck ist die Video-Gegensprechanlage. citeturn369409search7  
Das System „Video“ unterstützt u. a. JPG-Stream, MJPEG, CGI, H.264 über RTSP und H.265 über RTSP. citeturn369409search9

## Zwei Einbindungsvarianten

### Variante A: Direct Call

```text
Türstation ruft direkt myGEKKO an
```

Vorteile:
- weniger Komponenten
- lokal
- geringe Komplexität

Nachteile:
- Smartphone-Weiterleitung schwieriger
- mehrere Innenstellen nur, wenn die Türstation parallele SIP-Rufe unterstützt

myGEKKO verlangt dafür SIP, direkte Nummernwahl ohne SIP-Server, G.711, Full Duplex, Echo-Unterdrückung und Video-Snapshot/MJPEG. citeturn369409search5

### Variante B: SIP-Server / FritzBox

```text
Türstation → SIP-Server/FritzBox → myGEKKO / Smartphone
```

Vorteile:
- sauberere Rufverteilung
- Weiterleitung auf Smartphone möglich
- besser bei mehreren Endgeräten

Nachteile:
- zusätzliche Fehlerquelle
- SIP-Konfiguration nötig
- Netzwerk/Firewall sauber halten

myGEKKO nennt explizit einen SIP-Server, z. B. FritzBox, für die Weiterleitung und Kommunikation mit myGEKKO. citeturn369409search18

## Empfehlung für dein Setup

Für dein Haus mit **myGEKKO Slider 2**, PV, Speicher und Smart-Home-Integration:

**Priorität 1: 2N IP-Türstation per LAN/PoE.**  
Grund: myGEKKO-nahe Integration, professioneller Ansatz, weniger Consumer-Cloud-Abhängigkeit.

**Priorität 2: DoorBird, wenn App-Komfort wichtiger ist.**  
Grund: ebenfalls dokumentiert, gute App-Ausrichtung, aber tendenziell mehr Hersteller-Ökosystem.

**Nicht bevorzugt:** Ring, Google Nest Doorbell, reine WLAN-Türklingeln.  
Grund: oft Cloud-zentriert, eingeschränkter lokaler SIP/RTSP-Zugriff, schlechtere myGEKKO-Integration.

## Umsetzungsschritte

1. **LAN/PoE zur Haustür prüfen**
   - Idealfall: CAT-Kabel + PoE-Switch.
   - WLAN nur als Notlösung.

2. **Türstation auswählen**
   - 2N IP Verso / 2N IP Solo oder vergleichbar.
   - DoorBird nur bei App-Priorität.

3. **SIP-Struktur festlegen**
   - Einfach: Direct Call auf myGEKKO.
   - Besser: FritzBox/SIP-Server als Vermittler.

4. **myGEKKO VoIP aktivieren**
   - VoIP-Client aktivieren.
   - SIP-Benutzer/Nummer vergeben.
   - Klingelton, Klingelzeit, Lautstärke setzen.

5. **Kamera in myGEKKO Video einbinden**
   - Snapshot-URL oder RTSP/MJPEG-Stream eintragen.
   - Bei 2N z. B. Snapshot-Pfad über HTTP API; myGEKKO dokumentiert dafür Kamera-Snapshot-URLs. citeturn369409search8

6. **Türöffner getrennt absichern**
   - Türöffner nicht blind über Cloud/App freigeben.
   - Relais lokal, abgesichert und nachvollziehbar schalten.

## Kritische Fehlerquellen

| Fehler | Auswirkung |
|---|---|
| WLAN-Klingel statt LAN/PoE | instabile Verbindung, Latenz |
| kein SIP | myGEKKO kann nicht sauber klingeln |
| nur App-Cloud | schlechte lokale Integration |
| falscher Codec | Audio funktioniert nicht |
| kein Snapshot/RTSP | kein Bild in myGEKKO |
| Türöffner direkt an unsicherem Relais | Sicherheitsrisiko |
| VLAN/Firewall blockiert SIP/RTP | Klingeln ohne Ton/Bild |

## Zielbild

```text
2N / DoorBird IP-Türstation
→ SIP-Anruf an myGEKKO
→ Livebild im myGEKKO Video-System
→ optional Türöffner über myGEKKO
→ optional Smartphone-Weiterleitung über FritzBox/SIP
```

Beste Entscheidung: **2N per PoE + SIP über FritzBox oder lokalen SIP-Server + Kameraeinbindung in myGEKKO Video.**

### 4. Benutzer

Ich habe bereits eine verbaut diese ist defekt. Welche kompatibelen gibt es

### 5. Assistent

Kompatibel mit myGEKKO sind primär **2N** und **DoorBird**. Beide sind offiziell in der myGEKKO-Dokumentation geführt. Die Kommunikation läuft über **LAN/VoIP**, Video über Kamera-/Stream-Einbindung, Türöffner optional über Relais. citeturn574597search5turn574597search3turn574597search17

## Kompatible 2N-Modelle

| Modell | Audio | Video | Bewertung |
|---|---:|---:|---|
| **2N IP Verso** | ja | ja | Beste modulare Lösung |
| **2N IP Solo** | ja | ja | Sehr gut für Einfamilienhaus |
| **2N IP Base** | ja | ja | Einfachere Standardlösung |
| **2N IP Force** | ja | ja | Robust, vandalismussicher |
| **2N IP Vario** | ja | ja | Ältere/klassische Serie |
| **2N IP Style** | ja | ja | Hochwertig, teuer |
| **2N IP Video Kit** | ja | ja | Für Sonder-/Einbaulösungen |
| **2N IP Uni** | ja | nein | Nur Audio, nicht ideal |
| **2N IP Audio Kit** | ja | nein | Nur Audio, nicht ideal |

myGEKKO führt diese 2N-Modelle im VoIP-Handbuch als kompatibel; neuere myGEKKO-Hinweise nennen für 2N mindestens Firmware **2.40 oder höher**. citeturn574597search4turn574597search2

## Kompatible DoorBird-Modelle

| Modell | Tasten | Montage | Bewertung |
|---|---:|---|---|
| **DoorBird D1101V** | 1 | Aufputz / Unterputz | Gute einfache Lösung |
| **DoorBird D1102V** | 2 | Unterputz | Für 2 Parteien |
| **DoorBird D2101FV ekey UP** | 1 | Unterputz | Mit Fingerprint-Option |
| **DoorBird D2102FV ekey UP** | 2 | Unterputz | Mit Fingerprint-Option, 2 Parteien |
| **DoorBird A1101** | innen | Aufputz | Innensprechstelle, nicht Außenklingel |

myGEKKO nennt DoorBird als eigene Geräteschnittstelle und unterstützt laut Katalog bis zu **vier DoorBird Sprechstellen**. Die Einbindung erfolgt über LAN; WLAN ist technisch möglich, aber weniger robust. citeturn574597search0turn574597search3turn574597search8

## Empfehlung als Ersatz

### Beste Wahl: 2N IP Solo

Für ein Einfamilienhaus mit bestehender myGEKKO-Anlage:

```text
2N IP Solo
→ LAN/PoE
→ myGEKKO VoIP/Sprechstelle
→ Video im myGEKKO System
→ Türöffner optional lokal
```

**Warum:**  
Kompakt, sauber integrierbar, Video vorhanden, weniger überdimensioniert als Verso, professioneller als viele Consumer-Klingeln.

### Beste modulare Wahl: 2N IP Verso

Nehmen, wenn du brauchst:

- Fingerprint
- Keypad
- mehrere Ruftasten
- RFID
- Erweiterungsmodule
- späterer Ausbau

### Beste App-orientierte Wahl: DoorBird D1101V oder D2101FV

Nehmen, wenn dir wichtig ist:

- DoorBird App
- Push aufs Smartphone
- einfache Nutzerverwaltung
- stärkerer App-Komfort

## Nicht nehmen

| Gerätetyp | Grund |
|---|---|
| Ring Doorbell | keine saubere lokale myGEKKO-Integration |
| Google Nest Doorbell | Cloud-/App-zentriert |
| Eufy Video Doorbell | meist nicht sauber SIP/myGEKKO-fähig |
| Reolink Doorbell | kann für Video interessant sein, aber keine offiziell dokumentierte myGEKKO-Sprechstellenintegration |
| reine WLAN-Klingeln | Ausfallrisiko, Latenz, schlechtere Integration |

## Entscheidungsmatrix

| Kriterium | 2N IP Solo | 2N IP Verso | DoorBird D1101V/D2101 |
|---|---:|---:|---:|
| myGEKKO-Nähe | hoch | hoch | hoch |
| Modularität | mittel | sehr hoch | mittel |
| App-Komfort | mittel | mittel | hoch |
| Preis | mittel | hoch | mittel-hoch |
| Robustheit | hoch | hoch | hoch |
| Nachrüstung | gut | aufwendiger | gut |
| Fingerprint möglich | eingeschränkt/je nach Variante | ja | ja bei ekey-Varianten |
| Empfehlung | **1. Wahl** | Ausbau-Variante | App-Variante |

## Mindestprüfung vor Kauf

Vor Ersatzkauf diese Punkte prüfen:

```text
1. Aktuelles Modell der defekten Klingel
2. Montageart: Aufputz oder Unterputz
3. vorhandenes Kabel: LAN/CAT, 2-Draht, Klingeldraht, Strom
4. Versorgung: PoE, 12/24 V, separates Netzteil
5. Anzahl Klingeltasten
6. Türöffner vorhanden: ja/nein
7. Fingerprint/RFID gewünscht: ja/nein
8. myGEKKO OS-Version
```

## Konkrete Ersatzempfehlung

Ohne weitere Sonderanforderungen:

```text
1. 2N IP Solo
2. 2N IP Verso, wenn modular/Fingerprint/RFID gewünscht
3. DoorBird D1101V, wenn App-Komfort wichtiger ist
4. DoorBird D2101FV ekey UP, wenn Fingerprint integriert werden soll
```

Beste Standardentscheidung: **2N IP Solo per LAN/PoE**.

### 6. Benutzer

2N IP Solo
→ LAN/PoE
→ myGEKKO VoIP/Sprechstelle
→ Video im myGEKKO System
→ Türöffner optional lokal

### 7. Assistent

Ja. Das ist die saubere Zielarchitektur.

```text
2N IP Solo
→ LAN/PoE
→ myGEKKO VoIP / Sprechstelle
→ Video im myGEKKO System
→ Türöffner optional lokal
```

## Warum diese Kombination passt

myGEKKO unterstützt **2N VoIP-Haussprechstellen** über das lokale Netzwerk. Die 2N-Sprechstellen können als Video-Gegensprechanlage genutzt werden; Kamera, Mikrofon, Steuerung und Türöffnerfunktion sind im myGEKKO-Konzept vorgesehen. citeturn755016search5

myGEKKO beschreibt das System **Sprechstelle** explizit für 2N und DoorBird. Die Kommunikation läuft über **VoIP**, ein Türöffner kann eingebunden werden. citeturn755016search7

Das myGEKKO-System **Video** kann passende Kameraquellen anzeigen, unter anderem **JPG-Stream, MJPEG, CGI, H.264 über RTSP und H.265 über RTSP**. citeturn755016search2

## Umsetzung als Ersatzgerät

### 1. Hardware

Empfohlene Variante:

```text
2N IP Solo
PoE-Switch oder PoE-Injektor
LAN zur Haustür
myGEKKO Slide / Displaycontroller
optional vorhandener elektrischer Türöffner
```

Wichtig: Die 2N IP Solo braucht idealerweise **LAN mit PoE**. Wenn deine alte Klingel nur über 2-Draht oder Klingeldraht angebunden ist, muss geprüft werden, ob ein Netzwerkkabel vorhanden ist oder nachgezogen werden kann.

## 2. Netzwerk

Empfohlene feste Struktur:

```text
2N IP Solo:        feste IP, z. B. 192.168.178.60
myGEKKO:           feste IP, z. B. 192.168.178.20
FritzBox/SIP:      optional
PoE-Switch:        gleiche Netzwerkzone
```

Keine Cloud-Abhängigkeit als Kernfunktion. Die Türkommunikation sollte lokal funktionieren.

## 3. VoIP / Sprechstelle

Zwei Varianten.

### Variante A: Direktverbindung

```text
2N IP Solo ruft direkt myGEKKO an
```

Geeignet, wenn nur myGEKKO klingeln soll.

Vorteile:
- einfache Architektur
- weniger Fehlerquellen
- lokal

Nachteile:
- Smartphone-Weiterleitung eingeschränkt
- mehrere Endgeräte schwieriger

### Variante B: über FritzBox oder SIP-Server

```text
2N IP Solo
→ FritzBox / SIP-Server
→ myGEKKO
→ optional Smartphone / Telefon
```

Geeignet, wenn zusätzlich Handy, DECT-Telefon oder mehrere Innenstellen klingeln sollen.

Vorteile:
- bessere Rufverteilung
- Smartphone/Telefonie leichter möglich
- flexibler

Nachteile:
- mehr Konfiguration
- SIP/RTP kann bei falscher Netzwerkkonfiguration Probleme machen

## 4. Videoeinbindung

Die 2N liefert das Kamerabild. myGEKKO bindet es im System **Video** ein.

Typische Zielkonfiguration:

```text
myGEKKO Video
→ Kamera hinzufügen
→ Stream/Snapshot der 2N IP Solo eintragen
→ VoIP-Link setzen
→ Bild wird beim Klingeln angezeigt
```

myGEKKO unterstützt die relevanten Streamformate für Netzwerkkameras. citeturn755016search2

## 5. Türöffner

Empfehlung:

```text
Türöffner nicht cloudbasiert
Türöffner lokal über Relais
Freigabe über myGEKKO oder 2N sauber absichern
```

Wichtig:
- Relaiskontakt passend zum vorhandenen Türöffner prüfen.
- Spannung des Türöffners prüfen: oft 12 V AC/DC oder 24 V.
- Türöffnerstrom nicht blind über das falsche Relais führen.
- Bei Unsicherheit: Relais nur als potentialfreier Schaltkontakt nutzen und vorhandene Türöffner-Versorgung beibehalten.

## Kaufentscheidung

Für ein Einfamilienhaus:

```text
1. Wahl: 2N IP Solo
Alternative bei Modulen/Fingerprint/RFID: 2N IP Verso
Alternative mit stärkerer App-Nutzung: DoorBird D1101V / D2101FV
```

## Vor Kauf zwingend prüfen

| Punkt | Sollzustand |
|---|---|
| Montageart | passt zur vorhandenen Einbausituation |
| Kabel | LAN/CAT vorhanden oder nachrüstbar |
| Strom | PoE möglich |
| Anzahl Klingeltasten | 1 Taste bei IP Solo |
| Türöffner | Spannung und Schaltart bekannt |
| myGEKKO | VoIP/Sprechstelle verfügbar |
| Netzwerk | myGEKKO und 2N im gleichen Netz erreichbar |
| Smartphone-Wunsch | entscheidet über Direktverbindung vs. FritzBox/SIP |

## Empfehlung

Kaufen würde ich in deinem Fall:

```text
2N IP Solo
+ PoE-Versorgung
+ feste IP-Adresse
+ Einbindung als 2N VoIP-Sprechstelle in myGEKKO
+ Kamera als Videoquelle in myGEKKO
+ Türöffner lokal über Relais
```

Nicht kaufen:
```text
Ring
Google Nest
Eufy
reine WLAN-Video-Klingel
```

Grund: keine robuste, lokal saubere myGEKKO-Integration.

### 8. Benutzer

1. Wahl: 2N IP Solo
Alternative bei Modulen/Fingerprint/RFID: 2N IP Verso
Alternative mit stärkerer App-Nutzung: DoorBird D1101V / D2101FV

### 9. Assistent

Korrekt. Daraus ergibt sich diese klare Auswahl.

## Entscheidung

| Rang | Gerät | Einsatzfall | Entscheidung |
|---:|---|---|---|
| 1 | **2N IP Solo** | Einfamilienhaus, 1 Klingeltaste, stabile myGEKKO-Integration | **nehmen** |
| 2 | **2N IP Verso** | Module, Fingerprint, RFID, Keypad, mehrere Funktionen | nur bei Ausbauwunsch |
| 3 | **DoorBird D1101V / D2101FV** | App-Komfort, Smartphone-Push, DoorBird-Ökosystem | nur wenn App wichtiger ist |

## Beste Ersatzwahl

```text
2N IP Solo
+ Kamera
+ LAN/PoE
+ SIP/VoIP
+ 1 Ruftaste
+ Türöffner-Relais
```

myGEKKO unterstützt 2N-VoIP-Haussprechstellen über LAN; Kamera, Mikrofon, bidirektionale Kommunikation und Türöffnerfunktion sind vorgesehen. citeturn505608search0

Das myGEKKO-System „Sprechstelle“ bindet 2N und DoorBird per VoIP ein; Türöffner können ebenfalls eingebunden werden. citeturn505608search1

## Wichtig beim Kauf der 2N IP Solo

Nicht versehentlich die falsche Variante kaufen.

Prüfen:

```text
2N IP Solo MIT Kamera
Montageart: Aufputz oder Unterputz
PoE-fähig
SIP/VoIP aktiviert
1 Klingeltaste ausreichend
Türöffnerkontakt passend
```

2N nennt bei der IP Solo SIP als Signalisierungsprotokoll, Full Duplex mit Echo-Unterdrückung und Audio-Codecs wie G.711; genau diese Eigenschaften sind für myGEKKO relevant. citeturn505608search8

## Ausschluss

```text
2N IP Solo ohne Kamera → nicht nehmen
2N IP Uni → nicht nehmen, nur Audio
DoorBird nur WLAN → nicht bevorzugen
Ring / Nest / Eufy → nicht nehmen
```

## Finale Empfehlung

```text
Kaufen:
2N IP Solo Video
passend zur vorhandenen Montageart
mit PoE über LAN
```

Nur auf **2N IP Verso** wechseln, wenn Fingerprint, RFID, Keypad oder spätere Erweiterungen zwingend sind.

### 10. Benutzer

Erstelle mir eine Liste in Excel aller möglichen Variationen auch Drittanbieter, die mit meiner myGEKKO Slide zwei kompatibel sind inklusive Preis

### 11. Assistent

Ich erstelle eine Excel-Liste mit Kategorien, Kompatibilitätsart, Voraussetzungen, Risiken und Preisbereich. Preise müssen aktuell geprüft werden, sonst wäre die Liste für Kaufentscheidung zu schwach.

### 12. Assistent

Erstellt: [Excel-Liste myGEKKO Slide 2 Video-Klingel Kompatibilität & Preise](sandbox:/mnt/data/myGEKKO_Slide2_Video_Klingel_Kompatibilitaet_Preisliste.xlsx)

Inhalt:
- **Übersicht**: klare Kaufentscheidung und Ausschlusslogik
- **Varianten**: 31 Optionen inkl. 2N, DoorBird, Drittanbieter und nicht empfohlene Cloud-Klingeln
- **Bewertung**: Priorisierung nach Kompatibilität, Preis, Risiko und Einsatzfall
- **Quellen**: direkte URLs zu myGEKKO, 2N/DoorBird-Kompatibilität und Preisquellen

Kernaussage der Liste:
1. **2N IP Solo mit Kamera** bleibt die beste Ersatzwahl.
2. **2N IP Verso 2.0** nur bei Modulen/Fingerprint/RFID/Keypad.
3. **DoorBird D1101V/D2101FV** bei stärkerem App-Fokus.
4. **Akuvox/Fanvil/Grandstream** nur als technische Drittanbieter-Option mit vorherigem SIP/RTSP-Test.
5. **Ring/Nest/Eufy** nicht für saubere myGEKKO-Slide-2-Integration einplanen.

### 13. Benutzer

Ich hätte gern eine Zusammensetzung der Liste oder Ergänzung mit den Preisen der jeweiligen Kringel oder Freisprecheinrichtung wie auch immer gerne auch die von Ring Nest oder Ei

### 14. Assistent

Die Erweiterung wird als zusätzliche Kalkulationssicht aufgebaut: Außenstation, Innen-/Gong-Komponente, Zubehör, geschätzter Systempreis und Integrationsrisiko getrennt. Preise werden als Marktpreise mit Quellen-URL im Sheet abgelegt.

### 15. Assistent

Ergänzte Excel-Datei erstellt:

[Download: myGEKKO Slide 2 Video-Klingel Kompatibilität & Preisliste ergänzt](sandbox:/mnt/data/myGEKKO_Slide2_Video_Klingel_Kompatibilitaet_Preisliste_ergaenzt.xlsx)

Ergänzt wurden drei neue Sheets:

1. **Preiszusammensetzung_2026**
   - Außenstation
   - Innenstation / Freisprecheinrichtung / Gong
   - Zubehör / Module
   - Abo-/Cloud-Kosten als eigene Spalte
   - Systempreis min/max als Formel
   - Preisquelle je Zeile

2. **Kaufentscheidung**
   - klare Rangfolge
   - 2N IP Solo weiter auf Platz 1
   - DoorBird als offizielle Alternative
   - Akuvox/Fanvil/Grandstream als technische Testkandidaten
   - Ring/Nest/eufy/Aqara/Arlo als separate App-Systeme, nicht als saubere myGEKKO-Lösung

3. **Quellen_Preise_2026**
   - alle Preisquellen als direkte URLs

Preisstand: **31.05.2026**.  
Beispiele aus der Aktualisierung: 2N IP Solo AP ab **938,71 €**, 2N IP Solo UP ab **976,46 €**, 2N IP Verso 2.0 ab **1.094,18 €**, DoorBird D1101V ab **486,19 €**, Reolink PoE ab **79,00 €**, Ring Battery Video Doorbell Plus ab **74,95 €**, Google Nest Doorbell ab **99,99 €**, eufy E340 ab **117,05 €**. citeturn204033search0turn204033search1turn568105search1turn568105search3turn585895search0turn742436search5turn742436search4turn742436search2

### 16. Benutzer

Doorbird d1101v

### 17. Assistent

Ich ordne den DoorBird D1101V als konkrete Auswahl ein: myGEKKO-Kompatibilität, benötigte Zusatzteile, Preislogik, Risiken und Kaufvariante.

### 18. Assistent

## DoorBird D1101V für myGEKKO Slide 2

**Bewertung:** brauchbare offizielle Alternative, aber nicht meine erste Wahl gegenüber 2N IP Solo.

```text
DoorBird D1101V
→ LAN/PoE oder WLAN
→ DoorBird App
→ myGEKKO Sprechstelle / SIP
→ myGEKKO Video
→ Türöffner möglich
```

## Kompatibilität

myGEKKO führt die **DoorBird Außensprechstelle D1101V, 1 Taste, Aufputz, RJ45** in der eigenen DoorBird-Anleitung. Dort wird auch die SIP-Nummer der DoorBird-Sprechstelle für die Einbindung beschrieben. citeturn293369search14

DoorBird selbst beschreibt die D1101V Unterputz als IP-Video-Türstation, die eigenständig oder in eine Smart-Home-Plattform integriert werden kann. citeturn293369search3

## Aktuelle Preisorientierung

| Variante | Preis ab | Bewertung |
|---|---:|---|
| DoorBird D1101V Smart-Home Station | ca. **481,56 €** | realistische Basis für Aufputz-Variante |
| DoorBird D1101V graphitschwarz | ca. **481,56 €** | günstigste gefundene Variante |
| DoorBird D1101V silver | ca. **516,15 €** | Standardoptik |
| DoorBird D1101V graphite | ca. **570,78 €** | teurer |
| DoorBird D1101V anthrazit | ca. **587,91 €** | teurer |
| DoorBird D1101V bronze | ca. **645,17 €** | teuerste Optik |
| DoorBird D1101V Messing-Optik | ca. **668,53 €** | Premiumoptik |

Preise laut Idealo-Listings, Stand heute geprüft. citeturn293369search0turn293369search4turn293369search16

## Achtung bei Unterputz-Preis

Ein Suchergebnis zeigt eine **DoorBird D1101V Unterputz IP Video Türsprechanlage ab ca. 69–92 €**. Das ist preislich auffällig niedrig und wahrscheinlich nicht das vollständige Gerät, sondern Zubehör/Einbaurahmen/Komponente oder fehlerhafte Händlerzuordnung. Für die Kalkulation nicht als belastbaren Gesamtpreis verwenden. citeturn293369search2

## Technische Eckdaten relevant für myGEKKO

| Punkt | DoorBird D1101V |
|---|---|
| Türstation | ja |
| Video | ja |
| Audio | ja |
| 1 Klingeltaste | ja |
| PoE | ja, 802.3af |
| LAN | ja, 10/100 Base-T |
| WLAN | ja, 2,4 GHz |
| RTSP/RTP | ja |
| HTTP/HTTPS | ja |
| myGEKKO-Nähe | offiziell dokumentiert |
| App-Komfort | hoch |

Das DoorBird-Datenblatt nennt u. a. **PoE 802.3af**, **10/100 Base-T**, **2,4-GHz-WLAN** sowie Protokolle wie **HTTP, HTTPS, RTSP, RTP, TCP, UDP**. citeturn293369search10

## Benötigte Zusatzteile

| Bauteil | Pflicht | Preis grob |
|---|---:|---:|
| DoorBird D1101V | ja | ca. 482–669 € |
| PoE-Switch oder PoE-Injektor | ja, wenn kein PoE vorhanden | ca. 20–80 € |
| Netzwerkkabel CAT5e/CAT6 | ja | abhängig von Bestand |
| Türöffner-Relais/Anschlussmaterial | falls Türöffner genutzt wird | ca. 20–100 € |
| Innenstation | nein, wenn myGEKKO als Innenstelle genutzt wird | optional |
| DoorBird App | optional/nützlich | abhängig vom DoorBird-Modell/Service |

## Systempreis realistisch

```text
Minimal:
DoorBird D1101V + vorhandenes LAN/PoE + myGEKKO
≈ 500–700 €

Mit PoE-Zubehör und sauberem Türöffneranschluss:
≈ 600–850 €

Mit Elektriker/Montage:
≈ 800–1.300 €+
```

## Entscheidung gegen 2N IP Solo

| Kriterium | DoorBird D1101V | 2N IP Solo |
|---|---:|---:|
| myGEKKO-Kompatibilität | gut | sehr gut |
| App-Komfort | besser | mittel |
| Preis | niedriger | höher |
| professionelle Gebäudetechnik | gut | stärker |
| Erweiterbarkeit | begrenzt | begrenzt |
| Türöffner/SIP/Video | ja | ja |
| Risiko Cloud/App-Abhängigkeit | höher | niedriger |

## Empfehlung

**DoorBird D1101V nehmen**, wenn diese Punkte wichtiger sind:

```text
App-Komfort
Smartphone-Push
günstigerer Einstiegspreis
1 Klingeltaste reicht
bestehendes LAN/PoE vorhanden
myGEKKO soll eingebunden werden, aber nicht alleiniger Bedienkanal sein
```

**2N IP Solo nehmen**, wenn diese Punkte wichtiger sind:

```text
maximal saubere lokale Gebäudetechnik
weniger App-/Cloud-Fokus
myGEKKO als Hauptsystem
professionellere SIP-/Türkommunikationslogik
```

Für deinen Fall ist die DoorBird D1101V eine valide Wahl, aber die Entscheidung lautet:

```text
Preis/App-Komfort priorisiert → DoorBird D1101V
Robuste myGEKKO-Integration priorisiert → 2N IP Solo
```

### 19. Assistent

Ich behandle „n2“ als **2N**, weil deine bisherige Architektur 2N/myGEKKO betrifft. Entscheidend ist jetzt nicht nur Ersatzgerät, sondern **Mehrfamilienhaus-Logik: Anzahl Parteien/Ruftasten, bestehende Module, Einbauform und Türöffneranschluss**.

### 20. Benutzer

aktuell habe ich eine n2 mehrfamilienhaus im einsatz

### 21. Assistent

Dann ist die Lage klarer: **DoorBird D1101V ist wahrscheinlich der falsche Ersatz**, wenn du aktuell eine **2N-Anlage für ein Mehrfamilienhaus** nutzt.

## Korrektur der Empfehlung

Bisherige Empfehlung **2N IP Solo** gilt nur für:

```text
Einfamilienhaus
1 Klingeltaste
1 Zielruf / 1 Wohneinheit
einfache Türkommunikation
```

Bei dir gilt aber:

```text
Mehrfamilienhaus
mehrere Parteien / mehrere Ruftasten
bestehende 2N-Logik
myGEKKO Slide 2 als Innensprechstelle
wahrscheinlich mehrere Rufziele
```

Damit verschiebt sich die Empfehlung.

## Wahrscheinlich passendere Ersatzgeräte

| Rang | Gerät | Bewertung |
|---:|---|---|
| 1 | **2N IP Verso / IP Verso 2.0** | Beste Ersatzlogik für Mehrfamilienhaus |
| 2 | **2N IP Style** | Premiumlösung mit Touchdisplay |
| 3 | **2N IP Base mit 2 Tasten** | Nur bei sehr kleiner Anlage |
| 4 | **2N IP Force** | Robust, vandalismussicher |
| 5 | **DoorBird Mehrparteien-Modelle** | möglich, aber Systemwechsel |
| 6 | **DoorBird D1101V** | nur 1 Partei, daher für Mehrfamilienhaus meist ungeeignet |

myGEKKO nennt 2N-Modelle wie **2N IP Verso, IP Solo, IP Base, IP Vario, IP Force, IP Uni, IP Video Kit und IP Audio Kit** als kompatibel; die VoIP-Anbindung dient der Video-Gegensprechanlage mit myGEKKO Displaycontroller. citeturn676361search0turn676361search3

## Hauptentscheidung

### Wenn du die bestehende 2N-Mehrfamilienhausstruktur erhalten willst

Nimm:

```text
2N IP Verso / 2N IP Verso 2.0
```

Grund:
- mehrere Klingeltasten möglich
- Namensmodule möglich
- RFID/Keypad/Fingerprint je nach Ausbau möglich
- gleiche Systemfamilie
- geringere Umstellungsrisiken
- myGEKKO-kompatibel
- bessere Chance, vorhandene Konfiguration teilweise nachzubauen

2N IP Verso kann mit Ruftastenmodulen erweitert werden; 5-Ruftasten-Module sind handelsüblich und genau für solche Mehrparteien-Setups gedacht. citeturn676361search4turn676361search7

### Wenn du nur deine eigene Wohneinheit ersetzen willst

Dann kann **2N IP Solo** passen, aber nur wenn die bestehende Mehrparteienlogik irrelevant wird.

```text
2N IP Solo
= 1 Taste
= 1 Partei
= kein echter Mehrfamilienhaus-Ersatz
```

## DoorBird D1101V Einordnung

**DoorBird D1101V nicht als direkter Ersatz für eine 2N-Mehrfamilienhausanlage einplanen.**

Grund:

| Punkt | DoorBird D1101V |
|---|---|
| Ruftasten | 1 |
| Mehrfamilienhaus | nein, nur sehr eingeschränkt |
| Systemwechsel von 2N | ja |
| myGEKKO-kompatibel | ja, aber andere Logik |
| Risiko bei Ersatz | mittel bis hoch |

DoorBird ist mit myGEKKO grundsätzlich integrierbar; myGEKKO unterstützt DoorBird-Sprechstellen und laut DoorBird gibt es eine aktuelle myGEKKO-Integrationsanleitung. citeturn676361search11turn676361search8  
Das löst aber nicht automatisch dein Mehrfamilienhausproblem.

## Richtige Ersatzlogik

```text
Aktuell defekt: 2N Mehrfamilienhausanlage
↓
Nicht 1:1 ersetzen durch DoorBird D1101V
↓
Ersatzklasse bestimmen:
- 2N IP Verso / Verso 2.0
- 2N IP Style
- 2N IP Force, falls robust/vandalensicher nötig
```

## Preislogik grob

| Variante | Erwartbarer Systempreis |
|---|---:|
| 2N IP Solo | ca. 900–1.200 € |
| 2N IP Verso Basis | ca. 1.000–1.400 € |
| 2N IP Verso mit mehreren Tasten/Modulen | ca. 1.300–2.500 €+ |
| 2N IP Style | ca. 2.000–3.500 €+ |
| DoorBird D1101V | ca. 500–850 € |
| DoorBird Mehrparteienlösung | ca. 900–2.500 €+ |

## Konkrete Empfehlung

Für deine Situation:

```text
Primär prüfen:
2N IP Verso / 2N IP Verso 2.0

Nicht priorisieren:
DoorBird D1101V
2N IP Solo
Ring
Nest
eufy
```

## Wichtigste Folge für die Excel-Liste

Die Liste sollte jetzt nicht mehr nach „Video-Klingel allgemein“ priorisiert werden, sondern nach:

```text
Ersatz für bestehende 2N-Mehrfamilienhausanlage
+ myGEKKO Slide 2 kompatibel
+ mehrere Ruftasten/Rufziele
+ Türöffner
+ SIP/VoIP
+ Video
+ möglichst geringe Umverdrahtung
```

Damit wäre **2N IP Verso / Verso 2.0** die neue Referenz, nicht mehr 2N IP Solo.

### 22. Benutzer

wie richte ich diese ein ip?

### 23. Assistent

Ich gehe vom Setup **2N Mehrfamilienhaus-Türstation + myGEKKO Slide 2 + LAN/PoE** aus. Ziel: feste IP vergeben, Gerät erreichbar machen, danach SIP/Video in myGEKKO eintragen.

### 24. Assistent

## Ziel

Die 2N-Türstation bekommt eine **feste IP-Adresse**, damit myGEKKO sie dauerhaft findet.

Empfohlene Logik:

```text
2N Türstation:     192.168.178.60
myGEKKO Slide 2:   192.168.178.20
Router/FritzBox:   192.168.178.1
Subnetzmaske:      255.255.255.0
Gateway:           192.168.178.1
DNS:               192.168.178.1
```

IP-Adressen nur als Beispiel. Der Bereich muss zu deinem Heimnetz passen.

## Schritt 1: 2N an Netzwerk anschließen

```text
2N Türstation
→ LAN-Kabel
→ PoE-Switch oder PoE-Injektor
→ Router/FritzBox-Netzwerk
```

Die 2N muss im gleichen Netzwerk hängen wie dein PC und später auch der myGEKKO Slide 2.

## Schritt 2: aktuelle IP-Adresse finden

### Variante A: über Router/FritzBox

In der FritzBox:

```text
Heimnetz
→ Netzwerk
→ Netzwerkverbindungen
→ Gerät suchen: 2N / IP Intercom / unbekanntes LAN-Gerät
```

Dort steht die aktuelle IP-Adresse.

### Variante B: über 2N Network Scanner

2N stellt dafür den **2N IP Network Scanner** bereit. Damit lassen sich 2N-Geräte im LAN finden; das Tool zeigt IP-Adresse, Name, Seriennummer und Firmware an. citeturn582995search3turn582995search10

Ablauf:

```text
1. 2N Network Scanner installieren
2. Programm starten
3. 2N-Gerät suchen lassen
4. IP-Adresse notieren
5. Per Browser öffnen
```

### Variante C: Ansage der IP-Adresse

Viele 2N IP-Intercoms können ihre IP-Adresse über den eingebauten Lautsprecher ansagen. Wenn **0.0.0.0** angesagt wird, hat das Gerät keine DHCP-Adresse erhalten. citeturn582995search7

## Schritt 3: Weboberfläche öffnen

Im Browser eingeben:

```text
http://IP-DER-2N
```

Beispiel:

```text
http://192.168.178.60
```

Bei älteren/Default-Konfigurationen kann der Login so sein:

```text
Benutzer: Admin
Passwort: 2n
```

2N beschreibt die Konfiguration über die Weboberfläche und nennt bei einigen Geräten den Standardzugang **Admin / 2n**; bei neueren oder bereits eingerichteten Anlagen kann das Passwort geändert oder ein Initial-Setup aktiv sein. citeturn582995search1

## Schritt 4: feste IP in der 2N setzen

In der 2N-Weboberfläche:

```text
System
→ Network / Netzwerk
→ DHCP deaktivieren
→ feste IP-Adresse eintragen
```

Eintragen:

```text
IP-Adresse:      192.168.178.60
Subnetzmaske:    255.255.255.0
Gateway:         192.168.178.1
DNS Server:      192.168.178.1
```

Danach:

```text
Speichern
→ Gerät startet neu
→ neue IP im Browser öffnen
```

2N beschreibt diese Logik offiziell: DHCP deaktivieren, IP-Adresse, Subnetzmaske, Gateway und DNS eintragen, speichern; danach startet das Gerät neu. citeturn582995search4turn582995search11

## Schritt 5: IP in der FritzBox reservieren

Zusätzlich in der FritzBox festlegen:

```text
Heimnetz
→ Netzwerk
→ 2N Gerät
→ Bearbeiten
→ Diesem Netzwerkgerät immer die gleiche IPv4-Adresse zuweisen
```

Das verhindert IP-Konflikte.

Wichtig: Entweder saubere DHCP-Reservierung im Router oder statische IP im Gerät. Beides ist möglich, aber die IP darf nicht doppelt vergeben werden.

## Schritt 6: Erreichbarkeit testen

Am PC:

```text
Browser:
http://192.168.178.60
```

Optional in Windows Eingabeaufforderung:

```cmd
ping 192.168.178.60
```

Erwartung:

```text
Antwort von 192.168.178.60
```

Wenn kein Ping kommt, kann die Weboberfläche trotzdem erreichbar sein, falls ICMP blockiert ist. Browser-Test ist wichtiger.

## Schritt 7: myGEKKO vorbereiten

In myGEKKO brauchst du später diese Werte:

```text
2N IP-Adresse:       192.168.178.60
SIP-Benutzer:        z. B. 101 oder 2N
SIP-Ziel myGEKKO:    IP oder SIP-Nummer vom Slide 2
Video-URL:           Snapshot/MJPEG/RTSP der 2N
Türöffner:           Relaisausgang / HTTP-Befehl / 2N-Relais
```

myGEKKO führt 2N als kompatible Haussprechstelle und beschreibt die Einbindung über VoIP/Sprechstelle. citeturn582995search18

## Wenn du nicht auf die Weboberfläche kommst

### Fall 1: IP unbekannt

```text
2N Network Scanner nutzen
oder
FritzBox Heimnetzliste prüfen
```

### Fall 2: Gerät bekommt keine IP

Symptom:

```text
0.0.0.0
```

Ursachen:

```text
kein DHCP aktiv
falsches Netzwerk
PoE/Versorgung instabil
Kabel/Switch-Port defekt
VLAN trennt Gerät vom Router
```

### Fall 3: Gerät steht auf falschem statischem Netz

Beispiel:

```text
2N: 192.168.1.100
dein Netz: 192.168.178.x
```

Dann PC kurzfristig auf dasselbe Netz setzen:

```text
PC IP:        192.168.1.50
Subnetz:      255.255.255.0
Gateway:      leer oder 192.168.1.1
```

Dann öffnen:

```text
http://192.168.1.100
```

Danach 2N auf dein echtes Netz umstellen.

2N nennt bei fehlendem DHCP für manche Geräte den statischen Default-Zugriff über **192.168.1.100**. citeturn582995search1turn582995search6

### Fall 4: DHCP/statisch per Taste umschalten

Bei mehreren 2N IP-Modellen kann man durch **15× Drücken der Ruftaste** zwischen DHCP und statischer IP umschalten. Bei der 2N IP Solo ist diese Methode offiziell beschrieben; je nach Mehrfamilienhausmodell/Modul muss das konkrete Modell geprüft werden. citeturn582995search12

## Empfohlene feste Adressierung

```text
Router/FritzBox:       192.168.178.1
myGEKKO Slide 2:       192.168.178.20
2N Türstation:         192.168.178.60
weitere 2N Module:     192.168.178.61–69
Kameras:               192.168.178.70–89
Smart Home Geräte:     192.168.178.100–199
```

## Danach kommt die eigentliche Integration

Reihenfolge:

```text
1. 2N feste IP setzen
2. 2N Weboberfläche erreichbar
3. myGEKKO IP prüfen
4. SIP/VoIP konfigurieren
5. Ruftasten/Rufziele einrichten
6. Video-Stream in myGEKKO eintragen
7. Türöffner testen
```

Nicht mit SIP oder Video anfangen, bevor die IP stabil ist.

### 25. Assistent

Ich beschreibe die Einrichtung als Ablauf im Slide 2: zuerst Netzwerk/IP, dann System „Sprechstelle“, danach Videoquelle und Türöffner. Ich trenne 2N-direkt und SIP/FritzBox, weil beide in myGEKKO unterschiedlich wirken.

### 26. Benutzer

wie richte ich es in mygekko slide 2 ein

### 27. Assistent

## Annahme

Du richtest eine **2N IP Mehrfamilienhaus-Sprechstelle** an einem **myGEKKO Slide 2** ein.

Ziel:

```text
2N Außensprechstelle
→ ruft myGEKKO Slide 2 per VoIP/SIP
→ myGEKKO zeigt Kamerabild
→ myGEKKO kann optional Türöffner auslösen
```

myGEKKO unterstützt 2N-Sprechstellen über das lokale Netzwerk; Kamera, Mikrofon, bidirektionale Kommunikation und Türöffnerfunktion sind vorgesehen. citeturn117288search1

---

# 1. Voraussetzungen

## Netzwerkdaten festlegen

Beispiel:

```text
Router / FritzBox:       192.168.178.1
myGEKKO Slide 2:         192.168.178.20
2N Außensprechstelle:    192.168.178.60
SIP-Nummer myGEKKO:      2000
SIP-Nummer 2N:           2001
```

Wichtig:

```text
2N und myGEKKO müssen im gleichen Netzwerk erreichbar sein.
Die IP-Adressen dürfen nicht doppelt vergeben sein.
myGEKKO braucht eine feste IP.
2N braucht eine feste IP.
```

myGEKKO beschreibt die 2N-Umsetzung grundsätzlich in drei Schritten: alle Sprechstellen ins gleiche Netzwerk bringen, jedem Controller einen Namen und eine individuelle Nummer geben, dann die Controllerdaten über den Browser an die 2N-Sprechstelle übermitteln. citeturn117288search8

---

# 2. Am myGEKKO als Konfigurator anmelden

Am Slide 2:

```text
Zahnrad / Einstellungen
→ als Konfigurator anmelden
```

Danach in die Systemübersicht wechseln.

---

# 3. System „Telefonie“ aktivieren

Am myGEKKO Slide 2:

```text
Systemübersicht
→ Telefonie
→ Zahnrad oben rechts
→ IO-Konfiguration
```

Dann setzen:

```text
VoIP Client:      Aktiv
Anzeigename:      myGEKKO
SIP Benutzername: 2000
```

myGEKKO beschreibt für Direct Call genau diese Logik: Im System **Telefonie** muss der Controller einen Anzeigenamen und eine SIP-Nummer erhalten, damit die 2N-Außensprechstelle den Controller erreichen kann. citeturn117288search0

Beispiel:

```text
myGEKKO Slide 2
IP-Adresse:       192.168.178.20
Anzeigename:      myGEKKO
SIP Benutzername: 2000
```

Diese SIP-Nummer ist später das Rufziel in der 2N.

---

# 4. System „Sprechstelle“ einrichten

Am myGEKKO:

```text
Systemübersicht
→ Sprechstelle
→ neues Element / vorhandenes Element öffnen
→ Zahnrad / IO-Konfiguration
```

Eintragen:

```text
Typ / Schnittstelle:     2N
Betriebsart:             Direct Call oder SIP-Server
IP-Adresse 2N:           192.168.178.60
SIP-Nummer 2N:           2001
Türöffner:               optional
```

myGEKKO unterscheidet bei 2N zwischen **Direct Call** und **SIP-Server**. Direct Call bedeutet: 2N ruft den myGEKKO direkt über dessen IP an. SIP-Server bedeutet: FritzBox oder SIP-Server vermittelt den Ruf. citeturn117288search11

## Für deinen Fall zuerst Direct Call verwenden

```text
2N ruft direkt:
sip:2000@192.168.178.20
```

Vorteile:

```text
weniger Komponenten
lokal
einfacher Fehlerausschluss
```

SIP-Server/FritzBox erst verwenden, wenn zusätzlich Telefone, Smartphones oder mehrere Innenstellen klingeln sollen.

---

# 5. Video im myGEKKO einrichten

Am myGEKKO:

```text
Systemübersicht
→ Video
→ neues Video-Element erstellen
→ Zahnrad oben rechts
→ Parametereinstellungen
```

Bildpfad eintragen.

Für 2N laut myGEKKO-Beispiel:

```text
JPG:http://192.168.178.60/api/camera/snapshot?width=640&height=480
```

oder:

```text
MJPG:http://192.168.178.60/api/camera/snapshot?width=640&height=480&fps=15
```

myGEKKO dokumentiert genau diese 2N-Bildpfade für das System **Video**. Danach soll in der IO-Konfiguration die Zusatzfunktion **VoIP-Link** gesetzt werden, damit bei eingehendem Anruf das passende Kamerabild als Vollbild erscheint. citeturn117288search13

Dann:

```text
Video
→ Zahnrad
→ IO-Konfiguration
→ Zusatzfunktion: VoIP-Link
→ Sprechstelle 2N zuordnen
```

myGEKKO Video unterstützt u. a. JPG-Stream, MJPEG, CGI sowie H.264/H.265 über RTSP. citeturn117288search2

---

# 6. 2N-Weboberfläche konfigurieren

Am PC im Browser:

```text
http://192.168.178.60
```

Falls Zertifikatswarnung kommt: bestätigen.

myGEKKO empfiehlt für die 2N-Konfiguration den Browserzugriff über die IP-Adresse der 2N-Sprechstelle; die Oberfläche gilt u. a. für 2N IP Verso, Vario, Force, Uni, Video Kit, Audio Kit, Base und Solo. citeturn117288search7

## In der 2N einstellen

### 6.1 2N eigene SIP-Nummer

In der 2N:

```text
Services
→ Phone
→ Intercom Identity
```

Setzen:

```text
Phone Number / ID: 2001
```

Damit ist die Außensprechstelle selbst unter **2001** identifizierbar.

---

### 6.2 myGEKKO als Rufziel anlegen

In der 2N:

```text
Directory
→ Users
→ Benutzer anlegen
```

Beispiel:

```text
Name:          myGEKKO
Phone Number:  sip:2000@192.168.178.20
```

myGEKKO beschreibt bei Direct Call genau dieses Schema: In der 2N wird unter **Directory → Users** der myGEKKO SIP User inklusive IP-Adresse eingetragen, z. B. `sip:2000@192.168.2.252`. citeturn117288search4

---

### 6.3 Klingeltaste zuweisen

In der 2N:

```text
Hardware
→ Buttons
oder
Directory / Phone Book
→ Taste / Benutzer zuweisen
```

Zuweisen:

```text
Taste Wohnung Markus
→ Benutzer myGEKKO
→ Rufziel sip:2000@192.168.178.20
```

Bei Mehrfamilienhaus:

```text
Taste 1 → Wohnung 1 / SIP-Ziel 2000
Taste 2 → Wohnung 2 / anderes Ziel
Taste 3 → Wohnung 3 / anderes Ziel
```

Wichtig: Jede Innenstelle braucht eine eigene SIP-Nummer. myGEKKO nennt als Beispiel mehrere Innenstellen mit unterschiedlichen SIP-Benutzernamen, z. B. 2000, 2001 usw. citeturn117288search4

---

# 7. Türöffner einrichten

Es gibt zwei Varianten.

## Variante A: Türöffner direkt über 2N

```text
myGEKKO sendet Befehl
→ 2N schaltet internes Relais
→ Türöffner öffnet
```

Diese Variante ist meistens sauber, wenn der Türöffner bereits an der 2N hängt.

## Variante B: Türöffner über myGEKKO-IO

```text
myGEKKO schaltet eigenes Relais
→ Türöffner öffnet
```

Diese Variante ist sinnvoll, wenn der Türöffner bereits am Gebäuderegler hängt.

Für die Ansteuerung des 2N-Türöffnerkontakts beschreibt myGEKKO, dass im myGEKKO OS eine **HTTP IO-Station** angelegt wird. citeturn117288search10

Minimal prüfen:

```text
Türöffner-Spannung: 12 V oder 24 V?
AC oder DC?
Relais potentialfrei?
Türöffner an 2N oder an myGEKKO?
```

Fehler hier kann Hardware beschädigen. Keine Spannung blind auf Relais legen.

---

# 8. Testablauf

## Test 1: Netzwerk

Am PC:

```cmd
ping 192.168.178.60
ping 192.168.178.20
```

Browser:

```text
http://192.168.178.60
```

Erwartung:

```text
2N-Weboberfläche öffnet sich.
```

---

## Test 2: Video

Am myGEKKO:

```text
System Video öffnen
→ 2N-Kamera auswählen
```

Erwartung:

```text
Kamerabild sichtbar.
```

Falls kein Bild:

```text
Bildpfad falsch
Login für Kamera nötig
HTTP/HTTPS blockiert
2N API deaktiviert
falsche IP
```

---

## Test 3: Klingeln

An der 2N Taste drücken.

Erwartung:

```text
myGEKKO klingelt
Kamerabild erscheint
Sprechen/Hören funktioniert
```

Falls myGEKKO nicht klingelt:

```text
SIP Benutzername am myGEKKO falsch
Rufziel in 2N falsch
IP vom myGEKKO falsch
VoIP Client nicht aktiv
2N und myGEKKO nicht im gleichen Netz
Firewall/VLAN blockiert SIP/RTP
```

---

## Test 4: Audio

Prüfen:

```text
Ton von außen nach innen
Ton von innen nach außen
Lautstärke
Echo
Mikrofon
```

Wenn Klingeln funktioniert, aber kein Ton:

```text
RTP blockiert
Codec falsch
Firewall/VLAN
SIP über UDP/TCP inkonsistent
```

---

## Test 5: Türöffner

Nur testen, wenn Verdrahtung klar ist.

```text
myGEKKO Türöffner drücken
→ Relais schaltet
→ Türöffner summt/öffnet
```

---

# 9. Mehrfamilienhaus-spezifische Logik

Wenn deine 2N mehrere Wohnungen bedient:

```text
Nicht alle Tasten auf denselben myGEKKO legen.
Nicht dieselbe SIP-Nummer mehrfach vergeben.
Jede Innenstelle bekommt eigene Nummer.
Jede Taste bekommt eindeutiges Rufziel.
```

Beispiel:

```text
Wohnung 1:
myGEKKO IP 192.168.178.20
SIP 2000
2N Taste 1 → sip:2000@192.168.178.20

Wohnung 2:
Innenstelle IP 192.168.178.21
SIP 2001
2N Taste 2 → sip:2001@192.168.178.21

Wohnung 3:
Innenstelle IP 192.168.178.22
SIP 2002
2N Taste 3 → sip:2002@192.168.178.22
```

myGEKKO weist darauf hin, dass bei mehreren Innenstellen jede Innensprechstelle einen unterschiedlichen SIP-Benutzernamen bekommen muss und die Videobildkonfiguration auf jedem myGEKKO erfolgen muss. citeturn117288search4

---

# 10. Minimal-Konfiguration für deinen Slide 2

Diese Werte als Startpunkt nehmen:

```text
myGEKKO Slide 2
IP:                 192.168.178.20
VoIP Client:        Aktiv
Anzeigename:        myGEKKO
SIP Benutzername:   2000
```

```text
2N Außensprechstelle
IP:                 192.168.178.60
SIP Nummer:         2001
Rufziel:            sip:2000@192.168.178.20
```

```text
myGEKKO Video
Typ:                2N Kamera / Video
Bildpfad JPG:        JPG:http://192.168.178.60/api/camera/snapshot?width=640&height=480
Zusatzfunktion:     VoIP-Link
```

```text
Taste an 2N
Taste Wohnung:      Benutzer myGEKKO
Rufziel:            sip:2000@192.168.178.20
```

## Reihenfolge einhalten

```text
1. myGEKKO feste IP prüfen
2. 2N feste IP prüfen
3. myGEKKO Telefonie aktivieren
4. myGEKKO Sprechstelle anlegen
5. 2N Rufziel auf myGEKKO setzen
6. Video in myGEKKO anlegen
7. VoIP-Link setzen
8. Klingeltest
9. Audio-Test
10. Türöffner-Test
```

### 28. Benutzer

{"asset_pointer": "sediment://file_000000006ec87246ae4ab970e48d2cc6", "content_type": "image_asset_pointer", "fovea": null, "height": 617, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 26780, "width": 803}

### 29. Assistent

Du bist aktuell im **myGEKKO System „Video“ → IO-Konfiguration** der Kamera **„Klingel“**.

Der relevante Fehler im Screenshot:

```text
Zusatzfunktion = Digital Output
```

Für die 2N-Türstation brauchst du hier normalerweise **nicht „Digital Output“**, sondern den **VoIP-Link** zur Sprechstelle.

## Richtig einstellen

In diesem Bildschirm:

```text
Video
→ Klingel
→ IO-Konfiguration
→ Zusatzfunktion
```

Dort ändern von:

```text
Digital Output
```

auf:

```text
VoIP-Link
```

Danach die passende **Sprechstelle / Telefonie-Verknüpfung** auswählen.

## Bedeutung der Felder im Screenshot

| Feld | Aktueller Wert | Bewertung |
|---|---:|---|
| Anzeige bei | DI | nur nötig bei digitalem Eingang |
| Aufzeichnung bei | DI | nur nötig bei Aufnahmeauslösung |
| Neue Aufzeichnung vorhanden | DO | nur Statusausgang |
| Zusatzfunktion | Digital Output | für Klingelbild falsch/prioritär nicht passend |
| Ausgang Zusatztaster | DO | nur für Zusatzbutton/Türöffner/Relais |
| Nachlaufzeit | leer | nur relevant bei Trigger/Output |

## Zielkonfiguration für 2N

Für die Kamera der 2N im Video-System:

```text
Zusatzfunktion: VoIP-Link
Videoquelle: JPG/MJPEG/RTSP der 2N
Verknüpfte Sprechstelle: 2N / Klingel
```

Typischer 2N Snapshot-Pfad:

```text
JPG:http://IP_DER_2N/api/camera/snapshot?width=640&height=480
```

Beispiel:

```text
JPG:http://192.168.178.60/api/camera/snapshot?width=640&height=480
```

## Was du als Nächstes machen musst

1. Im Feld **Zusatzfunktion** auf den grauen Bereich **Digital Output** tippen.
2. Auf **VoIP-Link** umstellen.
3. Die 2N-Sprechstelle auswählen.
4. Speichern.
5. Zurück zur Videoansicht.
6. Prüfen, ob das Kamerabild sichtbar ist.
7. Danach an der 2N klingeln.

## Erwartetes Ergebnis

```text
2N Klingeltaste gedrückt
→ myGEKKO Slide 2 klingelt
→ Video „Klingel“ öffnet sich automatisch
→ Kamerabild erscheint
→ Gespräch kann angenommen werden
```

Wenn **VoIP-Link nicht auswählbar** ist, fehlt vorher die Einrichtung unter:

```text
Systemübersicht
→ Telefonie
```

oder

```text
Systemübersicht
→ Sprechstelle
```

Dann ist das Video-System schon offen, aber die eigentliche Sprechstellen-/VoIP-Verknüpfung existiert noch nicht.

### 30. Benutzer

wird nichts angezeigt. Ich möchte klingeln und dann wird das bild an der slide 2 angezeigt. schritt für schritt anleitung für anfänger

### 31. Assistent

## Ziel

```text
Klingeltaste an 2N drücken
→ myGEKKO Slide 2 klingelt
→ Bild der 2N-Kamera erscheint automatisch
```

Wichtig: Das passiert nur, wenn **3 Dinge** funktionieren:

```text
1. Video-Bild der 2N funktioniert im myGEKKO Video-System
2. Telefonie/Sprechstelle funktioniert
3. Video ist per VoIP-Link mit der Sprechstelle verbunden
```

Du bist aktuell bei Punkt 3, aber Punkt 1 oder 2 scheint noch nicht sauber zu funktionieren.

---

# Schritt 1: IP-Adresse der 2N prüfen

Am PC im Browser öffnen:

```text
http://IP-DEINER-2N
```

Beispiel:

```text
http://192.168.178.60
```

Wenn die 2N-Weboberfläche nicht aufgeht, zuerst das Netzwerkproblem lösen. Dann kann myGEKKO kein Bild anzeigen.

---

# Schritt 2: Kamerabild der 2N direkt testen

Am PC im Browser testen:

```text
http://IP-DEINER-2N/api/camera/snapshot?width=640&height=480
```

Beispiel:

```text
http://192.168.178.60/api/camera/snapshot?width=640&height=480
```

## Ergebnis A: Bild wird angezeigt

Dann ist die Kamera grundsätzlich erreichbar.

Weiter mit Schritt 3.

## Ergebnis B: Login-Abfrage kommt

Dann braucht myGEKKO Benutzername/Passwort oder die 2N erlaubt den Kamera-API-Zugriff nicht anonym.

Dann in der 2N-Weboberfläche prüfen:

```text
Services / Dienste
→ HTTP API
→ Camera API / Kamera API
→ Zugriff erlauben
```

Für Anfänger zuerst mit Benutzer/Passwort arbeiten.

Bildpfad dann später in myGEKKO so verwenden:

```text
JPG:http://BENUTZER:PASSWORT@IP-DEINER-2N/api/camera/snapshot?width=640&height=480
```

Beispiel:

```text
JPG:http://admin:DEINPASSWORT@192.168.178.60/api/camera/snapshot?width=640&height=480
```

## Ergebnis C: Kein Bild / Fehler

Dann stimmt einer dieser Punkte nicht:

```text
IP falsch
2N nicht erreichbar
Kamera-API deaktiviert
Benutzer/Passwort fehlt
2N und myGEKKO nicht im gleichen Netz
```

Nicht in myGEKKO weitermachen, bevor der Browser-Test ein Bild liefert.

---

# Schritt 3: myGEKKO Videoquelle einrichten

Am Slide 2:

```text
Home
→ Video
→ Klingel
→ Zahnrad
→ Parametereinstellungen
```

Dort die Bildquelle eintragen.

Ohne Passwort:

```text
JPG:http://192.168.178.60/api/camera/snapshot?width=640&height=480
```

Mit Passwort:

```text
JPG:http://BENUTZER:PASSWORT@192.168.178.60/api/camera/snapshot?width=640&height=480
```

Danach speichern.

Zurück in die normale Videoansicht.

## Test

```text
Video
→ Klingel öffnen
```

Erwartung:

```text
Bild der Türstation ist sichtbar
```

Wenn hier kein Bild sichtbar ist, liegt das Problem noch bei der Videoquelle. Dann bringt Klingeln auch nichts.

---

# Schritt 4: Telefonie am myGEKKO aktivieren

Am Slide 2:

```text
Home
→ Einstellungen / Zahnrad
→ Systemübersicht
→ Telefonie
→ Zahnrad
→ IO-Konfiguration
```

Setzen:

```text
VoIP Client: aktiv
Anzeigename: myGEKKO
SIP Benutzername: 2000
```

Beispielwerte:

```text
myGEKKO IP:          192.168.178.20
SIP Benutzername:    2000
```

Merken:

```text
2000 = Nummer vom Slide 2
```

---

# Schritt 5: Sprechstelle in myGEKKO einrichten

Am Slide 2:

```text
Home
→ Systemübersicht
→ Sprechstelle
→ neue Sprechstelle oder vorhandene öffnen
→ Zahnrad
→ IO-Konfiguration
```

Eintragen:

```text
Typ:             2N
Name:            Klingel
IP-Adresse:      192.168.178.60
Betrieb:         Direct Call
```

Wenn es ein Feld für SIP/Rufnummer gibt:

```text
SIP Nummer 2N:   2001
```

Wichtig:

```text
myGEKKO = 2000
2N = 2001
```

---

# Schritt 6: 2N so einstellen, dass sie den Slide 2 anruft

Am PC:

```text
http://192.168.178.60
```

In der 2N-Weboberfläche:

```text
Directory / Telefonbuch
→ Users / Benutzer
→ Benutzer anlegen
```

Eintragen:

```text
Name:          myGEKKO Slide 2
Phone Number:  sip:2000@192.168.178.20
```

Dann Klingeltaste zuweisen:

```text
Hardware
→ Buttons / Tasten
→ Taste auswählen
→ Benutzer myGEKKO Slide 2 zuweisen
```

Bei Mehrfamilienhaus:

```text
Taste deiner Wohnung
→ sip:2000@192.168.178.20
```

Nicht alle Tasten ändern.

---

# Schritt 7: Klingeltest ohne Video

Jetzt an der 2N klingeln.

Erwartung:

```text
myGEKKO Slide 2 klingelt
```

## Wenn myGEKKO nicht klingelt

Prüfen:

```text
Ist myGEKKO IP korrekt?
Ist SIP Benutzername am myGEKKO wirklich 2000?
Steht in der 2N wirklich sip:2000@IP-DES-SLIDE?
Sind 2N und Slide im gleichen Netzwerk?
Ist Telefonie am Slide aktiv?
```

Erst wenn der Slide klingelt, weiter mit Schritt 8.

---

# Schritt 8: Video mit Telefonie verknüpfen

Jetzt zurück zu deinem Screenshot.

Am Slide 2:

```text
Home
→ Video
→ Klingel
→ Zahnrad
→ IO-Konfiguration
```

Dort:

```text
Zusatzfunktion
```

ändern von:

```text
Digital Output
```

auf:

```text
VoIP-Link
```

Danach die passende Sprechstelle auswählen:

```text
Sprechstelle: Klingel / 2N
```

Speichern.

---

# Schritt 9: Automatische Bildanzeige testen

Jetzt final testen:

```text
1. Am Slide 2 auf Home gehen
2. 2N Klingeltaste drücken
3. Warten
```

Erwartung:

```text
Slide 2 klingelt
Video „Klingel“ öffnet sich
Bild erscheint automatisch
Gespräch kann angenommen werden
```

---

# Fehlerdiagnose nach Symptom

## Symptom 1: In Video „Klingel“ wird nie ein Bild angezeigt

Problem liegt bei:

```text
Videoquelle
Snapshot-URL
Passwort
2N Kamera-API
IP-Adresse
```

Lösung:

```text
Browser-Test mit Snapshot-URL wiederholen.
Erst wenn der PC das Bild sieht, myGEKKO konfigurieren.
```

---

## Symptom 2: Bild ist in Video sichtbar, aber bei Klingeln kommt nichts

Problem liegt bei:

```text
Telefonie
SIP-Rufziel
Sprechstelle
VoIP-Link fehlt
```

Lösung:

```text
Erst Klingeln ohne Video testen.
Dann VoIP-Link setzen.
```

---

## Symptom 3: Slide klingelt, aber Bild öffnet nicht automatisch

Problem liegt bei:

```text
Video ist nicht mit Sprechstelle verknüpft
Zusatzfunktion steht falsch
falsches Videoelement verknüpft
```

Lösung:

```text
Video → Klingel → IO-Konfiguration → Zusatzfunktion → VoIP-Link
```

---

## Symptom 4: Bild erscheint, aber kein Ton

Problem liegt bei:

```text
SIP/RTP
Audio-Codec
Firewall/VLAN
Mikrofon/Lautsprecher
```

Für Direct Call sollte möglichst alles im gleichen LAN sein.

---

# Minimalwerte für deine Einrichtung

Diese Werte sauber übernehmen und nur IPs anpassen:

```text
myGEKKO Slide 2
IP:                 192.168.178.20
Telefonie aktiv:    ja
SIP Benutzername:   2000
```

```text
2N Türstation
IP:                 192.168.178.60
Rufziel:            sip:2000@192.168.178.20
```

```text
myGEKKO Video „Klingel“
Bildquelle:
JPG:http://192.168.178.60/api/camera/snapshot?width=640&height=480

Zusatzfunktion:
VoIP-Link

Verknüpfung:
Sprechstelle Klingel / 2N
```

## Reihenfolge strikt einhalten

```text
1. 2N-Weboberfläche erreichbar
2. 2N-Snapshot im Browser sichtbar
3. Bild im myGEKKO Video sichtbar
4. myGEKKO Telefonie aktiv
5. 2N ruft myGEKKO an
6. Slide klingelt
7. Video-Zusatzfunktion auf VoIP-Link stellen
8. Klingeln testen
```

Nicht bei Schritt 8 anfangen, solange Schritt 3 und 6 nicht funktionieren.

### 32. Assistent

Dann ist dein Netzwerk wahrscheinlich:

```text
FritzBox / Router: 192.168.2.1
Netzbereich:       192.168.2.x
Subnetzmaske:      255.255.255.0
Gateway:           192.168.2.1
DNS:               192.168.2.1
```

## Neue Beispielwerte für deine Einrichtung

Nimm nicht mehr `192.168.178.x`, sondern `192.168.2.x`.

```text
myGEKKO Slide 2:      192.168.2.20
2N Türstation:        192.168.2.60
FritzBox:             192.168.2.1
Subnetzmaske:         255.255.255.0
Gateway:              192.168.2.1
DNS:                  192.168.2.1
```

## Schritt 1: myGEKKO-IP prüfen

Am Slide 2:

```text
Einstellungen
→ Netzwerk
→ IP-Adresse prüfen
```

Sollte ungefähr so aussehen:

```text
IP-Adresse:     192.168.2.xx
Gateway:        192.168.2.1
Subnetzmaske:   255.255.255.0
```

Wenn dort `192.168.178.xx` oder `192.168.1.xx` steht, ist der Slide nicht im gleichen Netz wie deine FritzBox.

## Schritt 2: 2N-IP festlegen

Für die 2N Türstation verwenden:

```text
IP-Adresse:     192.168.2.60
Subnetzmaske:   255.255.255.0
Gateway:        192.168.2.1
DNS:            192.168.2.1
```

Danach im Browser testen:

```text
http://192.168.2.60
```

## Schritt 3: Kamerabild direkt testen

Im Browser am PC öffnen:

```text
http://192.168.2.60/api/camera/snapshot?width=640&height=480
```

Wenn Bild erscheint, ist die Kamera erreichbar.

Wenn Login kommt, später in myGEKKO mit Benutzer/Passwort:

```text
JPG:http://BENUTZER:PASSWORT@192.168.2.60/api/camera/snapshot?width=640&height=480
```

## Schritt 4: myGEKKO Videoquelle eintragen

Am Slide 2:

```text
Home
→ Video
→ Klingel
→ Zahnrad
→ Parametereinstellungen
```

Bildquelle ohne Login:

```text
JPG:http://192.168.2.60/api/camera/snapshot?width=640&height=480
```

Mit Login:

```text
JPG:http://BENUTZER:PASSWORT@192.168.2.60/api/camera/snapshot?width=640&height=480
```

## Schritt 5: Telefonie am myGEKKO

Am Slide 2:

```text
Systemübersicht
→ Telefonie
→ IO-Konfiguration
```

Setzen:

```text
VoIP Client:        Aktiv
Anzeigename:        myGEKKO
SIP Benutzername:   2000
```

Damit ist dein Slide unter dieser SIP-Adresse erreichbar:

```text
sip:2000@192.168.2.20
```

## Schritt 6: 2N Rufziel eintragen

In der 2N-Weboberfläche:

```text
Directory / Telefonbuch
→ Users / Benutzer
→ Benutzer deiner Wohnung
```

Rufziel eintragen:

```text
sip:2000@192.168.2.20
```

Die Klingeltaste deiner Wohnung muss diesem Benutzer zugewiesen sein.

## Schritt 7: Video mit Klingelruf verknüpfen

Am Slide 2:

```text
Video
→ Klingel
→ Zahnrad
→ IO-Konfiguration
→ Zusatzfunktion
```

Ändern auf:

```text
VoIP-Link
```

Dann die passende 2N-Sprechstelle auswählen.

## Zielkonfiguration komplett

```text
FritzBox:
192.168.2.1
```

```text
myGEKKO Slide 2:
IP:                192.168.2.20
SIP Benutzername:  2000
```

```text
2N Türstation:
IP:                192.168.2.60
Rufziel:           sip:2000@192.168.2.20
```

```text
myGEKKO Video „Klingel“:
Bildquelle:
JPG:http://192.168.2.60/api/camera/snapshot?width=640&height=480

Zusatzfunktion:
VoIP-Link
```

## Testreihenfolge

```text
1. http://192.168.2.60 öffnet die 2N-Weboberfläche
2. Snapshot-URL zeigt am PC ein Bild
3. myGEKKO Video „Klingel“ zeigt Bild
4. Klingeltaste ruft sip:2000@192.168.2.20
5. Slide 2 klingelt
6. Bild öffnet automatisch
```

Erst wenn Punkt 2 funktioniert, lohnt sich die myGEKKO-Videoeinrichtung.

### 33. Benutzer

ip fritzbox 192.168.2.1

### 34. Benutzer

{"asset_pointer": "sediment://file_000000007aec7243bc7c8be082e67094", "content_type": "image_asset_pointer", "fovea": null, "height": 1536, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 485481, "width": 1152}
{"asset_pointer": "sediment://file_00000000bad4720a88390a9ee77b7c00", "content_type": "image_asset_pointer", "fovea": null, "height": 2556, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 372350, "width": 1179}
Das ist die Sprechstelle

### 35. Assistent

Das Gerät auf dem Foto ist **keine 2N IP Solo**, sondern sehr wahrscheinlich eine ältere **2N Helios IP / 2N IP Vario** Türsprechstelle. Das passt zu deiner Aussage „2N Mehrfamilienhaus“.

Im FritzBox-Screenshot sieht man oben abgeschnitten vermutlich ein Gerät mit:

```text
192.168.2.37
```

Das könnte deine 2N-Sprechstelle sein. Jetzt systematisch prüfen.

# Schritt 1: 2N-IP bestätigen

Am PC oder Handy im gleichen WLAN/LAN öffnen:

```text
http://192.168.2.37
```

Falls das nicht geht:

```text
https://192.168.2.37
```

## Ergebnis bewerten

| Ergebnis | Bedeutung |
|---|---|
| 2N-Weboberfläche öffnet sich | IP stimmt |
| Login erscheint | IP stimmt |
| Seite nicht erreichbar | falsche IP oder Gerät blockiert |
| Zertifikatswarnung | normal bei HTTPS, fortfahren |

Wenn `192.168.2.37` nicht funktioniert, in der FritzBox nach Gerätenamen suchen wie:

```text
2N
Helios
IP Intercom
Axis
unbekanntes LAN-Gerät
```

# Schritt 2: Kamera direkt testen

Wenn `192.168.2.37` die richtige IP ist, teste im Browser:

```text
http://192.168.2.37/api/camera/snapshot?width=640&height=480
```

## Ergebnis

### Bild erscheint

Dann ist die Kamera erreichbar. Diese URL kommt später in myGEKKO.

### Login erscheint

Dann brauchst du Benutzer und Passwort der 2N.

Dann lautet die myGEKKO-URL später:

```text
JPG:http://BENUTZER:PASSWORT@192.168.2.37/api/camera/snapshot?width=640&height=480
```

Beispiel:

```text
JPG:http://admin:DEINPASSWORT@192.168.2.37/api/camera/snapshot?width=640&height=480
```

### Kein Bild

Dann kann es bei diesem älteren Modell ein anderer Kamerapfad sein. Danach zuerst Weboberfläche prüfen, nicht in myGEKKO raten.

# Schritt 3: myGEKKO Video einrichten

Am Slide 2:

```text
Home
→ Video
→ Klingel
→ Zahnrad
→ Parametereinstellungen
```

Bei **Bildquelle / URL / Kameraadresse** eintragen:

```text
JPG:http://192.168.2.37/api/camera/snapshot?width=640&height=480
```

Falls Benutzer/Passwort nötig:

```text
JPG:http://BENUTZER:PASSWORT@192.168.2.37/api/camera/snapshot?width=640&height=480
```

Dann speichern.

## Test

```text
Video
→ Klingel öffnen
```

Erwartung:

```text
Livebild / Standbild der Türstation sichtbar
```

Wenn hier kein Bild kommt, ist die Video-URL falsch oder der Zugriff auf die 2N-Kamera gesperrt.

# Schritt 4: myGEKKO Telefonie prüfen

Am Slide 2:

```text
Home
→ Systemübersicht
→ Telefonie
→ Zahnrad
→ IO-Konfiguration
```

Setzen:

```text
VoIP Client: Aktiv
Anzeigename: myGEKKO
SIP Benutzername: 2000
```

Wichtig: Deine Slide-2-IP brauchst du auch.

Beispiel:

```text
myGEKKO Slide 2: 192.168.2.20
SIP Nummer:      2000
```

Wenn du die IP vom Slide nicht kennst:

```text
myGEKKO
→ Einstellungen
→ Netzwerk
→ IP-Adresse ablesen
```

# Schritt 5: In der 2N den Slide als Rufziel eintragen

In der 2N-Weboberfläche:

```text
http://192.168.2.37
```

Dann ungefähr:

```text
Directory / Telefonbuch
→ Users / Benutzer
→ Benutzer deiner Klingeltaste öffnen
```

Dort als Rufziel eintragen:

```text
sip:2000@IP-DEINES-SLIDE
```

Beispiel:

```text
sip:2000@192.168.2.20
```

Dann die Taste „KLINGEL“ diesem Benutzer zuweisen.

Bei älteren 2N-Menüs kann es heißen:

```text
Phone Book
→ User
→ Number 1
```

oder:

```text
Hardware
→ Buttons
→ Taste
→ Benutzer zuweisen
```

# Schritt 6: Klingelruf testen

Jetzt außen auf die Klingeltaste drücken.

## Erwartung

```text
myGEKKO Slide 2 klingelt
```

Wenn der Slide nicht klingelt, ist das Problem noch **Telefonie/SIP**, nicht Video.

Prüfen:

```text
2N-Rufziel = sip:2000@IP-DEINES-SLIDE
myGEKKO Telefonie aktiv
Slide-IP korrekt
2N und Slide im selben Netz 192.168.2.x
```

# Schritt 7: Video automatisch beim Klingeln anzeigen

Erst wenn Schritt 3 und Schritt 6 funktionieren:

```text
Bild in Video sichtbar
Slide klingelt bei Tastendruck
```

Dann am Slide 2:

```text
Home
→ Video
→ Klingel
→ Zahnrad
→ IO-Konfiguration
```

Dort ändern:

```text
Zusatzfunktion
```

von:

```text
Digital Output
```

auf:

```text
VoIP-Link
```

Dann die passende Sprechstelle auswählen:

```text
Klingel / 2N / Telefonie
```

Speichern.

# Zielkonfiguration für dein Netz

```text
FritzBox:
192.168.2.1
```

```text
2N Türstation:
vermutlich 192.168.2.37
```

```text
myGEKKO Slide 2:
192.168.2.xx
SIP Benutzername: 2000
```

```text
2N Rufziel:
sip:2000@192.168.2.xx
```

```text
myGEKKO Videoquelle:
JPG:http://192.168.2.37/api/camera/snapshot?width=640&height=480
```

```text
myGEKKO Video Zusatzfunktion:
VoIP-Link
```

# Fehlerlogik

| Symptom | Ursache |
|---|---|
| Browser öffnet 2N nicht | falsche IP |
| Browser öffnet 2N, aber Snapshot nicht | Kamera-API/Passwort/Pfad |
| myGEKKO Video bleibt schwarz | Video-URL falsch |
| myGEKKO klingelt nicht | SIP-Rufziel falsch |
| myGEKKO klingelt, aber kein Bild | VoIP-Link fehlt/falsch |
| Bild sichtbar, aber kein Ton | SIP/RTP/Codec |

# Reihenfolge strikt einhalten

```text
1. 2N-IP sicher finden
2. 2N-Weboberfläche öffnen
3. Kamera-Snapshot im Browser testen
4. Bild in myGEKKO Video sichtbar machen
5. Telefonie im myGEKKO aktivieren
6. 2N-Rufziel auf Slide 2 setzen
7. Klingeltest
8. Video Zusatzfunktion auf VoIP-Link setzen
9. Finaler Test: Klingeln → Bild erscheint
```
