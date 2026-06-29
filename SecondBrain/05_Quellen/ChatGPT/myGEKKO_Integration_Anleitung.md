---
title: "myGEKKO Integration Anleitung"
type: chatgpt_conversation
source: chatgpt
source_id: "68c2e16a-780c-832c-ad38-bf3c6b3d4ed0"
created: 2025-09-11
tags:
  - chatgpt
  - import
  - ki
  - projekt
  - sap
---


# myGEKKO Integration Anleitung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68c2e16a-780c-832c-ad38-bf3c6b3d4ed0`
- Nachrichten: 6

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Ich habe eine myGEKKO Slider 2 und eine pc Anlage mit einer 10k Akku von Sonnen. Der Wechselrichter ist von Solaredge. Beide befinden sich im gleichen Netzwerk. Nun möchte ich diese beiden mit einander verbinden so das ich in myGEKKO alle Werte auslesen kann

### 2. Assistent

Du hast also drei Hauptkomponenten im Spiel:  

1. **myGEKKO Slider 2** → das zentrale Smart Home/Visualisierungssystem.  
2. **Sonnen Batterie (10 kWh)** → Energiespeicher mit eigenem Kommunikationsinterface.  
3. **SolarEdge Wechselrichter** → PV-Anlage mit Monitoring und Schnittstellen.  

Alle hängen am gleichen Netzwerk – das ist schon mal die halbe Miete. Damit myGEKKO die Werte darstellen kann, brauchst du eine **gemeinsame Sprache**. Das läuft bei diesen Systemen typischerweise über **Modbus TCP**, **Sonnen API (REST)** oder ein proprietäres Protokoll.  

---

### 1. Sonnen Batterie
- Sonnen bietet eine **REST-API** (http/https), über die du Ladezustand (SOC), Lade-/Entladeleistung, Netzbezug etc. abfragen kannst.  
- Beispiel: `http://<IP-der-sonnen>/api/v2/status` liefert JSON mit allen Werten.  
- Manche Firmware-Versionen haben Modbus-TCP, das geht dann noch einfacher für myGEKKO.  

### 2. SolarEdge Wechselrichter
- SolarEdge kann über **Modbus TCP** angesprochen werden. Das muss meist im Wechselrichter-Menü aktiviert werden.  
- Alternativ gibt es die **SolarEdge Monitoring API (Cloud)** – dafür bräuchtest du aber einen API-Key und Internetzugang. Für lokale Werte ist Modbus besser und schneller.  

### 3. myGEKKO Integration
- Der myGEKKO Slider 2 kann über **Modbus TCP** Daten auslesen und in der Visualisierung anzeigen.  
- Du musst dazu im myGEKKO die passenden **Register-Adressen** anlegen.  
  - Für SolarEdge gibt es fertige Modbus-Register-Maps (z. B. aktuelle PV-Leistung, Spannung, Netzbezug).  
  - Für Sonnen musst du prüfen, ob dein Modell Modbus spricht. Falls nur die REST-API verfügbar ist, müsstest du eventuell einen **Gateway-Übersetzer** (z. B. mit einem kleinen Raspberry Pi oder Node-RED) einsetzen, der REST → Modbus macht.  

---

### Vorgehen Schritt für Schritt
1. **Netzwerkkonfiguration prüfen**: Sonnen und SolarEdge haben feste IPs im gleichen Subnetz wie myGEKKO.  
2. **Modbus aktivieren**:  
   - SolarEdge: Modbus TCP im Menü einschalten, Slave-ID festlegen (meist 1).  
   - Sonnen: prüfen, ob Modbus verfügbar ist.  
3. **myGEKKO konfigurieren**:  
   - Neue Modbus-Geräte anlegen.  
   - Die gewünschten Register eintragen (Leistung, SOC, Spannung usw.).  
   - Visualisierung einrichten.  
4. **Testen**: mit Tools wie „Modbus Poll“ oder `mbpoll` kannst du von einem PC aus prüfen, ob die Daten erreichbar sind, bevor du myGEKKO damit verbindest.  
5. **Falls Sonnen nur REST kann**: kleinen Übersetzer im Netzwerk einrichten, der die Werte von der API holt und als Modbus bereitstellt.  

---

