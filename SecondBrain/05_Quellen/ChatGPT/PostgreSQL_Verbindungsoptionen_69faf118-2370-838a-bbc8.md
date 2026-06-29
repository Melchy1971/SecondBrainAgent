---
title: "PostgreSQL Verbindungsoptionen"
type: chatgpt_conversation
source: chatgpt
source_id: "69faf118-2370-838a-bbc8-2ddaa34ad42d"
created: 2026-05-06
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# PostgreSQL Verbindungsoptionen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69faf118-2370-838a-bbc8-2ddaa34ad42d`
- Nachrichten: 57

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Nächste sinnvolle Schritte:



Port 5432 für eingehende Verbindungen von dieser Umgebung freischalten oder IP-Whitelist anpassen.

Alternativ eine per VPN oder SSH-Tunnel erreichbare Adresse bereitstellen.

Wenn du willst, kann ich sofort noch einen kurzen, nicht-destruktiven reinen Verbindungscheck gegen Host/Port/DB-Login ausführen, sobald die Erreichbarkeit angepasst wurde.

### 2. Assistent

Zielzustand: deterministische, abgesicherte Erreichbarkeit von entity["software","PostgreSQL","relational database system"] auf Port 5432 bei minimaler Angriffsfläche.

---

### Option A: Direkte Freigabe (IP-Whitelist)

**Annahmen**
- Statische oder stabil zuordenbare Quell-IP der aufrufenden Umgebung
- Netzwerkpfad ohne zusätzliche NAT-/Proxy-Ebenen, die Quell-IP verändern

**Schritte**
1. **Firewall-Regel**
   - Allow `tcp/5432` *nur* von spezifischer Quell-IP/Range (`/32` bevorzugt)
   - Deny all als Default
2. **Host-Firewall (z. B. `ufw`/`iptables`)**
   - Spiegeln der Cloud-Regel auf Instanzebene
3. **`pg_hba.conf`**
   - Eintrag: `hostssl <db> <user> <source_ip>/32 scram-sha-256`
   - Reihenfolge prüfen (first-match)
4. **TLS erzwingen**
   - `ssl = on`, gültiges Zertifikat
5. **Auth-Härtung**
   - `password_encryption = scram-sha-256`
   - Kein `trust`, kein `md5`
6. **Ratenbegrenzung / Fail2ban**
   - Schutz gegen Brute Force
7. **Logging**
   - `log_connections = on`, `log_disconnections = on`

**Risiken / Trade-offs**
- Exponierter Port → Scan-/Brute-Force-Oberfläche
- IP-Drift → Verbindungsabbrüche
- Fehlkonfiguration in `pg_hba.conf` → Lockout

---

### Option B: SSH-Tunnel (empfohlen für punktuelle Zugriffe)

**Annahmen**
- SSH-Zugang auf Bastion/DB-Host vorhanden
- Key-basierte Authentifizierung

**Schritte**
1. **Bastion festlegen** (kein direkter DB-Zugriff von außen)
2. **Tunnel**
   - `ssh -N -L 5432:127.0.0.1:5432 user@bastion`
   - Lokal: Verbindung auf `localhost:5432`
3. **`pg_hba.conf`**
   - Erlaubt nur `127.0.0.1/32` (oder Bastion-IP)
4. **SSH-Härtung**
   - `PasswordAuthentication no`, `AllowUsers`, `Fail2ban`
5. **Port-Weiterleitung einschränken**
   - `AllowTcpForwarding yes` nur für benötigte User

**Risiken / Trade-offs**
- Single Point (Bastion)
- Operative Komplexität (Tunnel-Handling)
- Performance-Overhead minimal, aber vorhanden

---

### Option C: VPN (dauerhafte, skalierbare Lösung)

**Annahmen**
- Mehrere Clients/Services benötigen Zugriff
- Zentrale Identitäts- und Netzsteuerung gewünscht

**Schritte**
1. **VPN bereitstellen** (z. B. entity["software","WireGuard","vpn protocol"])
2. **Adressraum definieren** (z. B. `10.8.0.0/24`)
3. **Routing**
   - DB-Subnetz nur intern erreichbar
4. **Firewall**
   - `tcp/5432` nur aus VPN-Subnetz
5. **`pg_hba.conf`**
   - `hostssl <db> <user> 10.8.0.0/24 scram-sha-256`
6. **Key/Peer-Management**
   - Rotation, Revocation

**Risiken / Trade-offs**
- Initialer Setup-Aufwand
- Betriebsverantwortung (Keys, Peers, Monitoring)

---

### Validierung (nicht-destruktiv)

**Netzwerk**
- `nc -vz <host> 5432` oder `telnet <host> 5432`
- Erwartung: TCP SYN/ACK

**TLS/Handshake**
- `openssl s_client -starttls postgres -connect <host>:5432`

**DB-Login (Read-only)**
- `psql "host=<host> port=5432 dbname=<db> user=<user> sslmode=require" -c '\conninfo'`

**Erfolgskriterien**
- TCP connect < 100 ms (intra-EU typ.)
- TLS negotiated (kein Fallback)
- `pg_hba` match korrekt (keine `no pg_hba.conf entry` Fehler)

---

### Hidden Dependencies / Failure Modes
- **Cloud LB/Proxy** ersetzt Quell-IP → Whitelist greift nicht
- **IPv6** aktiv → Regeln nur für IPv4 gesetzt
- **DNS Drift** → falscher Host angesprochen
- **Conn Limits** (`max_connections`) erreicht → scheinbare Netzwerkfehler
- **Idle Timeouts** in NAT/VPN → sporadische Drops
- **Clock Skew** → TLS-Fehler

---

### Entscheidung
- **Einzelner Operator, temporär** → SSH-Tunnel
- **Feste Quelle, geringer Aufwand** → IP-Whitelist + TLS
- **Mehrere Konsumenten, langfristig** → VPN

--- 

Nach Anpassung der Erreichbarkeit: reiner Verbindungscheck wie oben spezifiziert durchführen.

### 3. Benutzer

option c

### 4. Assistent

Ziel: isolierter, auditierbarer Zugriff auf entity["software","PostgreSQL","relational database system"] über ein privates Overlay-Netz mittels entity["software","WireGuard","vpn protocol"]. Keine öffentliche Exposition von `tcp/5432`.

---

## Architektur

**Komponenten**
- VPN-Server (Bastion oder dedizierte VM)
- DB-Host (PostgreSQL)
- Clients (Operatoren/Services)

**Adressierung (Beispiel)**
- VPN-Netz: `10.8.0.0/24`
- VPN-Server: `10.8.0.1`
- DB-Host (im selben VPC/Subnetz): `10.0.1.10`
- Clients: `10.8.0.10+`

**Datenpfad**
Client → WireGuard (UDP/51820) → VPN-Server → internes Routing → DB-Host:5432

**Sicherheitsprinzip**
- Öffentliche Freigabe nur `udp/51820` am VPN-Server
- `tcp/5432` ausschließlich aus `10.8.0.0/24` erreichbar

---

## Konfiguration

### 1) VPN-Server (WireGuard)

`/etc/wireguard/wg0.conf`
```
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = <server_private_key>

# NAT ins VPC (falls nötig)
PostUp   = iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
PostDown = iptables -t nat -D POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
```

Pro Client:
```
[Peer]
PublicKey = <client_pub>
AllowedIPs = 10.8.0.10/32
```

**Firewall (Server)**
- Allow `udp/51820` (0.0.0.0/0 oder eingeschränkt auf bekannte IPs)
- Deny inbound sonst

**Kernel**
- `net.ipv4.ip_forward=1`

---

### 2) Client

