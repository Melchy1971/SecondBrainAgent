---
title: "Docker Paperless Zugriff Problem"
type: chatgpt_conversation
source: chatgpt
source_id: "6811e0fd-f3a8-8007-9167-7b44fc1fbc89"
created: 2025-04-30
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# Docker Paperless Zugriff Problem

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6811e0fd-f3a8-8007-9167-7b44fc1fbc89`
- Nachrichten: 10

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

warum komme ich nicht auf die installierten docker wie z.b. paperless. die adresse ist 192.168.2.178:8000 es wird nichts im browser angezeigt obwohl der docker gestartet ist und ich auf unraid komme

### 2. Assistent

Hier ein schneller Leitfaden, wie du auf Unraid + Docker herausfindest, warum Paperless-ngx (oder ein anderer Container) trotz gestarteten Status nicht auf Port 8000 erreichbar ist:

---

### 1 – Stimmt die Adresse?

| Check | Wie? | Was du sehen willst |
|-------|------|---------------------|
| **IP** | Vom PC ein `ping 192.168.2.178` oder `arp -a` | Antwortpakete bzw. derselbe MAC wie dein Unraid-Server |
| **Port** | `curl -I http://192.168.2.178:8000` | `HTTP/1.1 200` oder wenigstens `Connection refused` statt Timeout |

*Timeout ⇒ Service lauscht gar nicht*   *Refused ⇒ Service läuft, Port aber falsch gemappt.*

---

### 2 – Port-Mapping im Docker-Tab

1. Docker-Tab ➜ Paperless-Container ➜ „Ansicht ändern ➜ Erweitert“  
2. In der Spalte **„Ports“** sollte etwas wie  
   ```
   0.0.0.0:8000 → 8000/tcp
   ```  
   stehen.

* Häufiger Fehler: Host-Port wurde z. B. auf `5080` gesetzt. Dann müsstest du `:5080` im Browser aufrufen.
* Wenn **Netzwerk-Modus = br0** (oder br1):  
  - Der Container bekommt eine _eigene_ IP (z. B. 192.168.2.181).  
  - Dann ruf die Container-IP _ohne_ Port-Mapping auf: `http://192.168.2.181:8000`.

---

### 3 – Container-Logs checken

*UI* Docker-Tab ➜ Klick auf das Symbol 📝 (Log) neben dem Container.  
*CLI* `docker logs -f paperless`  

Achte auf Zeilen wie:

* `Gunicorn listening on 0.0.0.0:8000` ✅ alles ok  
* `address already in use` → Port-Konflikt auf dem Host  
* `migrations pending` oder `waiting for db` → Paperless startet noch

---

### 4 – Health-Status prüfen

In Unraid 6.12+ zeigt die Spalte „Health“ schnell an, ob der Container **healthy / unhealthy / starting** ist.  
`unhealthy` → Öffne die Logs, oft fehlt z. B. die Datenbank-Verbindung.

---

### 5 – Firewall / Browser Cache

* Keine Windows-/AV-Suite blockiert Port 8000?  
* Anderen Browser oder Inkognito testen.

---

### 6 – Typische Stolpersteine bei Paperless-ngx

| Problem | Symptom | Lösung |
|---------|---------|--------|
| Erststart dauert | Browser-Timeout, CPU-Last hoch | Warten, bis `Created superuser` im Log erscheint |
| Redis nicht verbunden | „Cannot connect to redis“ im Log | Stelle sicher, dass das Redis-Sidecar / Service läuft |
| falscher `PAPERLESS_PORT`-Wert | Container lauscht auf 8000, aber du hast 8001 gemappt | Gleichziehen oder Umleiten (Traefik, Nginx Proxy Manager) |

---

## Schnelle To-Do-Liste

1. **Ping + curl** → zeigt, ob Netz + Port offen sind.  
2. **Docker-Tab** → Port-Mapping bzw. eigene IP verifizieren.  
3. **Logs live ansehen (`docker logs -f`)** → Fehlermeldung finden.  
4. **Health-Status** → zeigt sofort, ob Paperless selbst ein Problem hat.  

Wenn du dabei auf eine konkrete Fehlermeldung stößt, schick mir den Log-Ausschnitt (die letzten ~20 Zeilen) – dann können wir gezielt weitermachen.

### 3. Benutzer

ist nicht erreichbar

### 4. Assistent

Okay, dann lass uns ein-bis-zwei gezielte Checks machen, um den Schuldigen einzukreisen. Du brauchst nur das Unraid-Web-Terminal oder SSH auf den Server.

---

## 1 – Siehst du den Port überhaupt auf dem **Host**?