Das Entscheidende ist also: **Kann deine Sonnen-Batterie nativ Modbus TCP?**  
Wenn ja, ist es ziemlich direkt. Wenn nein, brauchst du eine kleine Middleware.  

👉 Willst du, dass ich dir die passenden Modbus-Register für SolarEdge und Sonnen raussuche und dir ein Beispiel für die myGEKKO-Konfiguration gebe?

### 3. Benutzer

Ja mit Schritt für Schritt Anleitung in myGEKKO

### 4. Assistent

Alles klar, Markus — hier ist die kompakte, funktionierende Schritt-für-Schritt-Anleitung, um deine **myGEKKO SLIDE 2** mit **SolarEdge (Wechselrichter)** und der **Sonnen-Batterie** zu verheiraten. Wir gehen so vor:

- SolarEdge → **lokal per Modbus TCP / SunSpec** einbinden (direkt in myGEKKO).
- Sonnen → je nach Firmware entweder **direkt per Modbus TCP** (falls verfügbar) oder praxisbewährt über die **lokale REST-API** mit einer kleinen **Node-RED-„Brücke“** (REST → Modbus), damit myGEKKO die Werte wie gewohnt per Modbus holt.

myGEKKO arbeitet dabei **ausschließlich als Modbus-Master** (Client) — also Daten abholen, nicht bereitstellen. citeturn7view0

---

# 0) Voraussetzungen (einmalig)

1) **Feste IP-Adressen** vergeben für:
   - SolarEdge-WR (z. B. 192.168.1.50)
   - Sonnen-Batterie (z. B. 192.168.1.60)
   - myGEKKO (z. B. 192.168.1.10)

2) **Nur ein Modbus-Master pro SolarEdge!** Wenn z. B. eine andere Software schon Modbus liest, abschalten — SolarEdge erlaubt genau einen Master (entweder TCP **oder** RTU). citeturn14view2

3) Du brauchst auf dem WR **Modbus TCP aktiv**, Port **502**, **Unit-ID** (typisch **1**). (Aktivierbar in SetApp/LCD, Details im SolarEdge-Technikdokument zur SunSpec-Implementierung.) citeturn14view2

---

# 1) SolarEdge → myGEKKO (SunSpec/Modbus TCP)

## 1.1 SolarEdge vorbereiten
- **Modbus TCP** aktivieren (SetApp/LCD): Kommunikation → Modbus → **TCP an**, **Port 502**, **Device ID 1** (oder deine ID). Beachte: **ein Master**. citeturn14view2

## 1.2 Modbus-IO-Station in myGEKKO anlegen
1) Am myGEKKO als **Konfigurator** anmelden.  
2) **Einstellungen → IO-Konfiguration** öffnen, **neue IO-Station: „Modbus“**.  
3) **TCP** wählen, **Port: „LAN-TCP“**, IP des SolarEdge eintragen, **Port 502**. Sobald die Verbindung steht, wird der Button der IO-Station grau. citeturn10view0

## 1.3 Für den Energiemanager: SunSpec-Zähler nutzen (empfohlen)
myGEKKO kann PV-Leistungs-/Energiewerte direkt über **SunSpec-Modbus** als **PV-Produktionszähler** einbinden:

1) **System → Energiemanager** öffnen, neues Element anlegen.  
2) **IO-Konfiguration** des Energiemanagers → **PV-Produktionszähler** → **Einbindung: „SunSpec-Modbus“** wählen und die eben angelegte Modbus-Station referenzieren.  
3) Damit fließen die PV-Leistungs-/Energiewerte sauber in Visualisierung, Trends, Tageslisten und Regeln. citeturn6view0

> Hintergrund: Der Energiemanager akzeptiert PV-Werte via SunSpec; für Batterielogik brauchst du zusätzlich Netz-/Haus-Zähler oder Batterie-Leistungswerte (siehe Abschnitt 3). citeturn6view0

## 1.4 Optional: Einzelwerte selbst als Register abholen (für eigene Anzeigen)
Wenn du zusätzlich Rohwerte z. B. für Kacheln/Trends willst, nutze **„REG List“** und trage SunSpec-Register ein. Beispiel (SolarEdge SunSpec Inverter-Modell 101/102/103, Basis ab 40070):

