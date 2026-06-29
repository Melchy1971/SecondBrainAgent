---
title: "Wärmepumpe App offline"
type: chatgpt_conversation
source: chatgpt
source_id: "6a23fb03-a0d4-83eb-aabc-5c2c9b8885f5"
created: 2026-06-06
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# Wärmepumpe App offline

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6a23fb03-a0d4-83eb-aabc-5c2c9b8885f5`
- Nachrichten: 6

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

{"asset_pointer": "sediment://file_000000000340720a948a05c2b7d32236", "content_type": "image_asset_pointer", "fovea": null, "height": 1152, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 866989, "width": 1536}
Unsere Pool Wärmepumpe läuft und lässt sich manuell bedienen. In der App zeigt es aber offline an. Woran liegt das

### 2. Assistent

Auf dem Typenschild steht **Inverter FP-Smart STN130**. Das Gerät selbst läuft, also liegt der Fehler sehr wahrscheinlich **nicht an der Wärmepumpe**, sondern an der **WLAN-/App-Anbindung**.

Wahrscheinlichste Ursachen, nach Priorität:

## 1. WLAN nur 5 GHz statt 2,4 GHz

Viele Pool-Wärmepumpen-WLAN-Module funktionieren nur mit **2,4 GHz WLAN**. In Anleitungen zu vergleichbaren Inverter-Poolwärmepumpen wird explizit verlangt, dass der Router auf **2,4 GHz** konfiguriert ist. citeturn158197search2

Prüfen:

```text
Router-WLAN:
2,4 GHz aktiv
5 GHz testweise deaktivieren
WLAN-Name ohne Sonderzeichen
Passwort ohne Sonderzeichen testweise verwenden
WPA2 statt WPA3
```

Kritisch sind Mesh-Systeme oder FritzBox mit gleichem Namen für 2,4 und 5 GHz. Dann verbindet sich das Handy oft korrekt, aber die Wärmepumpe nicht.

## 2. WLAN-Modul hat Verbindung verloren

Wenn die App „offline“ zeigt, die Wärmepumpe aber lokal bedienbar ist, ist typisch:

```text
WLAN-Modul hängt
WLAN-Modul nicht verbunden
alte Routerdaten gespeichert
App-Bindung ungültig
Cloud-Verbindung unterbrochen
```

Eine Anleitung für WLAN-Adapter beschreibt bei „Gerät offline“ genau diesen Fall: WLAN-Modul prüfen, Gerät neu starten und neu verbinden. citeturn158197search11

Maßnahme:

```text
1. Wärmepumpe komplett stromlos machen
2. 2 Minuten warten
3. Router ebenfalls neu starten
4. Wärmepumpe wieder einschalten
5. App prüfen
```

## 3. Gerät muss neu gekoppelt werden

Wenn sich WLAN-Name, Passwort, Router, Mesh, Repeater oder App geändert haben, muss die Kopplung gelöscht und neu gesetzt werden. Bei ähnlichen Geräten wird beschrieben: WLAN-Taste bzw. Tastenkombination mehrere Sekunden halten, bis das WLAN-Symbol blinkt, danach in der App neu hinzufügen. citeturn158197search2

Ablauf:

```text
App:
Gerät entfernen

Wärmepumpe:
WLAN-Modus / Pairing-Modus aktivieren
meist 3–10 Sekunden WLAN-/Timer-/Set-Taste halten
WLAN-Symbol muss blinken