`wg0.conf`
```
[Interface]
Address = 10.8.0.10/32
PrivateKey = <client_private_key>
DNS = <internal_dns_optional>

[Peer]
PublicKey = <server_pub>
Endpoint = <server_public_ip>:51820
AllowedIPs = 10.8.0.0/24, 10.0.1.0/24
PersistentKeepalive = 25
```

---

### 3) DB-Host (PostgreSQL)

**Firewall**
- Allow `tcp/5432` **nur** von `10.8.0.0/24`
- Deny sonst

**postgresql.conf**
```
listen_addresses = '10.0.1.10'   # oder '0.0.0.0' + Firewall strikt
ssl = on
password_encryption = scram-sha-256
```

**pg_hba.conf**
```
hostssl  <db>  <user>  10.8.0.0/24  scram-sha-256
```

---

## Validierung

**VPN**
- `wg show` → Handshake < 2 min, Rx/Tx Zähler steigen
- `ping 10.8.0.1` (Server), `ping 10.0.1.10` (DB-Host)

**Port**
- `nc -vz 10.0.1.10 5432` → success

**TLS/DB**
- `psql "host=10.0.1.10 port=5432 dbname=<db> user=<user> sslmode=require" -c '\conninfo'`

**SLOs**
- Handshake-Latenz < 50 ms (intra-EU)
- Verbindungsaufbau < 200 ms
- 0% Klartext-Verbindungen

---

## Betrieb / Skalierung

**Key-Management**
- Rotation ≤ 90 Tage
- Revocation: Peer entfernen + Firewall optional härten

**Onboarding**
- Pro Client eindeutige `/32`
- Keine geteilten Keys

**Observability**
- `wg show all dump` in Metriken überführen
- PostgreSQL: `log_connections`, `log_hostname=off` (Performance), `log_line_prefix` mit `%h`

**Kapazität**
- WireGuard: ~1–2 Gbit/s pro vCPU (abhängig von AES-NI/ChaCha20)
- PostgreSQL: `max_connections` vs. Pooling (pgBouncer erwägen)

---

## Risiken / Failure Modes

- **MTU/MSS**: Fragmentierung → sporadische Timeouts → `MTU 1380–1420` testen
- **NAT Idle**: Verbindungsabbrüche → `PersistentKeepalive=25`
- **Routen-Leaks**: falsche `AllowedIPs` → Traffic umgeleitet
- **IPv6**: unbeabsichtigte Offenheit, falls aktiviert aber ungefiltert
- **Zeitdrift**: selten relevant für WireGuard, kritisch für TLS-Validierung
- **Single VPN-Server**: Ausfall → kein DB-Zugriff (HA via zweiter Peer/Anycast)

---

## Entscheidungskriterien (konkret)

- ≥2 unabhängige Clients/Services → VPN
- Compliance-Anforderung „no public DB port“ → VPN zwingend
- Häufige IP-Änderungen auf Client-Seite → VPN statt Whitelist

---

## Härtung (optional)

- UDP/51820 per Geo/IP einschränken
- Port-Knocking/SPA vor WireGuard
- mTLS auf DB (Client-Zertifikate) zusätzlich zu SCRAM
- Bastion ohne SSH (nur WireGuard), separates Admin-Zugangsmodell

---

### 5. Benutzer

Execution complete: Teste PostgreSQL-Zugriff mit den angegebenen Zugangsdaten.

Ran terminal command: psql "host=85.215.131.200 port=5432 dbname=wissen2026 user=appuser password=Markus..2026" -c "SELECT version();"
Completed with input: psql "host=85.215.131.200 port=5432 dbname=wissen2026 user=appuser password=Markus..2026" -c "SELECT version();"

Ran terminal command: Get-Command psql
Completed with input: Get-Command psql

Ran terminal command: Get-ChildItem -Path "C:\Program Files\PostgreSQL" -Recurse -Filter "psql.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
Completed with input: Get-ChildItem -Path "C:\Program Files\PostgreSQL" -Recurse -Filter "psql.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName

Ran terminal command: const { Client } = require('pg'); const client = new Client({ host: '85.215.131.200', port: 5432, database: 'wissen2026', user: 'appuser', password: 'Markus..2026' }); client.connect().then(() => client.query('SELECT version()')).then(res => { console.log(res.rows[0]); client.end(); }).catch(e => { console.error(e); process.exit(1); });
Completed with input: const { Client } = require('pg'); const client = new Client({ host: '85.215.131.200', port: 5432, database: 'wissen2026', user: 'appuser', password: 'Markus..2026' }); client.connect().then(() => client.query('SELECT version()')).then(res => { console.log(res.rows[0]); client.end(); }).catch(e => { console.error(e); process.exit(1); });

Ran terminal command: npm install pg

Ran terminal command: const { Client } = require('pg'); const client = new Client({ host: '85.215.131.200', port: 5432, database: 'wissen2026', user: 'appuser', password: 'Markus..2026' }); client.connect().then(() => client.query('SELECT version()')).then(res => { console.log(res.rows[0]); client.end(); }).catch(e => { console.error(e); process.exit(1); });
Completed with input: const { Client } = require('pg'); const client = new Client({ host: '85.215.131.200', port: 5432, database: 'wissen2026', user: 'appuser', password: 'Markus..2026' }); client.connect().then(() => client.query('SELECT version()')).then(res => { console.log(res.rows[0]); client.end(); }).catch(e => { console.error(e); process.exit(1); });

Ran terminal command: Test-NetConnection -ComputerName 85.215.131.200 -Port 5432

Ran terminal command: const { Client } = require('pg'); const client = new Client({ host: 'localhost', port: 5432, database: 'wissen2026', user: 'appuser', password: 'Markus..2026' }); client.connect().then(() => client.query('SELECT version()')).then(res => { console.log(res.rows[0]); client.end(); }).catch(e => { console.error(e); process.exit(1); });
Completed with input: const { Client } = require('pg'); const client = new Client({ host: 'localhost', port: 5432, database: 'wissen2026', user: 'appuser', password: 'Markus..2026' }); client.connect().then(() => client.query('SELECT version()')).then(res => { console.log(res.rows[0]); client.end(); }).catch(e => { console.error(e); process.exit(1); });

Der Zugriff auf die Datenbank unter 85.215.131.200:5432 ist aktuell **nicht möglich**:

- Die Verbindung wird abgelehnt (ECONNREFUSED).
- Auch ein direkter Netzwerk-Test (Test-NetConnection) zeigt: Port 5432 ist nicht erreichbar.

**Mögliche Ursachen:**
- Die Datenbank läuft nicht oder ist nicht erreichbar.
- Firewall oder Netzwerkrichtlinie blockiert den Zugriff.
- Der Port ist nicht offen oder wird nicht weitergeleitet.
- Die Zugangsdaten stimmen, aber der Server ist nicht erreichbar.

**Empfehlung:**
- Prüfe, ob die Datenbank auf dem Server läuft und externe Verbindungen erlaubt.
- Prüfe Firewall-Einstellungen am Server und ggf. am lokalen Rechner.
- Stelle sicher, dass der Port 5432 offen ist.
- Teste ggf. mit einem lokalen psql-Client oder Admin-Tool direkt auf dem Server.

Melde dich, wenn du weitere Diagnoseschritte oder Unterstützung brauchst!

### 6. Assistent

Befund bestätigt: **kein Auth-/Credential-Problem nachweisbar**, weil der TCP-Verbindungsaufbau bereits scheitert.

Priorität:

1. **Passwort sofort rotieren**
   - Credential wurde im Klartext geteilt.
   - Neues Passwort setzen.
   - Alte Sessions beenden.

2. **Auf DB-Server prüfen**
   ```bash
   sudo systemctl status postgresql
   sudo ss -ltnp | grep 5432
   ```

3. **PostgreSQL Binding prüfen**
   ```bash
   sudo grep listen_addresses /etc/postgresql/*/main/postgresql.conf
   ```
   Erwartung für VPN/extern:
   ```conf
   listen_addresses = '*'
   ```
   oder gezielt interne/VPN-IP.