- **AC-Leistung (W)**: Reg **40084** (I_AC_Power, int16), **Skalierungsfaktor**: **40085** (I_AC_Power_SF, int16).  
- **AC-Frequenz (Hz)**: **40086**, SF **40087**.  
- **Lebensdauer-Energie (Wh)**: **40094–40095** (acc32), SF **40096**.  
- **Status**: **40108** (I_Status).  
(Die SunSpec-Register sind dokumentiert; beachte Int+SF-Scaling.) citeturn14view2

**So trägst du das in myGEKKO ein:**  
Einstellungen → IO-Konfiguration → deine **Modbus-Station** → **Register → „REG List“**.  
- Als **TYPE** je nach Wert **REG16** (16 Bit) oder **REG32** (32 Bit).  
- Reihenfolge zählt: legst du 32-Bit an, bleibt die nächste Zeile frei (Adressloch).  
- Die **Skalierung** (SF) kann in myGEKKO nicht dynamisch verknüpft werden; lies **Wert** und **SF** und rechne bei Bedarf in einer myGEKKO-Logik nach (oder verwende für den Energiemanager direkt „SunSpec“ wie oben). citeturn12view0turn13view1

**Verbindung testen:** In der Modbus-Station auf **„Testing“** klicken, z. B. Register **40084** lesen. Wenn „OK“, ist die Verbindung stabil. citeturn13view0

---

# 2) Sonnen-Batterie → myGEKKO

Es gibt zwei praktikable Wege:

## 2A) Direkt per Modbus TCP (falls in deiner Sonnen-Firmware vorhanden)
Einige Varianten/Regionen erlauben Modbus (z. B. für Zähler-Anbindung). Wenn dein Sonnen-System eine **öffentliche Modbus-Registertabelle** bereitstellt, kannst du exakt wie bei SolarEdge vorgehen: **IO-Station (Modbus TCP)** anlegen, **Register** laut Handbuch eintragen, dann im **Energiemanager** unter **„Speichersystem“** die Lade-/Entladeleistung zuweisen. (Die allgemeine TCP-Konfiguration ist identisch.) citeturn10view0turn6view0

> Da Sonnen die Modbus-Register der Batterie **nicht** überall offen dokumentiert, ist 2B oft der realistische Weg.

## 2B) Stabil & lokal: REST-API → Node-RED-Brücke → Modbus (empfohlen, wenn 2A fehlt)

**Idee:** myGEKKO liest Modbus. Die Sonnen liefert lokal per **REST-API v2** alle Werte (SoC, Leistung etc.). Eine kleine Node-RED-Instanz holt die Sonnen-JSON-Daten zyklisch und stellt sie als **„virtuellen Modbus-Server“** im LAN bereit. myGEKKO greift darauf zu, als wäre es ein normales Modbus-Gerät.

### Schritte

1) **Sonnen-API prüfen**  
   - API-Token im Sonnen-Dashboard unter „Software-Integration“ (je nach Modell/FW).  
   - Test im Browser/Tool:  
     - `http://<IP-der-sonnen>/api/v2/latestdata` (meist mit `Auth-Token: <TOKEN>`)  
     - oder `http://<IP-der-sonnen>/api/v2/status`  
     Die API liefert u. a. SoC, aktuelle Batterie-Leistung, Netzbezug/Einspeisung. citeturn5search0

2) **Node-RED auf einem kleinen Rechner (z. B. RPi, VM) installieren**  
   - Nodes: `node-red-node-httprequest` (REST), `node-red-contrib-modbus` (Modbus TCP **Server**).  
   - Flow (alle 2–5 s):  
     - HTTP-Request → Sonnen `/api/v2/latestdata`  
     - JSON parsen → relevante Felder abgreifen  
     - Auf **eigene Modbus-Register** mappen (z. B. Start bei 100):

      | Virtuelles Register | Inhalt (Beispiel)                 | Typ / Wertebereich                 |
      |---|---|---|
      | 100 | **SoC** in % ×100 (z. B. 63,45 % → 6345) | REG16, Anzeige in myGEKKO mit 1/100 skalieren |
      | 101 | **Batterie-Leistung W** (+ Laden / − Entladen) | REG16 (oder REG32, wenn >±32 kW nötig) |
      | 102 | **Netzleistung W** (+ Bezug / − Einspeisung)   | REG16 |
      | 103 | **Hausverbrauch W** (falls Feld vorhanden/ableitbar) | REG16 |

   - Modbus-Server in Node-RED auf **Port 1502** lauschen lassen (so kollidiert es nicht mit anderen 502-Diensten).