```bash
# zeigt alle offenen Sockets, filtert auf 8000
lsof -i -P -n | grep ':8000'
```

* **Falls eine Zeile erscheint** wie  
  `python3   12345 paperless   7u  IPv4 … TCP *:8000 (LISTEN)`  
  ▶︎ Paperless lauscht – gut, es ist eher ein Netzwerk-/Mapping-Problem.
* **Wenn gar nichts kommt**  
  ▶︎ Paperless startet nicht richtig → gleich Log ansehen (Schritt 3).

---

## 2 – Stimmt das Port-Mapping bzw. der Netzwerk-Modus?

```bash
docker ps --format '{{.Names}}\t{{.Networks}}\t{{.Ports}}' | grep paperless
```

* **Bridge-Modus (Standard)**  
  Ausgabe sollte z. B. `0.0.0.0:8000->8000/tcp` zeigen.  
  ╰→  in diesem Fall **muss** `http://192.168.2.178:8000` erreichbar sein.
* **br0 / eigene IP**  
  Dann steht dort `br0` und _kein_ Mapping. Hole dir die Container-IP:

  ```bash
  docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' paperless
  ```
  Browser-Aufruf wäre dann `http://<Container-IP>:8000`.

---

## 3 – Container-Logs (zeigt meist sofort den Fehler)

```bash
docker logs --tail=50 paperless
```

* Suche nach:
  * `Listening on 0.0.0.0:8000` → Port ok
  * `address already in use`  → anderer Dienst blockiert 8000
  * `waiting for db` / `cannot connect to redis` → Abhängigkeit fehlt
  * Tracebacks oder _migrations pending_ → erste Initialisierung läuft noch

---

## 4 – Gegenprobe von **außen** (deinem PC)

```bash
# Windows PowerShell / macOS / Linux
curl -I --connect-timeout 3 http://192.168.2.178:8000
```

* **`HTTP/1.1 …`** → Seite liefert etwas zurück, Problem liegt im Browser/Proxy.
* **`Connection refused`** → Server erreicht, Port wird aber aktiv abgelehnt → Port-Mapping falsch.
* **Timeout** → Gar keine Antwort → Dienst lauscht nicht (siehe Schritte 1/3) _oder_ Firewall blockiert.

---

### Wenn du festhängst …

1. **Log-Auszug posten** (letzte 30 Zeilen).  
2. Ergebnis von `docker ps --format '{{.Names}}\t{{.Ports}}' | grep paperless` posten.  
3. Ergebnis von `lsof -i -P -n | grep ':8000'` posten.

Damit können wir in die richtige Richtung bohren.

### 5. Benutzer

wie rufe ich das terminal auf

### 6. Assistent

So kommst du unter Unraid an ein Terminal (CLI), um die Befehle auszuführen:

| Methode | Wann sinnvoll | Schritte |
|---------|---------------|----------|
| **Web-Terminal (integriert)** | Schnellster Weg, wenn du schon in der Unraid-GUI bist | 1. Melde dich in der Unraid-Web-GUI an.  <br>2. Rechts oben in der Menüleiste siehst du ein **`>_`-Symbol** (Tooltip „Terminal“). <br>3. Anklicken → es öffnet sich ein neues Browser-Fenster mit einer Shell als **root**. |
| **Docker-Console** | Nur für Befehle _im Container_ | Docker-Tab ➜ gewünschter Container ➜ **rechts auf das Terminal-Symbol klicken** („Console“). |
| **SSH von deinem PC** | Bequemer, wenn du öfter CLI brauchst oder lieber dein eigenes Terminal nutzt | 1. **SSH in Unraid aktivieren**: Settings ➜ Management Access ➜ „SSH“ = Enable, Port 22 lassen. <br>2. Vergewissere dich, dass du für **root** ein Passwort gesetzt hast (Users ➜ root ➜ Passwort). <br>3. **Windows 10/11**: Eingabeaufforderung / PowerShell → `ssh root@192.168.2.178` <br>    **oder** Putty: Host = 192.168.2.178, Port = 22, Open. <br>   **macOS / Linux**: Terminal → `ssh root@192.168.2.178` <br>4. Fingerprint akzeptieren, Passwort eingeben → du bist in der Shell. |
| **Direkt am Server (Keyboard + Monitor)** | Wenn Netzwerk tot ist oder SSH deaktiviert | Monitor und Tastatur an den Unraid-Rechner anschließen → anmelden als **root**. |

> **Tipp:** Das Web-Terminal genügt für die Befehle  
> `lsof -i -P -n | grep ':8000'`  
> und  
> `docker ps --format '{{.Names}}\t{{.Ports}}' | grep paperless`