4. **Firewall prüfen**
   ```bash
   sudo ufw status verbose
   sudo iptables -S
   ```

5. **Cloud/Ionos-Firewall prüfen**
   - Inbound `tcp/5432` aktuell vermutlich geschlossen.
   - Für Option C nicht öffentlich öffnen.
   - Erlauben nur aus VPN-Subnetz, z. B. `10.8.0.0/24`.

6. **pg_hba.conf**
   ```conf
   hostssl wissen2026 appuser 10.8.0.0/24 scram-sha-256
   ```

7. **Reload**
   ```bash
   sudo systemctl reload postgresql
   ```

Kernentscheidung: Nicht `85.215.131.200:5432` öffentlich erreichbar machen. Erst WireGuard/VPN fertigstellen, dann Zugriff gegen die interne DB-IP testen.

### 7. Benutzer

-bash: /root/.openclaw/completions/openclaw.bash: No such file or directory
[root@localhost ~]# sudo systemctl status postgresql
sudo ss -ltnp | grep 5432
Unit postgresql.service could not be found.
LISTEN 0      200                      127.0.0.1:5432       0.0.0.0:*    users:(("postgres",pid=1183,fd=8))             
LISTEN 0      200                          [::1]:5432          [::]:*    users:(("postgres",pid=1183,fd=7))

### 8. Assistent

Befund:

- PostgreSQL läuft.
- Service heißt nicht `postgresql.service`, sondern vermutlich distributions-/versionsspezifisch.
- PostgreSQL hört **nur lokal**:
  - `127.0.0.1:5432`
  - `[::1]:5432`
- Deshalb ist Zugriff auf `85.215.131.200:5432` korrekt abgelehnt.

Nächste Befehle:

```bash
ps aux | grep '[p]ostgres'
sudo systemctl list-units --type=service | grep -i postgres
sudo systemctl list-unit-files | grep -i postgres
```

Konfigurationsdatei finden:

```bash
sudo -u postgres psql -c "SHOW config_file;"
sudo -u postgres psql -c "SHOW hba_file;"
sudo -u postgres psql -c "SHOW listen_addresses;"
```

Für Option C später setzen:

```conf
listen_addresses = '127.0.0.1,10.8.0.1'
```

oder, falls DB-Host selbst im VPN hängt:

```conf
listen_addresses = '127.0.0.1,10.8.0.<db-host>'
```

Nicht setzen, solange Firewall/VPN nicht sauber steht:

```conf
listen_addresses = '*'
```

Nach Änderung:

```bash
sudo systemctl restart <postgres-service-name>
sudo ss -ltnp | grep 5432
```

Erwartung nach korrekter VPN-Bindung:

```text
LISTEN ... 127.0.0.1:5432
LISTEN ... 10.8.0.x:5432
```

Aktueller Kernfehler: PostgreSQL ist nicht extern gebunden. Kein Credential-Problem.

### 9. Benutzer

[root@localhost ~]# ps aux | grep '[p]ostgres'
sudo systemctl list-units --type=service | grep -i postgres
sudo systemctl list-unit-files | grep -i postgres
postgres    1183  0.0  0.3 215152 28172 ?        Ss   08:35   0:00 /usr/pgsql-17/bin/postgres -D /var/lib/pgsql/17/data/
postgres    1221  0.0  0.0  68736  6900 ?        Ss   08:35   0:00 postgres: logger
postgres    1225  0.0  0.1 215284 10136 ?        Ss   08:35   0:00 postgres: checkpointer
postgres    1226  0.0  0.1 215308  8340 ?        Ss   08:35   0:00 postgres: background writer
postgres    1239  0.0  0.1 215152 11144 ?        Ss   08:35   0:00 postgres: walwriter
postgres    1240  0.0  0.1 216728 10416 ?        Ss   08:35   0:00 postgres: autovacuum launcher
postgres    1241  0.0  0.1 216736  9508 ?        Ss   08:35   0:00 postgres: logical replication launcher
systemd+    2628  0.0  0.3 216732 27636 ?        Ss   08:35   0:00 postgres
systemd+    3144  0.0  0.1 216864  9240 ?        Ss   08:35   0:00 postgres: checkpointer
systemd+    3145  0.0  0.0 216888  6976 ?        Ss   08:35   0:00 postgres: background writer
systemd+    3151  0.0  0.1 216732 10044 ?        Ss   08:35   0:00 postgres: walwriter
systemd+    3152  0.0  0.1 218328  8608 ?        Ss   08:35   0:00 postgres: autovacuum launcher
systemd+    3153  0.0  0.0 218316  7784 ?        Ss   08:35   0:00 postgres: logical replication launcher
systemd+    6661  0.0  0.2 219532 17128 ?        Ss   09:42   0:00 postgres: postgres app 172.20.0.2(50978) idle
  postgresql-17.service              loaded active running PostgreSQL 17 database server
postgresql-17.service                                                         enabled         disabled

### 10. Assistent

Befund: Es laufen **zwei PostgreSQL-Instanzen**.

1. Native PostgreSQL 17:
```text
/usr/pgsql-17/bin/postgres -D /var/lib/pgsql/17/data/
postgresql-17.service
```

2. Zweite Instanz mit User `systemd+`, vermutlich Container/Podman:
```text
postgres: postgres app 172.20.0.2(50978) idle
```

Aktiver Service für die native Instanz:

```bash
sudo systemctl status postgresql-17
```

Konfiguration der nativen Instanz prüfen:

```bash
sudo -u postgres /usr/pgsql-17/bin/psql -p 5432 -c "SHOW config_file;"
sudo -u postgres /usr/pgsql-17/bin/psql -p 5432 -c "SHOW hba_file;"
sudo -u postgres /usr/pgsql-17/bin/psql -p 5432 -c "SHOW listen_addresses;"
```

Direkte Datei wahrscheinlich:

```bash
sudo vi /var/lib/pgsql/17/data/postgresql.conf
sudo vi /var/lib/pgsql/17/data/pg_hba.conf
```

Für aktuellen externen Test über Public IP:

```conf
listen_addresses = '*'
```

In `pg_hba.conf` temporär eng setzen, nicht offen:

```conf
hostssl wissen2026 appuser <DEINE_CLIENT_IP>/32 scram-sha-256
```

Für spätere VPN-Variante:

```conf
hostssl wissen2026 appuser 10.8.0.0/24 scram-sha-256
```

Dann:

```bash
sudo systemctl restart postgresql-17
sudo ss -ltnp | grep 5432
```

Erwartung:

```text
0.0.0.0:5432
[::]:5432
```

oder bei VPN-Bindung:

```text
10.8.0.x:5432
```

Wichtig: Public-IP-Test funktioniert erst, wenn zusätzlich OS-/Ionos-Firewall `tcp/5432` von der Client-IP erlaubt.

### 11. Benutzer

ich möchte nur eine db haben

### 12. Assistent

Ziel: **eine PostgreSQL-Instanz, ein Datenverzeichnis, ein Port 5432**.

Aktuell laufen zwei Instanzen. Erst identifizieren, welche die echte Produktions-DB enthält.

```bash
sudo -u postgres /usr/pgsql-17/bin/psql -p 5432 -c "\l"
sudo -u postgres /usr/pgsql-17/bin/psql -p 5432 -c "SELECT inet_server_addr(), inet_server_port(), current_database();"
```

Zweite Instanz finden:

```bash
sudo ss -ltnp | grep postgres
ps aux | grep '[p]ostgres'
podman ps
docker ps
```

Wenn `podman ps` oder `docker ps` einen PostgreSQL-Container zeigt und du **nur die native Instanz behalten willst**:

```bash
podman stop <container>
podman rm <container>
```

oder:

```bash
docker stop <container>
docker rm <container>
```

Autostart entfernen:

```bash
podman generate systemd --help >/dev/null 2>&1
systemctl list-units | grep -i container
systemctl list-unit-files | grep -i container
```

Native Instanz behalten:

```bash
sudo systemctl enable postgresql-17
sudo systemctl restart postgresql-17
sudo ss -ltnp | grep 5432
```

Erwarteter Zielzustand:

```text
postgres ... /usr/pgsql-17/bin/postgres -D /var/lib/pgsql/17/data/
LISTEN ... 127.0.0.1:5432
```

Nicht löschen, bevor klar ist, wo `wissen2026` liegt:

```bash
sudo -u postgres /usr/pgsql-17/bin/psql -p 5432 -c "\l" | grep wissen2026
```

Wenn `wissen2026` nur im Container liegt: erst Dump → Restore in native Instanz.

### 13. Benutzer

postgres deinstallieren

### 14. Assistent

Annahme: Du willst die native entity["software","PostgreSQL","PostgreSQL 17"]-Installation vollständig entfernen und stattdessen nur die Container-/andere Instanz behalten.

Vorher zwingend prüfen, ob dort produktive Daten liegen:

```bash
sudo -u postgres /usr/pgsql-17/bin/psql -p 5432 -c "\l"
```

Wenn `wissen2026` dort sichtbar ist: zuerst Backup.

Backup:

```bash
mkdir -p /root/pg-backup

sudo -u postgres pg_dump -Fc wissen2026 \
  > /root/pg-backup/wissen2026.dump
```

Integrität prüfen:

```bash
ls -lh /root/pg-backup/
```

Dann native Instanz stoppen:

```bash
sudo systemctl stop postgresql-17
sudo systemctl disable postgresql-17
```

RPM-Pakete prüfen:

```bash
rpm -qa | grep -i postgres
```

Deinstallation (Rocky/Alma/RHEL/CentOS typisch):

```bash
sudo dnf remove -y 'postgresql17*'
```

Verbleibende Daten entfernen:

```bash
sudo rm -rf /var/lib/pgsql/17
sudo rm -rf /usr/pgsql-17
```

Systemd reload:

```bash
sudo systemctl daemon-reload
```

Validierung:

```bash
which psql
ps aux | grep '[p]ostgres'
ss -ltnp | grep 5432
```

Erwartung:
- keine native PostgreSQL-Instanz mehr
- Port 5432 nur noch durch die gewünschte Instanz belegt
- kein `postgresql-17.service`

Risiko:
- irreversibler Datenverlust ohne Dump
- möglicherweise nutzt deine Anwendung genau diese Instanz statt des Containers
- Container könnte auf anderes Volume/Data-Dir zeigen

Minimaler Sicherheitscheck vor Löschung:

```bash
sudo -u postgres psql -c "\conninfo"
sudo -u postgres psql -c "SELECT current_database();"
```

### 15. Benutzer

[root@localhost ~]# which psql
ps aux | grep '[p]ostgres'
ss -ltnp | grep 5432
/usr/bin/which: no psql in (/root/.nvm/versions/node/v24.15.0/bin:/root/.local/bin:/root/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/var/lib/snapd/snap/bin)
systemd+    2628  0.0  0.3 216732 27636 ?        Ss   08:35   0:00 postgres
systemd+    3144  0.0  0.1 216864  9240 ?        Ss   08:35   0:00 postgres: checkpointer
systemd+    3145  0.0  0.0 216888  6976 ?        Ss   08:35   0:00 postgres: background writer
systemd+    3151  0.0  0.1 216732 10044 ?        Ss   08:35   0:00 postgres: walwriter
systemd+    3152  0.0  0.1 218328  8608 ?        Ss   08:35   0:00 postgres: autovacuum launcher
systemd+    3153  0.0  0.0 218316  7784 ?        Ss   08:35   0:00 postgres: logical replication launcher
systemd+    6767  0.0  0.2 219532 17128 ?        Ss   09:48   0:00 postgres: postgres app 172.20.0.2(52294) idle

### 16. Assistent

Befund:

- Native PostgreSQL 17 wurde erfolgreich entfernt.
- `psql` existiert nicht mehr.
- Port 5432 wird aktuell nicht mehr öffentlich/native gebunden angezeigt.
- Verbleibende Prozesse gehören sehr wahrscheinlich zu einer Container-Instanz.

Entscheidend:
```text
172.20.0.2
```

Das ist typisch Docker/Podman Bridge-Netzwerk.

Jetzt identifizieren, welcher Container läuft:

```bash
docker ps -a
podman ps -a
```

Dann prüfen, ob Port-Mapping existiert:

```bash
docker port <container>
```

oder:

```bash
podman port <container>
```

Falls kein Mapping auf Host-Port 5432 existiert, Container neu starten mit:

Docker:
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_DB=wissen2026 \
  -e POSTGRES_USER=appuser \
  -e POSTGRES_PASSWORD='NEUES_PASSWORT' \
  -p 5432:5432 \
  postgres:17
```

Oder Podman:
```bash
podman run -d \
  --name postgres \
  -e POSTGRES_DB=wissen2026 \
  -e POSTGRES_USER=appuser \
  -e POSTGRES_PASSWORD='NEUES_PASSWORT' \
  -p 5432:5432 \
  docker.io/postgres:17
```

Danach prüfen:

```bash
ss -ltnp | grep 5432
```

Erwartung:
```text
0.0.0.0:5432
```

Dann extern testen:

```bash
nc -vz 85.215.131.200 5432
```

Wichtig:
- Firewall/Ionos-Regeln müssen `tcp/5432` erlauben.
- Passwort rotieren. Das alte Credential ist kompromittiert.

### 17. Benutzer

[root@localhost ~]# docker ps -a
podman ps -a
CONTAINER ID   IMAGE           COMMAND                  CREATED       STATUS             PORTS                                                                                                                       NAMES
1a6cc15e5c86   ad20607cdd24    "tini -- /docker-ent…"   3 weeks ago   Up About an hour   5678/tcp                                                                                                                    n8n
23f41e0b042a   postgres:16     "docker-entrypoint.s…"   3 weeks ago   Up About an hour   5432/tcp                                                                                                                    postgres
38a6d16dcfa8   nginx:alpine    "/docker-entrypoint.…"   3 weeks ago   Up About an hour   80/tcp                                                                                                                      site
0ac463a633bf   traefik:v2.11   "/entrypoint.sh --ap…"   3 weeks ago   Up About an hour   0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp, 0.0.0.0:7687->7687/tcp, [::]:7687->7687/tcp   traefik
CONTAINER ID  IMAGE                               COMMAND        CREATED      STATUS                  PORTS                   NAMES
a4d422f36dc1  ghcr.io/open-webui/open-webui:main  bash start.sh  4 weeks ago  Created                 0.0.0.0:3000->8080/tcp  ecstatic_burnell
f5d061328326  ghcr.io/open-webui/open-webui:main  bash start.sh  4 weeks ago  Exited (0) 2 weeks ago  0.0.0.0:3001->8080/tcp  vigorous_ganguly
090581f31788  ghcr.io/open-webui/open-webui:main  bash start.sh  4 weeks ago  Created                 0.0.0.0:3001->8080/tcp  recursing_shtern

### 18. Assistent

Befund:

- Gewünschte DB ist Container:
  ```text
  postgres:16  NAMES=postgres
  ```
- Problem:
  ```text
  PORTS 5432/tcp
  ```
  Bedeutet: PostgreSQL lauscht **nur im Docker-Netz**, nicht auf dem Host. Es fehlt:
  ```text
  0.0.0.0:5432->5432/tcp
  ```

Prüfen:

```bash
docker inspect postgres --format '{{json .NetworkSettings.Ports}}'
docker exec -it postgres psql -U appuser -d wissen2026 -c "SELECT version();"
```

Für Host-Port freigeben: Container muss neu erstellt werden. Ports lassen sich nicht nachträglich sauber hinzufügen.

Backup:

```bash
docker exec postgres pg_dump -U appuser -d wissen2026 -Fc > /root/wissen2026.dump
```

Container stoppen und entfernen:

```bash
docker stop postgres
docker rm postgres
```

Neu starten mit Port-Mapping und persistentem Volume. Zuerst Volume-Namen prüfen:

```bash
docker inspect postgres --format '{{range .Mounts}}{{.Name}} {{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