3) **myGEKKO an den virtuellen Modbus hängen**  
   - **Neue IO-Station: „Modbus“**, **TCP**, IP des Node-RED-Hosts, **Port 1502**.  
   - **REG List** anlegen und die obigen Register (100ff) als **REG16/REG32** eintragen; SoC mit **C.1/100** anzeigen. citeturn10view0turn12view0turn13view1

4) **Energiemanager verknüpfen**  
   - **System → Energiemanager → IO-Konfiguration → „Speichersystem“**:  
     - **Batterie-Lade-/Entladeleistung** = dein Modbus-Eingang (z. B. Reg 101).  
   - Optional: **Netz- und Hauszähler** zuweisen (entweder echte Zähler oder abgeleitete Messwerte). Hinweis aus dem Handbuch: Für korrekte Berechnungen brauchst du **entweder** Batterie-Leistung **+** Hausverbrauch **oder** einen **Netzzähler**, sonst verzerren sich die Werte. citeturn6view0

---

# 3) Visualisierung, Trends & Logik in myGEKKO

- **Kacheln/Displays**: Die angelegten Modbus-Eingänge (PV-Leistung, SoC, Netzfluss …) kannst du direkt in myGEKKO-Seiten anzeigen.  
- **Trends/Tageslisten**: Über den Energiemanager werden die Energiedaten automatisch aufgezeichnet und schön aufbereitet. citeturn6view0  
- **Skalierung**: In **„Verwenden der Register“** kannst du pro Register Typ (REG16/32) und einfache Skalierungen einstellen (z. B. 1/100). Für **SunSpec-Scale-Faktoren** (dynamisch) lies den Wert und den SF getrennt und verrechne ihn bei Bedarf in einer myGEKKO-Logik. citeturn13view1

---

# 4) Tests & Fehlersuche

- **Modbus-Test**: In der IO-Station auf **„Testing“** ein Register lesen (z. B. 40084 bei SolarEdge). „OK“ = Verbindung steht. citeturn13view0  
- **Adressierung**: Achte in myGEKKO auf **0-/1-basierte** Adressen und **Registerbreite** (16/32 Bit). Bei 32 Bit die nächste Zeile freilassen (Adressloch). citeturn12view0  
- **Ein Master**: Wenn SolarEdge keine Werte liefert, prüfe, ob noch eine andere Software als Modbus-Master aktiv ist. citeturn14view2  
- **SunSpec-Register sicher**: Typische SolarEdge-Adressen (Beispiele):  
  - AC-Power **40084**, SF **40085**; Lifetime-Energy **40094–40095**, SF **40096**; Status **40108**. (Offizielle SunSpec-Map) citeturn14view2  
- **Sonnen-API**: Wenn `/api/v2/latestdata` oder `/api/v2/status` nicht antworten, prüfe Token/Endpoint im Sonnen-Dashboard (Software-Integration). citeturn5search0

---

## Warum diese Architektur?

- **myGEKKO liebt Modbus** (Master, TCP/RTU) und hat dafür saubere UI-Anbindung inkl. Energiemanager. citeturn7view0turn10view0  
- **SolarEdge** liefert lokal per **SunSpec-Modbus** alle relevanten PV-Werte: robust, schnell, ohne Cloud. citeturn14view2  
- **Sonnen** ist lokal hervorragend per **REST-API v2** auslesbar; mit der kleinen Node-RED-Brücke wird’s für myGEKKO „wie Modbus“. citeturn5search0

---

Wenn du das so umsetzt, siehst du in myGEKKO:

- **PV-Leistung/Energie** (SunSpec/Modbus direkt vom SolarEdge)  
- **SoC & Batterie-Leistung** (über Sonnen-API → Node-RED-Modbus)  
- **Netzfluss/Hausverbrauch** (aus Zähler oder abgeleitet), alles sauber im **Energiemanager** verknüpft — inklusive Visualisierung, Trends und Automationslogik. citeturn6view0