Sobald du die Shell offen hast, kannst du genau diese Kommandos eingeben und mir die Ausgabe schicken, dann gehen wir den nächsten Schritt.

### 7. Benutzer

die ip adresse lässt sich anpingen nur der port nicht

### 8. Assistent

Alles klar – die Verbindung zum Server selbst klappt (Ping), aber TCP-Port 8000 antwortet nicht. Das bedeutet fast immer, dass **entweder der Dienst im Container nicht lauscht** oder **das Port-Mapping/Netzwerk-Modell falsch ist**. Lass uns das jetzt systematisch prüfen. Du brauchst nur das Web-Terminal, das du gerade geöffnet hast.

---

## 1 – Sieht Unraid den Port überhaupt?

```bash
# Auf dem Unraid-Host
lsof -i -P -n | grep ':8000'
```

* **Erscheint eine Zeile mit „LISTEN“?**  
  ➜ Beispiel  
  ```
  python3 12345 paperless   7u  IPv4 0x…  TCP *:8000 (LISTEN)
  ```  
  → Dienst lauscht ⇒ Problem liegt im Docker-Mapping oder in einer Firewall.

* **Kommt nichts zurück?**  
  → Paperless lauscht nicht ⇒ gleich Schritt 3 (Logs) ansehen.

---

## 2 – Port-Mapping / Netzwerk-Modus prüfen

```bash
docker ps --format '{{.Names}}\t{{.Networks}}\t{{.Ports}}' | grep -i paperless
```

* **Bridge-Modus**  
  Ausgabe enthält etwas wie `0.0.0.0:8000->8000/tcp`.  
  * Wenn dort **ein anderer Host-Port** steht (z. B. `0.0.0.0:5080->8000/tcp`), dann musst du im Browser `http://192.168.2.178:5080` aufrufen.  
  * Steht `:::8000->8000/tcp`, ist alles korrekt und Port 8000 sollte erreichbar sein.

* **br0 (eigene IP)**  
  Es steht `br0` und **kein Port-Mapping**. Dann bekommt der Container eine eigene Adresse im LAN. Hole sie dir:

  ```bash
  docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' paperless
  ```

  Aufruf wäre dann `http://<Container-IP>:8000`.

Notier dir die komplette Zeile und schick sie mir hier, falls du nicht sicher bist, was du siehst.

---

## 3 – Container-Logs auf Fehlermeldungen prüfen

```bash
docker logs --tail=50 paperless
```

Achte auf Zeilen wie:

* `Listening on 0.0.0.0:8000`  ✅ Dienst läuft  
* `address already in use`    → Port-Konflikt mit einem anderen Container/Dienst  
* `waiting for db` / `cannot connect to redis` → Abhängigkeiten fehlen, Paperless startet gar nicht  
* Tracebacks oder Migrations-Output → erster Start dauert, einfach warten

Kopiere bei Fehlern die letzten 20 Zeilen hier hinein.

---

## 4 – Gegenprobe direkt auf dem Host

Wenn Schritt 1 gezeigt hat, dass jemand auf 8000 lauscht, teste von **Unraid selbst**:

```bash
curl -I http://127.0.0.1:8000
```

* **Antwort (`HTTP/1.1 200` oder 302 etc.)** → Dienst läuft; das Problem ist das externe Mapping.  
* **`Connection refused`** → Dienst lauscht nicht oder iptables blockt.  
* **Timeout** → Dienst existiert nicht → Logs checken.

---

## 5 – Firewall/AV auf deinem PC ausschließen

Selten blockiert eine lokale Sicherheits-Suite ungewöhnliche Ports. Teste kurz von einem zweiten Gerät oder in einem Inkognito-Fenster, während du Schritte 1-4 durchführst.

---

### Nächste Schritte

1. Führe **Schritt 1** und **Schritt 2** aus und kopiere die jeweilige Ausgabe hierher.  
2. Wenn im Log (Schritt 3) Fehlermeldungen auftauchen, poste die letzten Zeilen.  

Damit sehen wir sofort, ob der Dienst selbst klemmt oder das Port-Setup.

### 9. Benutzer

fehler wurde gefunden

### 10. Assistent

Super – das ist schon die halbe Miete!  
Magst du kurz beschreiben, **welcher Fehler genau** aufgetaucht ist (z. B. Log-Zeilen oder falsches Port-Mapping), bzw. was du jetzt in den Logs oder den Container-Einstellungen gesehen hast? Dann kann ich dir Schritt für Schritt zeigen, wie du ihn sauber behebst.