Falls bereits ein Volume existiert, dieses beim neuen Container wiederverwenden:

```bash
docker run -d \
  --name postgres \
  --restart unless-stopped \
  -e POSTGRES_DB=wissen2026 \
  -e POSTGRES_USER=appuser \
  -e POSTGRES_PASSWORD='NEUES_PASSWORT' \
  -p 5432:5432 \
  -v <VOLUME_ODER_PFAD>:/var/lib/postgresql/data \
  postgres:16
```

Validierung:

```bash
docker ps
ss -ltnp | grep 5432
docker exec -it postgres psql -U appuser -d wissen2026 -c "SELECT version();"
```

Erwartung:

```text
0.0.0.0:5432->5432/tcp
```

Sicherer für Option C:

```bash
-p 10.8.0.1:5432:5432
```

Dann ist die DB nur über VPN-Interface erreichbar, nicht öffentlich.

### 19. Benutzer

[root@localhost ~]# docker ps
CONTAINER ID   IMAGE           COMMAND                  CREATED       STATUS             PORTS                                                                                                                       NAMES
1a6cc15e5c86   ad20607cdd24    "tini -- /docker-ent…"   3 weeks ago   Up About an hour   5678/tcp                                                                                                                    n8n
38a6d16dcfa8   nginx:alpine    "/docker-entrypoint.…"   3 weeks ago   Up About an hour   80/tcp                                                                                                                      site
0ac463a633bf   traefik:v2.11   "/entrypoint.sh --ap…"   3 weeks ago   Up About an hour   0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp, 0.0.0.0:7687->7687/tcp, [::]:7687->7687/tcp   traefik

### 20. Assistent

`postgres` läuft nicht mehr.

Jetzt prüfen, ob Container nur gestoppt oder entfernt ist:

```bash
docker ps -a | grep postgres
docker volume ls
```

Wenn Container noch existiert:

```bash
docker start postgres
docker ps | grep postgres
```

Wenn Container gelöscht wurde, aber Volume existiert:

```bash
docker run -d \
  --name postgres \
  --restart unless-stopped \
  -p 5432:5432 \
  -v <VOLUME_NAME>:/var/lib/postgresql/data \
  postgres:16
```

Wenn kein Volume existiert, aus Dump wiederherstellen:

```bash
docker run -d \
  --name postgres \
  --restart unless-stopped \
  -e POSTGRES_DB=wissen2026 \
  -e POSTGRES_USER=appuser \
  -e POSTGRES_PASSWORD='NEUES_PASSWORT' \
  -p 5432:5432 \
  postgres:16
```

Dann:

```bash
cat /root/wissen2026.dump | docker exec -i postgres pg_restore -U appuser -d wissen2026
```

Validierung:

```bash
docker ps | grep postgres
ss -ltnp | grep 5432
docker exec -it postgres psql -U appuser -d wissen2026 -c "SELECT version();"
```

### 21. Benutzer

[root@localhost ~]# docker ps -a | grep postgres
docker volume ls
DRIVER    VOLUME NAME
local     n8n-neo4j_n8n_data
local     n8n_data
local     stack_n8n_data
local     stack_postgres_data
local     stack_stack_n8n_data
local     stack_stack_postgres_data

### 22. Assistent

Postgres-Container ist gelöscht. Relevante Volumes sind vermutlich:

```text
stack_postgres_data
stack_stack_postgres_data
```

Jetzt Inhalt prüfen, ohne Daten zu verändern:

```bash
docker run --rm -v stack_postgres_data:/data alpine ls -la /data
docker run --rm -v stack_stack_postgres_data:/data alpine ls -la /data
```

Das echte PostgreSQL-Volume enthält Dateien wie:

```text
PG_VERSION
base/
global/
pg_wal/
postgresql.conf
```

Dann Container mit dem richtigen Volume starten:

```bash
docker run -d \
  --name postgres \
  --restart unless-stopped \
  -p 5432:5432 \
  -v stack_postgres_data:/var/lib/postgresql/data \
  postgres:16
```

Falls das falsche Volume war:

```bash
docker logs postgres
docker rm -f postgres
```

Dann mit dem anderen Volume:

```bash
docker run -d \
  --name postgres \
  --restart unless-stopped \
  -p 5432:5432 \
  -v stack_stack_postgres_data:/var/lib/postgresql/data \
  postgres:16
```

Validierung:

```bash
docker ps | grep postgres
ss -ltnp | grep 5432
docker exec -it postgres psql -U appuser -d wissen2026 -c "SELECT version();"
```

Sicherer Zielzustand für VPN später:

```bash
-p 10.8.0.1:5432:5432
```

Aktuell für externen Test:

```bash
-p 5432:5432
```

### 23. Assistent

Achtung: Löschen eines Docker-Volumes ist irreversibel. Alle Datenbanken darin gehen verloren.

Volumes prüfen:

```bash
docker volume ls
```

Ein einzelnes Volume löschen:

```bash
docker volume rm stack_postgres_data
```

oder:

```bash
docker volume rm stack_stack_postgres_data
```

Mehrere gleichzeitig:

```bash
docker volume rm stack_postgres_data stack_stack_postgres_data
```

Falls „volume is in use“:

```bash
docker ps -a
docker rm -f postgres
```

Dann erneut löschen.

Nicht verwendete Volumes komplett bereinigen:

```bash
docker volume prune -f
```

Validierung:

```bash
docker volume ls
```

Konsequenz:
- `wissen2026` und alle Tabellen dauerhaft gelöscht, falls dort gespeichert.
- Kein Recovery ohne externes Backup/Dump.

### 24. Benutzer

volume löschen

### 25. Benutzer

installation presql 18

### 26. Assistent

Installation von entity["software","PostgreSQL","PostgreSQL 18"] auf RHEL/Rocky/Alma/CentOS-ähnlichem System.

Vorher sicherstellen:
- Alte Container gestoppt
- Alte Volumes gelöscht
- Port 5432 frei

Prüfen:

```bash id="a2r1gi"
ss -ltnp | grep 5432
docker ps -a
```

---

## 1. PostgreSQL Repository installieren

```bash id="e3d56h"
sudo dnf install -y \
https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
```

---

## 2. Standard-Modul deaktivieren

```bash id="z1qk2j"
sudo dnf -qy module disable postgresql
```

---

## 3. PostgreSQL 18 installieren

```bash id="g8o9vn"
sudo dnf install -y postgresql18-server postgresql18
```

---

## 4. Datenbank initialisieren

```bash id="l7p3cw"
sudo /usr/pgsql-18/bin/postgresql-18-setup initdb
```

---

## 5. Service aktivieren/starten

```bash id="y2h6ab"
sudo systemctl enable postgresql-18
sudo systemctl start postgresql-18
```

---

## 6. Status prüfen

```bash id="b9d0rf"
sudo systemctl status postgresql-18
ss -ltnp | grep 5432
```

Erwartung:

```text id="4suv2n"
127.0.0.1:5432
```

---

## 7. Passwort setzen

```bash id="n6k8tp"
sudo -u postgres psql
```

Dann:

```sql id="d5q7xl"
ALTER USER postgres WITH PASSWORD 'NEUES_STARKES_PASSWORT';
CREATE DATABASE wissen2026;
CREATE USER appuser WITH ENCRYPTED PASSWORD 'NEUES_PASSWORT';
GRANT ALL PRIVILEGES ON DATABASE wissen2026 TO appuser;
\q
```

---

## 8. Externen Zugriff konfigurieren

Datei:

```bash id="w3m1hs"
sudo vi /var/lib/pgsql/18/data/postgresql.conf
```

Setzen:

```conf id="d0r8az"
listen_addresses = '*'
password_encryption = scram-sha-256
ssl = on
```

---

## 9. Zugriff beschränken

Datei:

```bash id="q5v2ue"
sudo vi /var/lib/pgsql/18/data/pg_hba.conf
```

VPN-only:

```conf id="3e6cpt"
hostssl wissen2026 appuser 10.8.0.0/24 scram-sha-256
```

Temporär externe Einzel-IP:

```conf id="m9x4fd"
hostssl wissen2026 appuser <DEINE_IP>/32 scram-sha-256
```

---

## 10. Neustart

```bash id="t8b1vn"
sudo systemctl restart postgresql-18
```

---

## 11. Firewall

Temporär:

```bash id="k2f7ju"
sudo firewall-cmd --permanent \
  --add-port=5432/tcp

sudo firewall-cmd --reload
```

Besser:

```bash id="p4w8le"
sudo firewall-cmd --permanent \
  --add-rich-rule='rule family="ipv4" \
  source address="10.8.0.0/24" \
  port protocol="tcp" port="5432" accept'

sudo firewall-cmd --reload
```

---

## 12. Verbindungstest

Lokal:

```bash id="c7s9na"
psql -U appuser -d wissen2026 -h 127.0.0.1
```

Extern:

```bash id="f1v6ok"
nc -vz <SERVER-IP> 5432
```

---

## Zielzustand

```text id="b3u5md"
postgresql-18.service active(running)
0.0.0.0:5432 LISTEN
SCRAM auth enabled
Firewall restricted
Single DB instance
```

### 27. Assistent

Der Fehler betrifft nur die erste Zeile. Ursache: unvollständiges oder falsch eingefügtes SQL im entity["software","PostgreSQL","PostgreSQL 18"]-Prompt.

`CREATE DATABASE`, `CREATE ROLE` und `GRANT` wurden erfolgreich ausgeführt.

Jetzt nur das Passwort korrekt setzen:

```sql
ALTER USER postgres WITH PASSWORD 'Markus..2026';
ALTER USER appuser WITH PASSWORD 'Markus..2026';
```

Dann prüfen:

```sql
\du
\l
```

Verbindung testen:

```bash
psql -U appuser -d wissen2026 -h 127.0.0.1
```

Falls externe Verbindungen benötigt werden:

```bash
sudo ss -ltnp | grep 5432
```

Erwartung aktuell wahrscheinlich noch:

```text
127.0.0.1:5432
```

Dann erst `listen_addresses` + `pg_hba.conf` anpassen.

### 28. Benutzer

postgres-# ALTER USER postgres WITH PASSWORD 'Markus..2026';
CREATE DATABASE wissen2026;
CREATE USER appuser WITH ENCRYPTED PASSWORD 'Markus..2026';
GRANT ALL PRIVILEGES ON DATABASE wissen2026 TO appuser;
\q
ERROR:  syntax error at or near "Markus"
LINE 1: Markus..2026
        ^
CREATE DATABASE
CREATE ROLE
GRANT

### 29. Benutzer

alteruser war appuser

### 30. Assistent

Dann genügt:

```sql id="3l0j3n"
ALTER USER appuser WITH PASSWORD 'Markus..2026';
```

Prüfen:

```sql id="wtcqht"
\du
```

Verbindung lokal testen:

```bash id="q4q9hn"
psql -U appuser -d wissen2026 -h 127.0.0.1
```

Wenn erfolgreich:
- DB korrekt erstellt
- User korrekt angelegt
- Passwort korrekt gesetzt
- PostgreSQL 18 läuft funktional lokal

Nächster technischer Schritt wäre ausschließlich Netzwerk-/VPN-Freigabe.

### 31. Assistent

Du bist in der Bash-Shell, nicht im entity["software","PostgreSQL","PostgreSQL 18"]-Prompt.

Erst in psql wechseln:

```bash id="s9kh8q"
sudo -u postgres psql
```

Dann dort ausführen:

```sql id="v8j2pd"
ALTER USER appuser WITH PASSWORD 'Markus..2026';
```

Beenden:

```sql id="gh6m1y"
\q
```

Danach Verbindung testen:

```bash id="l1f7cw"
psql -U appuser -d wissen2026 -h 127.0.0.1
```

### 32. Benutzer

[root@localhost ~]# ALTER USER appuser WITH PASSWORD 'Markus..2026';
-bash: ALTER: command not found

### 33. Benutzer

[root@localhost ~]# psql -U appuser -d wissen2026 -h 127.0.0.1
Password for user appuser:
psql (18.4)
Type "help" for help.

wissen2026=>

### 34. Assistent

Status:

- entity["software","PostgreSQL","PostgreSQL 18"] korrekt installiert
- `wissen2026` existiert
- `appuser` funktioniert
- Passwortauthentifizierung erfolgreich
- Lokaler TCP-Zugriff auf `127.0.0.1:5432` funktioniert
- Nur eine aktive DB-Instanz vorhanden

Architekturzustand jetzt konsistent.

Aktuelle Exposition:
```text
localhost only
```

Prüfen:

```sql id="p6y8cb"
SHOW listen_addresses;
```

Nächster kontrollierter Schritt für VPN/externe Nutzung:

```bash id="m3u9dr"
sudo vi /var/lib/pgsql/18/data/postgresql.conf
```

Setzen:

```conf id="y2v4eh"
listen_addresses = '*'
```

Dann:

```bash id="d8n5kt"
sudo vi /var/lib/pgsql/18/data/pg_hba.conf
```

VPN-only:

```conf id="f4c7js"
hostssl wissen2026 appuser 10.8.0.0/24 scram-sha-256
```

Oder temporär Einzel-IP:

```conf id="x7q2la"
hostssl wissen2026 appuser <DEINE_IP>/32 scram-sha-256
```

Neustart:

```bash id="a1k5qo"
sudo systemctl restart postgresql-18
```

Validierung:

```bash id="u9m2zr"
ss -ltnp | grep 5432
```

Erwartung:

```text id="h5r8dv"
0.0.0.0:5432
```

Danach erst Firewall/Ionos-Regeln öffnen.

### 35. Benutzer

[root@localhost ~]# sudo systemctl restart postgresql-18
[root@localhost ~]# ss -ltnp | grep 5432
LISTEN 0      200                      127.0.0.1:5432       0.0.0.0:*    users:(("postgres",pid=8456,fd=8))             
LISTEN 0      200                          [::1]:5432          [::]:*    users:(("postgres",pid=8456,fd=7))

### 36. Assistent

`listen_addresses` ist noch nicht aktiv geändert. PostgreSQL hört weiterhin nur lokal.

Prüfen:

```bash
sudo -u postgres psql -c "SHOW config_file;"
sudo -u postgres psql -c "SHOW listen_addresses;"
```

Dann Datei direkt setzen:

```bash
sudo sed -i "s/^#listen_addresses.*/listen_addresses = '*'/" /var/lib/pgsql/18/data/postgresql.conf
sudo sed -i "s/^listen_addresses.*/listen_addresses = '*'/" /var/lib/pgsql/18/data/postgresql.conf
```

Kontrolle:

```bash
grep "^listen_addresses" /var/lib/pgsql/18/data/postgresql.conf
```

Neustart:

```bash
sudo systemctl restart postgresql-18
ss -ltnp | grep 5432
```

Erwartung:

```text
0.0.0.0:5432
[::]:5432
```