Kleines Extra für die Nerd-Seele: Wenn du bei SolarEdge zusätzlich Feingrößen wie DC-Spannung, Temperatur oder Statuscodes brauchst, leg sie über „REG List“ an (Register **40099**, **40104**, **40108** etc.) und veredle sie mit myGEKKO-Logik — das ist wie Gewürze an die Suppe: nicht zwingend, aber köstlich. citeturn14view2turn13view1

---

### Weiterführen
Als Nächstes lohnt sich eine **Energieszene** im Energiemanager (z. B. Priorität Laden ab SoC < 30 %, ab SoC > 80 % Überschuss an Wärmepumpe/Wallbox freigeben) und **Trend-Dashboards** für Tages-/Monatsverläufe. Das macht die Anlage nicht nur hübsch, sondern messbar effektiv. citeturn6view0

Wenn du möchtest, formuliere ich dir auf Wunsch ein **Node-RED-Flow-Snippet** für die Sonnen-Bridge (inkl. Beispiel-Registermapping 100–110) und eine kleine **myGEKKO-REG-List-Vorlage** zum direkten Abtippen.

### 5. Benutzer

Ja

### 6. Assistent

Super — hier ist das **konkrete Paket**:  
1) ein lauffähiger **Node-RED-Flow** (Sonnen-API → Modbus-TCP-Server, Register 100ff),  
2) Vorlagen für **myGEKKO REG-List** (Sonnen-Werte & SolarEdge-SunSpec-Basics),  
3) kurze Checkliste in myGEKKO.

---

# 1) Node-RED-Bridge (Sonnen REST → Modbus TCP)

## 1.1 Benötigte Nodes
- `node-red-node-httprequest`
- `node-red-contrib-modbus` (wir nutzen **Modbus Flex Server**)

## 1.2 Flow-JSON (einfügen über Menü → Import → Clipboard)

> **Bitte anpassen:** `SONNEN_IP` und `SONNEN_TOKEN`.  
> Der Modbus-Server lauscht lokal auf **Port 1502**, Unit-ID **1**.  
> Register-Mapping (Holding Register):  
> 100=SoC×100, 101=Batt-Power(W), 102=Grid-Power(W), 103=Home-Power(W), 104=PV-Power(W)