Handy:
mit 2,4-GHz-WLAN verbinden
mobile Daten testweise ausschalten
VPN deaktivieren
Bluetooth + Standort erlauben
Gerät in App neu hinzufügen
```

## 4. Empfang am Standort reicht für Handy, aber nicht für Wärmepumpe

Handy-Empfang am Gerät ist kein zuverlässiger Maßstab. Das WLAN-Modul in der Wärmepumpe ist deutlich schwächer.

Test:

```text
Router oder Repeater testweise näher an die Wärmepumpe
mindestens -65 dBm Signalqualität anstreben
keine Metallabdeckung direkt vor dem WLAN-Modul
keine Pooltechnikbox aus Metall
```

Falls Repeater verwendet wird:

```text
eigene 2,4-GHz-SSID nur für Geräte
feste Kanalwahl 1, 6 oder 11
keine automatische Bandsteuerung
kein WPA3-only
```

## 5. Falsche oder instabile App

Für FP-Smart/STN-Geräte wird eine WiFi-Steuerung mit App beworben. citeturn158197search1 Je nach Importeur laufen bauähnliche Geräte aber über unterschiedliche Apps, zum Beispiel herstellereigene Apps, „Fairland Smart Pool“, „Smart Life“ oder Full-Inverter-Apps. Wenn die falsche App verwendet wird, kann das Gerät gekoppelt wirken, aber dauerhaft offline bleiben.

Prüfen:

```text
Bedienungsanleitung / QR-Code an der Wärmepumpe
exakter App-Name
Gerät in App löschen
nur mit korrekter App neu koppeln
```

## Entscheidungspfad

| Symptom | Wahrscheinlichste Ursache | Maßnahme |
|---|---|---|
| App offline, Gerät läuft manuell | WLAN-Modul offline | Stromlos machen, neu starten |
| Kopplung schlägt fehl | 5 GHz / WPA3 / Mesh | 2,4 GHz separates WLAN einrichten |
| Gerät war früher online | Routerdaten geändert oder Modul hängt | Gerät löschen, neu koppeln |
| Gerät geht sporadisch online/offline | Signal zu schwach | Repeater näher, 2,4 GHz fixieren |
| App findet Gerät gar nicht | falsche App oder Pairing nicht aktiv | QR-Code/Manual prüfen, Pairing-Modus starten |

## Konkrete Empfehlung

Richte in der FritzBox oder im Router ein separates WLAN ein:

```text
Name: Pool-WLAN
Band: nur 2,4 GHz
Verschlüsselung: WPA2
Passwort: einfach, keine Sonderzeichen
5 GHz: aus für dieses WLAN
WPA3: aus
```

Dann Wärmepumpe aus der App löschen, Wärmepumpe 2 Minuten stromlos machen, WLAN-Pairing neu starten und über dieses separate **Pool-WLAN** neu verbinden.

### 3. Benutzer

Wie lautet die tasten Kombination für das wlan

### 4. Assistent

Bei der **FP-Smart / STN130** ist die WLAN-Aktivierung laut baugleicher **Dr. Smart STN130**-Anleitung:

```text
1. Display entsperren:
   Ein/Aus-Taste ca. 3 Sekunden gedrückt halten

2. WLAN-Kopplung starten:
   WLAN-/Verbindungstaste ca. 3–5 Sekunden gedrückt halten,
   bis ein Piepton kommt und das WLAN-Symbol blinkt

3. Danach in der App:
   Gerät hinzufügen starten
```

In der Anleitung steht für die STN-Serie: Zum Entsperren die Taste **3 Sekunden halten**; für die WLAN-Verbindung danach die entsprechende Taste halten, bis ein Signalton kommt. Während der Verbindung blinkt das WLAN-Symbol, bei erfolgreicher Verbindung leuchtet es dauerhaft. citeturn558548search1turn558548search4

Wichtig:

```text
Handy vorher mit 2,4-GHz-WLAN verbinden
5 GHz testweise deaktivieren
WPA2 verwenden, nicht WPA3-only
mobile Daten/VPN am Handy testweise ausschalten
```

Falls auf deinem Bedienfeld **keine eigene WLAN-Taste** ist, ist es meistens die Taste mit dem Symbol für **Timer/Uhr**, **SET** oder **Modus**. Bei dieser Baureihe ist das Symbol in manchen PDF-Anleitungen schlecht dargestellt, deshalb am Gerät nach dem kleinen WLAN-/Funk-Symbol suchen.

### 5. Benutzer

Wie lautet das Passwort

### 6. Assistent

Das Passwort ist **nicht das Passwort der Wärmepumpe**.

In der App musst du normalerweise das Passwort von deinem **Heim-WLAN / Router-WLAN** eingeben.

```text
Gemeint ist:
WLAN-Name: dein 2,4-GHz-WLAN
Passwort: dein normales WLAN-Passwort vom Router
```

Wichtig: Nicht mit dem WLAN/Hotspot der Wärmepumpe verbinden, falls eines angezeigt wird. Die App soll die Wärmepumpe mit deinem Heim-WLAN verbinden. Bei ähnlichen Pool-Wärmepumpen wird genau dieser Fehler beschrieben: Das Handy muss im Heim-WLAN bleiben; der Wärmepumpen-Hotspot ist nicht das Zielnetz. citeturn371292search1

Prüfe also:

```text
Handy mit 2,4-GHz-Heim-WLAN verbinden
App öffnen
Gerät hinzufügen
WLAN-Passwort vom Heim-WLAN eingeben
nicht das Wärmepumpen-WLAN auswählen
```

Falls die App ein Geräte- oder Hotspot-Passwort verlangt, probiere als Standardwerte:

```text
12345678
88888888
```

Aber bei deiner Einrichtung ist mit hoher Wahrscheinlichkeit dein **Router-WLAN-Passwort** gemeint.