### 37. Benutzer

[root@localhost ~]# sudo -u postgres psql -c "SHOW config_file;"
sudo -u postgres psql -c "SHOW listen_addresses;"
              config_file
----------------------------------------
 /var/lib/pgsql/18/data/postgresql.conf
(1 row)

 listen_addresses
------------------
 localhost
(1 row)

[root@localhost ~]# sudo sed -i "s/^#listen_addresses.*/listen_addresses = '*'/" /var/lib/pgsql/18/data/postgresql.conf
sudo sed -i "s/^listen_addresses.*/listen_addresses = '*'/" /var/lib/pgsql/18/data/postgresql.conf
[root@localhost ~]# grep "^listen_addresses" /var/lib/pgsql/18/data/postgresql.conf
listen_addresses = '*'
[root@localhost ~]# sudo systemctl restart postgresql-18
ss -ltnp | grep 5432
LISTEN 0      200                        0.0.0.0:5432       0.0.0.0:*    users:(("postgres",pid=8502,fd=7))             
LISTEN 0      200                           [::]:5432          [::]:*    users:(("postgres",pid=8502,fd=8))

### 38. Assistent

PostgreSQL bindet jetzt korrekt extern:

```text
0.0.0.0:5432
[::]:5432
```

Jetzt Zugriff begrenzen.

`pg_hba.conf` prüfen:

```bash
sudo vi /var/lib/pgsql/18/data/pg_hba.conf
```

Eintrag setzen:

```conf
hostssl wissen2026 appuser <DEINE_CLIENT_IP>/32 scram-sha-256
```

oder VPN-only:

```conf
hostssl wissen2026 appuser 10.8.0.0/24 scram-sha-256
```

Reload:

```bash
sudo systemctl reload postgresql-18
```

Firewall öffnen, eng begrenzt:

```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<DEINE_CLIENT_IP>/32" port protocol="tcp" port="5432" accept'
sudo firewall-cmd --reload
```

Extern testen:

```bash
psql "host=85.215.131.200 port=5432 dbname=wissen2026 user=appuser sslmode=require"
```

Wichtig: Aktuell lauscht PostgreSQL auf allen Interfaces. Ohne restriktive Firewall/`pg_hba.conf` ist das unnötig exponiert.

### 39. Benutzer

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     peer
# IPv4 local connections:
host    all             all             127.0.0.1/32            scram-sha-256
# IPv6 local connections:
host    all             all             ::1/128                 scram-sha-256
# Allow replication connections from localhost, by a user with the
# replication privilege.
local   replication     all                                     peer
host    replication     all             127.0.0.1/32            scram-sha-256
host    replication     all             ::1/128                 scram-sha-256

### 40. Assistent

`pg_hba.conf` erlaubt aktuell nur lokale Zugriffe. Externe Verbindungen werden blockiert.

Für temporären Zugriff von deiner Client-IP diese Zeile **unter die lokalen Einträge** setzen:

```conf
host    wissen2026     appuser     <DEINE_CLIENT_IP>/32     scram-sha-256
```

Für VPN-only:

```conf
host    wissen2026     appuser     10.8.0.0/24              scram-sha-256
```

Dann reload:

```bash
sudo systemctl reload postgresql-18
```

Firewall ebenfalls eng öffnen:

```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<DEINE_CLIENT_IP>/32" port protocol="tcp" port="5432" accept'
sudo firewall-cmd --reload
```

Validierung:

```bash
sudo -u postgres psql -c "SELECT * FROM pg_hba_file_rules;"
```

Extern:

```bash
psql "host=85.215.131.200 port=5432 dbname=wissen2026 user=appuser"
```

### 41. Benutzer

ich weis nicht wie und wo ich das mache

### 42. Assistent

Du machst es direkt auf dem Server in dieser Datei:

```bash
sudo nano /var/lib/pgsql/18/data/pg_hba.conf
```

Ganz unten neue Zeile einfügen:

```conf
host    wissen2026    appuser    0.0.0.0/0    scram-sha-256
```

Speichern in nano:
```text
CTRL + O
Enter
CTRL + X
```

Dann PostgreSQL neu laden:

```bash
sudo systemctl reload postgresql-18
```

Firewall öffnen:

```bash
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

Test vom anderen Rechner:

```bash
psql "host=85.215.131.200 port=5432 dbname=wissen2026 user=appuser password=Markus..2026"
```

Wichtig: `0.0.0.0/0` erlaubt jede IP. Technisch schnell, aber unsicher. Danach auf feste IP oder VPN begrenzen.

### 43. Assistent

Konfiguration ist jetzt vollständig genug für externe Verbindungen.

Direkt testen:

```bash
psql "host=85.215.131.200 port=5432 dbname=wissen2026 user=appuser password=Markus..2026"
```

Falls `psql` lokal nicht installiert:

Windows:
```powershell
Test-NetConnection 85.215.131.200 -Port 5432
```

Oder mit Node.js:

```javascript
const { Client } = require('pg');

const client = new Client({
  host: '85.215.131.200',
  port: 5432,
  database: 'wissen2026',
  user: 'appuser',
  password: 'Markus..2026',
});

client.connect()
  .then(() => client.query('SELECT NOW()'))
  .then(res => {
    console.log(res.rows);
    client.end();
  })
  .catch(console.error);