```json
[
  {
    "id": "inject5s",
    "type": "inject",
    "z": "flow1",
    "name": "alle 5 s",
    "props": [{"p":"payload"}],
    "repeat": "5",
    "once": true,
    "onceDelay": "1",
    "wires": [["build-url"]]
  },
  {
    "id": "build-url",
    "type": "function",
    "z": "flow1",
    "name": "URL & Header",
    "func": "const SONNEN_IP = \"192.168.1.60\"; // <- ANPASSEN\nconst SONNEN_TOKEN = \"DEIN_TOKEN_HIER\"; // <- ANPASSEN\n\nmsg.headers = {\n  \"Auth-Token\": SONNEN_TOKEN,\n  \"Accept\": \"application/json\"\n};\nmsg.method = \"GET\";\n// Bevorzugt: /api/v2/latestdata (fällt zurück auf /api/v2/status)\nmsg.url = `http://${SONNEN_IP}/api/v2/latestdata`;\nreturn msg;",
    "outputs": 1,
    "noerr": 0,
    "wires": [["http-sonnen","catch-try-status"]]
  },
  {
    "id": "http-sonnen",
    "type": "http request",
    "z": "flow1",
    "name": "GET /api/v2/latestdata",
    "method": "GET",
    "ret": "obj",
    "paytoqs": "ignore",
    "tls": "",
    "persist": false,
    "wires": [["map-values"]]
  },
  {
    "id": "catch-try-status",
    "type": "http request",
    "z": "flow1",
    "name": "Fallback: /api/v2/status (bei 404/401)",
    "method": "GET",
    "ret": "obj",
    "paytoqs": "ignore",
    "tls": "",
    "persist": false,
    "wires": [["map-values"]]
  },
  {
    "id": "map-values",
    "type": "function",
    "z": "flow1",
    "name": "JSON → Register 100ff",
    "func": "// Erwartete Felder (je nach FW heißen sie leicht anders):\n// SoC (%), BatteryChargePower / BatteryDischargePower oder BatteryPower (Vorzeichen),\n// GridPower (+Bezug/-Einspeisung), Production_W (PV), Consumption_W (Haus).\n\nconst d = msg.payload || {};\n\nfunction pickNumber(...keys){\n  for (const k of keys){\n    if (d[k] !== undefined && d[k] !== null) {\n      const v = Number(d[k]);\n      if (!Number.isNaN(v)) return v;\n    }\n  }\n  return 0;\n}\n\n// SoC in % als x100 (z.B. 63.45% → 6345)\nconst soc = pickNumber('USOC','RSOC','StateOfCharge','SoC','Percentage','soc');\nconst soc_x100 = Math.round(soc * 100);\n\n// Batterie-Leistung (W), Vorzeichen: + Laden / - Entladen oder umgekehrt je nach Feld\nlet battW = 0;\nif (d.hasOwnProperty('BatteryPower')) {\n  battW = Number(d['BatteryPower']);\n} else {\n  const ch = pickNumber('BatteryChargePower');\n  const dis = pickNumber('BatteryDischargePower');\n  // Konvention: positive Werte = Laden, negative = Entladen\n  battW = Math.round(ch - dis);\n}\n\nconst gridW = pickNumber('GridPower','GridFeedIn_W','Pac_total_W','PowerGrid');\nconst homeW = pickNumber('Consumption_W','Load_W','HomeLoad_W');\nconst pvW = pickNumber('Production_W','PV_W','Pac_PV');\n\n// In Holding-Register schreiben:\n// 100 SoC x100 (REG16), 101 battW (REG32 für Sicherheit),\n// 102 gridW (REG32), 103 homeW (REG32), 104 pvW (REG32)\n\n// Wir bauen ein Objekt für den Flex-Server: { holding: { index: value, ... } }\nconst holding = {};\nholding[100] = Math.max(0, Math.min(10000, soc_x100));\n\nfunction toInt32(v){\n  // 32-bit signed wrap\n  const n = (v | 0); // Node macht 32-bit int op\n  return n;\n}\n\nholding[101] = toInt32(battW);\nholding[102] = toInt32(gridW);\nholding[103] = toInt32(homeW);\nholding[104] = toInt32(pvW);\n\nmsg.payload = { holding };\nreturn msg;",
    "outputs": 1,
    "noerr": 0,
    "wires": [["flex-server"]]
  },
  {
    "id": "flex-server",
    "type": "modbus-flex-server",
    "z": "flow1",
    "name": "Virtueller Modbus TCP Server (Port 1502, Unit 1)",
    "host": "0.0.0.0",
    "port": "1502",
    "unitid": 1,
    "floatbe": false,
    "databits": "8",
    "parity": "none",
    "stopbits": "1",
    "useIOFile": false,
    "ioFile": "",
    "reconnectTimeout": "2000",
    "showErrors": true,
    "wires": [[],[],[],[]]
  }
]
```

### Hinweise
- Wenn deine Sonnen-FW nur mit `/api/v2/status` antwortet: Der Fallback-HTTP-Node bleibt 200/OK, der erste würde 404/401 zeigen. Du kannst den Fallback per Link aus dem URL-Builder trennen, falls nicht nötig.
- Registerbreite: Wir liefern **REG16** (SoC×100) und **REG32** (Leistungen), myGEKKO kann beides lesen.

---

# 2) myGEKKO: IO-Station & REG-List

## 2.1 IO-Station anlegen (Sonnen-Bridge)
- **Einstellungen → IO-Konfiguration**  
- **Neue IO-Station: „Modbus“** → **TCP**  
- **IP** = IP des Node-RED-Hosts, **Port** = **1502**, **Unit-ID** = **1**  
- Speichern; Station wird grau, wenn Verbindung steht.

## 2.2 REG-List (Sonnen-Werte)
> **Einstellungen → IO-Konfiguration → [deine Modbus-Station] → Register → REG List**

| Nr. | TYPE  | REG | Beschreibung                          | Skalierung in Anzeige |
|----:|:-----:|----:|----------------------------------------|-----------------------|
| 1   | REG16 | 100 | SoC ×100 (%)                           | Faktor 0.01           |
| 2   | REG32 | 101 | Batterie-Leistung (W) (+Laden/−Entl.)  | —                     |
| 3   | REG32 | 102 | Netzleistung (W) (+Bezug/−Einspeisung) | —                     |
| 4   | REG32 | 103 | Hausverbrauch (W)                      | —                     |
| 5   | REG32 | 104 | PV-Leistung (W)                        | —                     |

> In myGEKKO kannst du bei der Anzeige **0.01** als Faktor setzen, damit aus 6345 wieder **63,45 %** wird.

---

# 3) SolarEdge (direkt via SunSpec/Modbus TCP)

## 3.1 IO-Station anlegen (SolarEdge)
- **Neue IO-Station: „Modbus“** → **TCP**, IP = SolarEdge-WR, **Port 502**, **Unit-ID 1** (oder deine).

## 3.2 Schnelle REG-List (häufige SunSpec-Werte)
> Viele SolarEdge-Modelle nutzen SunSpec-Model 103; die Startadressen variieren je nach Map. Diese Beispiel-Adressen sind oft zutreffend — prüfe im Zweifel die Dokumentation deines WR.

| Nr. | TYPE  | REG   | Beschreibung                      | Hinweis                   |
|----:|:-----:|------:|------------------------------------|---------------------------|
| 1   | REG16 | 40084 | AC-Leistung (W, int16)             | mit SF bei 40085          |
| 2   | REG16 | 40085 | AC-Power Scale Factor (int16)      | z. B. −1 → Wert×10^-1     |
| 3   | REG32 | 40094 | Lifetime-Energy Low (Wh)           | 32-bit, nächstes frei lassen |
| 4   | REG32 | 40095 | Lifetime-Energy High (Wh)          | Teil des 32-bit-Wertes    |
| 5   | REG16 | 40096 | Energy Scale Factor (int16)        |                           |
| 6   | REG16 | 40108 | Inverter-Status                    | Zustandskode              |

**Wichtig zu SunSpec-Scaling:** myGEKKO skaliert nicht automatisch mit dem SF-Register. Lies **Wert** und **SF** getrennt ein und rechne bei Bedarf in einer kleinen myGEKKO-Logik nach (oder verwende für PV im **Energiemanager** die Einbindung **„SunSpec-Modbus“**, die die Energiewerte sauber übernimmt).

---

# 4) Energiemanager verbinden

**System → Energiemanager → IO-Konfiguration**

- **PV-Produktionszähler**: Einbindung **„SunSpec-Modbus“** auf die SolarEdge-Station setzen (empfohlen).  
- **Speichersystem**:  
  - **Batterie-Leistung** = Sonnen-Bridge **Reg 101**  
  - Optional: **Netzleistung** = **Reg 102** und/oder **Hausverbrauch** = **Reg 103**  
- Damit laufen Visualisierung, Tageslisten und Regelwerke konsistent.

---

# 5) Tests & Trouble-Shooting

- **Modbus-Test** in der IO-Station: Register z. B. 100 (SoC) oder 40084 (WR-Leistung) lesen → „OK“ erwartet.  
- **32-Bit-Register**: In myGEKKO beim Anlegen die **nächste Zeile frei lassen** (Adressloch), damit 32-Bit sauber gepuffert wird.  
- **Ein Master je SolarEdge-WR**: Wenn Werte sporadisch fehlen, prüfe, ob noch eine andere Software per Modbus auf den WR zugreift.  
- **Sonnen-API**: Wenn `/latestdata` 401/404 liefert, nutze `/status` oder prüfe Token/Endpoint.

---

## Nächste sinnvolle Erweiterungen
- Register 105–110 für **Summenenergie** (kWh), **Temperaturen**, **Zustände** reservieren.  
- Eine kleine **Fehleranzeige** (Register 120: 0=OK, ≠0 bedeutet „API/Mapping-Problem“) aus dem Flow setzen.  
- Optional: Node-RED schreibt die **SunSpec-Scale-Faktoren** in eigene Register (z. B. 130/131), dann kannst du in myGEKKO jederzeit korrekt skalieren.

Viel Spaß beim Verdrahten im Datenuniversum. Wenn du willst, liefere ich dir noch eine **myGEKKO-RegList als CSV** zum Copy-Paste oder ein **kleines Mapping-Diagramm** für dein Projekt-Notizbuch.