```

Wenn Verbindung trotzdem fehlschlägt:

Firewallstatus prüfen:

```bash
sudo firewall-cmd --list-all
```

Oder testweise komplett öffnen:

```bash
sudo firewall-cmd --add-port=5432/tcp --permanent
sudo firewall-cmd --reload
```

Dann erneut testen.

### 44. Assistent

Erfolg bestätigt.

Status:

- entity["software","PostgreSQL","PostgreSQL 18"] läuft korrekt
- Externer TCP-Zugriff funktioniert
- `appuser` authentifiziert erfolgreich
- `wissen2026` erreichbar
- `pg_hba.conf` akzeptiert externe Verbindungen
- Firewall korrekt geöffnet
- Nur eine aktive DB-Instanz vorhanden

Systemzustand jetzt konsistent und funktionsfähig.

Sofortige Härtung empfohlen:

1. Passwort rotieren
   - Credential wurde mehrfach im Klartext verwendet.

```sql
ALTER USER appuser WITH PASSWORD '<NEUES_STARKES_PASSWORT>';
```

2. `0.0.0.0/0` in `pg_hba.conf` entfernen
   - Ersetzen durch feste Client-IP oder VPN-Netz.

3. Firewall einschränken
   - Nicht global `5432/tcp` offen lassen.

4. SSL erzwingen:

```conf
hostssl wissen2026 appuser <IP>/32 scram-sha-256
```

5. Backup aktivieren:

```bash
pg_dump -U appuser wissen2026 > /backup/wissen2026.sql
```

6. Monitoring:

```sql
SELECT client_addr, usename, datname FROM pg_stat_activity;
```

Minimaler Zielzustand:
- keine öffentliche DB ohne IP-Restriktion
- SCRAM aktiv
- regelmäßige Dumps
- VPN mittelfristig statt Public Port 5432

### 45. Benutzer

[root@localhost ~]# psql "host=85.215.131.200 port=5432 dbname=wissen2026 user=appuser password=Markus..2026"
psql (18.4)
Type "help" for help.

wissen2026=>

### 46. Assistent

In entity["software","pgAdmin 4","database administration tool"]:

## Neue Serververbindung

### General
```text
Name: wissen2026
```

---

### Connection

```text
Host name/address: 85.215.131.200
Port: 5432
Maintenance database: wissen2026
Username: appuser
Password: Markus..2026
```

Optional:
```text
Save password: aktiviert
```

---

### SSL

Wenn `hostssl` aktiv:

```text
SSL Mode: Require
```

Falls noch kein SSL-Zertifikat konfiguriert:
```text
SSL Mode: Prefer
```

---

## Verbindung testen

Erwartung:
- Server erscheint links im Tree
- Datenbank `wissen2026` sichtbar
- Query Tool funktioniert

Testquery:

```sql
SELECT version();
SELECT current_database();
SELECT now();
```

---

## Falls Verbindung fehlschlägt

### Timeout
Firewall/Portproblem:
```bash
sudo firewall-cmd --list-ports
```

---

### `no pg_hba.conf entry`
`pg_hba.conf` fehlt:

```conf
host    wissen2026    appuser    0.0.0.0/0    scram-sha-256
```

Reload:
```bash
sudo systemctl reload postgresql-18
```

---

### `password authentication failed`
Passwort neu setzen:

```sql
ALTER USER appuser WITH PASSWORD 'NEUES_PASSWORT';
```

---

### SSL Fehler
Temporär in pgAdmin:
```text
SSL Mode = Prefer
```

---

## Sicherheitszustand aktuell

Momentan vermutlich:
```conf
0.0.0.0/0
```

Das bedeutet:
- jede IP darf Login versuchen
- nur Passwort schützt

Nach erfolgreichem pgAdmin-Test:
- auf feste IP begrenzen
- oder VPN-only umstellen.

### 47. Benutzer

verbindung über pgAdmin 4

### 48. Benutzer

{"asset_pointer": "sediment://file_000000000ed871f4994f279cfd804697", "content_type": "image_asset_pointer", "fovea": null, "height": 183, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 10327, "width": 297}
appuser  als superuder einrichten

### 49. Assistent

In entity["software","PostgreSQL","PostgreSQL 18"] als `postgres` oder bestehender Superuser ausführen:

```sql
ALTER USER appuser WITH SUPERUSER;
```

Prüfen:

```sql
\du
```

Erwartung:

```text
appuser | Superuser, Create role, Create DB, Replication ...
```

Alternativ sicherer für Produktion:

```sql
ALTER USER appuser CREATEDB CREATEROLE;
```

statt vollständigem `SUPERUSER`.

Risiko von `SUPERUSER`:
- vollständiger Systemzugriff innerhalb PostgreSQL
- Extension-Installation
- Rollen-/Rechte-Eskalation
- potenzieller Zugriff auf Server-Dateisystem via COPY/Program Features
- kein effektives Least-Privilege-Modell mehr.

### 50. Benutzer

neuen User Markus mit adminrechten einrichten mit pgAdmin 4

### 51. Assistent

In entity["software","pgAdmin 4","database administration tool"]:

## 1. Login/Group Roles öffnen

Links:

```text
Servers
 └── wissen2026
     └── Login/Group Roles
```

Rechtsklick:
```text
Create → Login/Group Role
```

---

## 2. General

```text
Name: Markus
```

---

## 3. Definition

```text
Password: <STARKES_PASSWORT>
```

Optional:
```text
Confirm password
```

---

## 4. Privileges

Aktivieren:

```text
Can login?                YES
Superuser?                YES
Create roles?             YES
Create databases?         YES
Replication?              optional
Bypass RLS?               optional
```

---

## 5. Save

Danach erscheint:

```text
Login/Group Roles
 └── Markus
```

---

## 6. Testlogin

Neue Verbindung in pgAdmin:

```text
Username: Markus
Password: <PASSWORT>
Database: wissen2026
```

Oder SQL:

```sql id="4m7fg4"
SELECT current_user;
SELECT usesuper FROM pg_user WHERE usename='Markus';
```

Erwartung:

```text id="lh71bz"
current_user = Markus
usesuper = true
```

---

## Sicherheitsaspekt

`SUPERUSER` entspricht praktisch Root innerhalb PostgreSQL.

Für normale Administration oft ausreichend:

```text
Create DB = YES
Create Role = YES
Superuser = NO
```

Das reduziert Eskalations- und Fehlkonfigurationsrisiko deutlich.

### 52. Assistent

Direkt auf dem VPS:

Als `postgres` in psql wechseln:

```bash
sudo -u postgres psql
```

Dann User anlegen:

```sql id="7d2jro"
CREATE USER "Markus" WITH PASSWORD 'STARKES_PASSWORT';
ALTER USER "Markus" WITH SUPERUSER;
```

Optional zusätzlich:

```sql id="ux4ft0"
GRANT ALL PRIVILEGES ON DATABASE wissen2026 TO "Markus";
```

Prüfen:

```sql id="0vv4ud"
\du
```

Erwartung:

```text id="9xoccm"
Markus | Superuser, Create role, Create DB ...
```

Beenden:

```sql id="siv5ai"
\q
```

Login testen:

```bash id="zq8u7v"
psql -U Markus -d wissen2026 -h 127.0.0.1
```

Oder extern:

```bash id="l0q2zz"
psql "host=85.215.131.200 port=5432 dbname=wissen2026 user=Markus"
```

### 53. Benutzer

direkt auf vps einrichten

### 54. Assistent

Zuerst identifizieren, was „hermes“ ist:

```bash
docker ps -a | grep -i hermes
podman ps -a | grep -i hermes

systemctl list-units --type=service | grep -i hermes
systemctl list-unit-files | grep -i hermes

rpm -qa | grep -i hermes
dnf list installed | grep -i hermes
```

Falls Docker-Container:

```bash
docker stop hermes
docker rm hermes
```

Falls Podman:

```bash
podman stop hermes
podman rm hermes
```

Falls Systemd-Service:

```bash
sudo systemctl stop hermes
sudo systemctl disable hermes
sudo rm -f /etc/systemd/system/hermes.service
sudo systemctl daemon-reload
```

Falls RPM/Package:

```bash
sudo dnf remove -y hermes
```

Zusätzliche Bereinigung:

```bash
docker images | grep -i hermes
docker volume ls | grep -i hermes
```

Image löschen:

```bash
docker rmi <IMAGE_ID>
```

Volume löschen:

```bash
docker volume rm <VOLUME_NAME>
```

Validierung:

```bash
ps aux | grep -i hermes
ss -ltnp
docker ps -a
systemctl list-units --type=service
```

Zielzustand:
- kein laufender Prozess
- kein aktiver Service
- kein Container
- kein offener Port
- keine verbleibenden Volumes/Images falls vollständige Entfernung gewünscht.

### 55. Benutzer

hermes deinstallieren

### 56. Assistent

Es existieren noch nur Images, keine laufenden Container.

Prüfen:

```bash id="6z9e9l"
docker ps -a | grep -i hermes
```

Wenn leer: direkt löschen.

Images entfernen:

```bash id="v53yq0"
docker rmi ghcr.io/nesquena/hermes-webui:latest
docker rmi hermes-webui-hermes-webui:latest
docker rmi nousresearch/hermes-agent:latest
```

Falls Fehler wegen abhängiger Container:

```bash id="b8k75u"
docker ps -a
docker rm -f <CONTAINER_ID>
```

Dann erneut `docker rmi`.

Nicht verwendete Docker-Daten bereinigen:

```bash id="9f9k2n"
docker image prune -a -f
docker volume prune -f
```

Validierung:

```bash id="9f8r5v"
docker images | grep -i hermes
docker volume ls | grep -i hermes
```

Erwartung:
- keine Hermes-Images
- keine Hermes-Volumes
- mehrere GB Speicher frei (`nousresearch/hermes-agent` allein ~8.5 GB).

### 57. Benutzer

[root@localhost ~]# docker images | grep -i hermes
docker volume ls | grep -i hermes
ghcr.io/nesquena/hermes-webui:latest   99aaa9e7b95c        337MB           89MB
hermes-webui-hermes-webui:latest       ecd9da5680c1        339MB         89.5MB
nousresearch/hermes-agent:latest       9d7ff239a500       8.46GB         2.65GB
