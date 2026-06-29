---
title: "Hermes KI Agent Installation"
type: chatgpt_conversation
source: chatgpt
source_id: "69e9bf96-aff0-8389-870e-eb8b349a1af0"
created: 2026-04-23
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
---


# Hermes KI Agent Installation

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69e9bf96-aff0-8389-870e-eb8b349a1af0`
- Nachrichten: 6

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Zielzustand: reproduzierbare, isolierte Laufumgebung für einen „Hermes KI Agent“ auf deinem VPS (Rocky Linux 9, Root-Zugriff), mit klaren Abhängigkeiten, Netzwerk-Exposition und Persistenz.

Annahme:
- „Hermes KI Agent“ = Python-basierter Agent (typisch: LLM-Wrapper + Tools, z. B. Hermes/OpenHermes + Framework wie LangChain/AutoGen/Custom Repo).
- Deployment via Docker (präferiert wegen Isolation) oder nativ via Python.
- Externer LLM-Zugriff (OpenAI/Local LLM via Ollama).

---

## 1. Basis-System vorbereiten

```bash
dnf update -y
dnf install -y git curl wget nano
```

Firewall (minimal offen):
```bash
firewall-cmd --permanent --add-port=22/tcp
firewall-cmd --permanent --add-port=8000/tcp   # Agent API
firewall-cmd --reload
```

---

## 2. Docker installieren (empfohlen)

```bash
dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io
systemctl enable docker
systemctl start docker
```

Test:
```bash
docker run hello-world
```

---

## 3. Projektstruktur

```bash
mkdir -p /opt/hermes-agent
cd /opt/hermes-agent
```

Minimalstruktur:
```
/opt/hermes-agent
 ├── app/
 │    ├── main.py
 │    └── agent.py
 ├── requirements.txt
 ├── Dockerfile
 └── .env
```

---

## 4. Abhängigkeiten definieren

Beispiel `requirements.txt`:

```
fastapi
uvicorn
openai
langchain
python-dotenv
```

---

## 5. Minimaler Hermes-Agent (Beispiel)

`app/agent.py`:
```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def run_agent(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

`app/main.py`:
```python
from fastapi import FastAPI
from app.agent import run_agent

app = FastAPI()

@app.get("/ask")
def ask(q: str):
    return {"response": run_agent(q)}
```

---

## 6. Dockerfile

```Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 7. Environment konfigurieren

`.env`:
```
OPENAI_API_KEY=dein_key
```

---

## 8. Build + Run

```bash
docker build -t hermes-agent .
docker run -d \
  --name hermes \
  -p 8000:8000 \
  --env-file .env \
  hermes-agent
```

Test:
```
http://85.215.131.200:8000/ask?q=hello
```

---

## 9. Alternative: Lokales LLM (kein API-Key)

Ollama installieren:

```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl enable ollama
systemctl start ollama
```

Modell:
```bash
ollama pull openhermes
```

Agent anpassen:
- statt OpenAI → HTTP Call zu `http://localhost:11434`

---

## 10. Reverse Proxy + TLS (optional, produktiv)

Nginx:

```bash
dnf install -y nginx
systemctl enable nginx
systemctl start nginx
```

Config:
```
server {
    listen 80;
    server_name deine-domain.de;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

TLS via Let’s Encrypt (certbot).

---

## 11. Persistenz + Betrieb

Probleme ohne Maßnahmen:
- Container-Verlust → Zustand weg
- Logs volatil

Fix:
```bash
docker run -d \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  hermes-agent
```

---

## 12. Risiken / Failure Modes

- Offene API ohne Auth → Missbrauch / Kostenexplosion
- Kein Rate Limiting → DoS
- Root-Zugriff + offene Ports → Angriffsfläche
- LLM-Calls extern → Latency + Kosten
- Lokales Modell → RAM/CPU Bottleneck (8 GB reicht nur für kleine Modelle)

---

## 13. Skalierung

Limitierungen:
- Single VPS (6 vCore / 8 GB RAM)
- Kein Queueing

Erweiterung:
- Redis + Worker (Celery)
- Horizontal via Docker Swarm / Kubernetes
- Caching Layer für Antworten

---

## 14. Entscheidungslogik

| Option            | Vorteil                     | Nachteil                    |
|------------------|----------------------------|-----------------------------|
| OpenAI API       | Qualität, einfach          | Kosten, extern              |
| Ollama lokal     | Kontrolle, keine API-Kosten| Ressourcen, Setup           |
| Docker           | Reproduzierbar             | zusätzlicher Layer          |
| Native Python    | einfacher Debug            | weniger isoliert            |

---

Endzustand:  
HTTP-Endpoint `/ask` läuft auf deinem VPS, kapselt Hermes-Agent-Logik, austauschbar zwischen externem und lokalem LLM, containerisiert, firewall-begrenzt, skalierbar.

### 2. Benutzer

{"asset_pointer": "sediment://file_00000000bb74720a8ef1f361d1d10f8a", "content_type": "image_asset_pointer", "fovea": null, "height": 889, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 69393, "width": 607}
wie installiere und konfiguriere ich Hermes KI Agent auv meinem vps

### 3. Assistent

Dann entfällt der Basis-Teil. Relevanter Zustand ist jetzt:

- Docker vorhanden
- Ollama läuft
- Neo4j läuft
- `presql` sehr wahrscheinlich = PostgreSQL
- Ziel: Hermes-Agent als zusätzlicher Service in die bestehende Container-Landschaft integrieren

## Zielarchitektur

```text
[Hermes Agent API]
   ├── nutzt Ollama für Inferenz
   ├── nutzt Neo4j für Wissensgraph / Memory / Beziehungen
   └── nutzt PostgreSQL für Tasks, Sessions, Logs, Zustände
```

## Annahmen

- Ollama ist im selben Docker-Netz erreichbar
- Neo4j ist im selben Docker-Netz erreichbar
- PostgreSQL ist im selben Docker-Netz erreichbar
- „Hermes KI Agent“ meint keinen proprietären Installer, sondern einen Agent-Service, der mit einem Hermes/OpenHermes-Modell über Ollama arbeitet
- Rocky 9 Host ist nicht das Problem; die Integration passiert auf Compose-/Container-Ebene

## Entscheidung

Nicht nativ auf dem Host installieren. Als separaten Container deployen. Gründe:

- klare Abgrenzung der Abhängigkeiten
- reproduzierbares Update-Verhalten
- einfache Netzwerk- und Secret-Verwaltung
- kein Python-/Systempaket-Mischzustand auf dem Host

---

# 1. Docker-Netz prüfen

Vorbedingung: alle Container müssen im gleichen Netzwerk liegen.

Bestehende Netzwerke anzeigen:

```bash
docker network ls
```

Falls noch kein gemeinsames Netzwerk existiert:

```bash
docker network create ai-stack
```

Bestehende Container verbinden:

```bash
docker network connect ai-stack ollama
docker network connect ai-stack neo4j
docker network connect ai-stack postgres
```

Container-Namen prüfen:

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"
```

Wichtig: im Agent-Container müssen diese Hostnamen auflösbar sein:

- `ollama`
- `neo4j`
- `postgres`

Wenn deine Container anders heißen, diese Namen überall ersetzen.

---

# 2. Modell in Ollama bereitstellen

Hermes-Modell lokal ziehen. Typische Varianten:

```bash
docker exec -it ollama ollama pull openhermes
```

oder moderner/robuster:

```bash
docker exec -it ollama ollama pull hermes3
```

Modelle prüfen:

```bash
docker exec -it ollama ollama list
```

Trade-off:

- `openhermes`: leicht, älter, meist einfacher
- `hermes3`: aktueller, besseres Verhalten, potenziell höherer Ressourcenbedarf

Mit 8 GB RAM auf dem VPS bleibt die Modellgröße der Engpass. Große Modelle führen zu:
- Swap-Druck
- hohe Latenz
- Container-Kills
- Host-Instabilität

Deshalb kleine bis mittlere Modelle bevorzugen.

---

# 3. PostgreSQL-Struktur anlegen

Falls PostgreSQL bereits läuft, Datenbank und User für den Agent anlegen:

```bash
docker exec -it postgres psql -U postgres
```

Dann in `psql`:

```sql
CREATE DATABASE hermes;
CREATE USER hermes_user WITH PASSWORD 'STRONG_DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE hermes TO hermes_user;
```

Optional Basistabelle für Sessions/Logs:

```sql
\c hermes

CREATE TABLE IF NOT EXISTS agent_runs (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    prompt TEXT NOT NULL,
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

# 4. Neo4j vorbereiten

Neo4j-Container prüfen:

```bash
docker ps | grep neo4j
```

Zugang testen:

```bash
docker exec -it neo4j cypher-shell -u neo4j -p 'DEIN_PASSWORT' "RETURN 1;"
```

Optional Constraints für Knowledge Graph:

```cypher
CREATE CONSTRAINT entity_name IF NOT EXISTS
FOR (e:Entity)
REQUIRE e.name IS UNIQUE;
```

Nutzen:
- Duplikatreduktion
- schnellere Merges
- stabilere Wissensstruktur

---

# 5. Hermes-Agent als Service bauen

Projektverzeichnis:

```bash
mkdir -p /opt/hermes-agent/app
cd /opt/hermes-agent
```

## `requirements.txt`

```txt
fastapi
uvicorn[standard]
requests
psycopg2-binary
neo4j
python-dotenv
pydantic
```

## `app/main.py`

```python
import os
import json
import requests
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "openhermes")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "hermes")
POSTGRES_USER = os.getenv("POSTGRES_USER", "hermes_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "STRONG_DB_PASSWORD")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "CHANGE_ME")

app = FastAPI(title="Hermes Agent")

class AskRequest(BaseModel):
    session_id: str
    prompt: str

def get_pg_conn():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

def store_run(session_id: str, prompt: str, response: str):
    conn = get_pg_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_runs (session_id, prompt, response)
                    VALUES (%s, %s, %s)
                    """,
                    (session_id, prompt, response)
                )
    finally:
        conn.close()

def store_graph_fact(prompt: str, response: str):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            session.run(
                """
                MERGE (q:Query {text: $prompt})
                MERGE (a:Answer {text: $response})
                MERGE (q)-[:GENERATED]->(a)
                """,
                prompt=prompt,
                response=response
            )
    finally:
        driver.close()

def call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=180)
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Ollama error: {r.text}")
    data = r.json()
    return data.get("response", "").strip()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask(req: AskRequest):
    response = call_ollama(req.prompt)
    store_run(req.session_id, req.prompt, response)
    store_graph_fact(req.prompt, response)
    return {"session_id": req.session_id, "response": response}
```

## `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# 6. Compose-Datei für den Agent

Wenn du bereits ein zentrales `docker-compose.yml` hast, nur den neuen Service ergänzen.

## Variante: separater Service in bestehendem Stack

```yaml
services:
  hermes-agent:
    build: /opt/hermes-agent
    container_name: hermes-agent
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      OLLAMA_URL: http://ollama:11434
      OLLAMA_MODEL: openhermes
      POSTGRES_HOST: postgres
      POSTGRES_DB: hermes
      POSTGRES_USER: hermes_user
      POSTGRES_PASSWORD: STRONG_DB_PASSWORD
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: CHANGE_ME
    networks:
      - ai-stack

networks:
  ai-stack:
    external: true
```

Wichtig:
- `external: true` nur verwenden, wenn `ai-stack` bereits existiert
- Port `8000` nur veröffentlichen, wenn externer Zugriff nötig ist
- intern-only wäre sicherer

---

# 7. Build und Start

```bash
cd /opt/hermes-agent
docker compose up -d --build
```

Logs:

```bash
docker logs -f hermes-agent
```

Healthcheck:

```bash
curl http://localhost:8000/health
```

Testabfrage:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "prompt": "Erkläre in drei Sätzen, was ein Wissensgraph ist."
  }'
```

---

# 8. Netzwerk-Failure-Modes

## Problem: Agent erreicht Ollama nicht
Symptom:
- Timeout
- `Name or service not known`
- Connection refused

Prüfen:

```bash
docker exec -it hermes-agent ping ollama
docker exec -it hermes-agent curl http://ollama:11434/api/tags
```

Ursachen:
- nicht im gleichen Docker-Netz
- falscher Containername
- Ollama lauscht nicht korrekt

## Problem: Agent erreicht PostgreSQL nicht

```bash
docker exec -it hermes-agent python -c "import socket; print(socket.gethostbyname('postgres'))"
```

## Problem: Agent erreicht Neo4j nicht

```bash
docker exec -it hermes-agent bash
apt-get update && apt-get install -y netcat-openbsd
nc -zv neo4j 7687
```

---

# 9. Ressourcenrisiko auf deinem VPS

Dein VPS:
- 6 vCore
- 8 GB RAM

Das ist für die Kombination kritisch:

- Ollama-Modell
- Neo4j
- PostgreSQL
- zusätzlicher Python-Agent

Hauptengpass: RAM, nicht CPU.

Typische Konsequenzen:
- Neo4j Heap-Konkurrenz
- Ollama lädt Modell und blockiert Speicher
- PostgreSQL Caches wachsen
- Kernel OOM-Killer beendet Container

## Gegenmaßnahmen

### Für den Agent-Container Limits setzen

```yaml
services:
  hermes-agent:
    mem_limit: 1g
    cpus: "1.5"
```

### Für Neo4j Heap begrenzen
In Neo4j-Umgebung:

```yaml
environment:
  NEO4J_server_memory_heap_initial__size: 512m
  NEO4J_server_memory_heap_max__size: 1024m
```

### Für PostgreSQL konservativ bleiben
Kein aggressives Shared Buffer Tuning auf 8 GB Host.

### Für Ollama kleine Modelle verwenden
Kein 13B/34B-Modell auf diesem Host.

---

# 10. Sicherheitskonfiguration

Aktueller Standardfehler wäre: `/ask` offen ins Internet stellen.

Folgen:
- Fremdnutzung
- Ressourcenmissbrauch
- Prompt Flooding
- Modell- und DB-Überlast

## Minimal absichern

### Nur lokal veröffentlichen
Statt:

```yaml
ports:
  - "8000:8000"
```

besser:

```yaml
ports:
  - "127.0.0.1:8000:8000"
```

Dann Zugriff nur per Reverse Proxy oder SSH-Tunnel.

### Optional API-Key erzwingen
In FastAPI Header-Check ergänzen:

```python
from fastapi import Header

API_KEY = os.getenv("API_KEY", "")

@app.post("/ask")
def ask(req: AskRequest, x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
```

---

# 11. Wenn du bereits ein UI oder Orchestrierungs-Tool nutzt

Falls der „Hermes-Agent“ nicht als eigener Python-Service gedacht ist, sondern als Agent-Logik in einem vorhandenen Stack, dann ist die saubere Zuordnung:

- **Ollama** = Model Runtime
- **Neo4j** = Graph Memory / Retrieval Layer
- **PostgreSQL** = Operational State / Logging / Sessions
- **Hermes-Agent** = Orchestrator, nicht Modell

Das heißt: Hermes ist kein vierter Datenbank-/Inference-Server, sondern die Anwendungsschicht.

---

# 12. Produktive Empfehlung für deinen Stack

Für deinen VPS ist die robusteste Variante:

1. Ollama weiterlaufen lassen
2. kleines Hermes-Modell verwenden
3. Hermes-Agent als schlanken FastAPI-Container deployen
4. PostgreSQL nur für Session-/Run-Logs verwenden
5. Neo4j nur für semantische Knoten/Beziehungen verwenden
6. API nicht öffentlich exponieren
7. RAM-Limits auf Container setzen

---

# 13. Minimaler Implementierungsplan

```bash
mkdir -p /opt/hermes-agent/app
cd /opt/hermes-agent
```

Dateien anlegen:
- `requirements.txt`
- `Dockerfile`
- `app/main.py`

Dann:

```bash
docker network ls
docker compose up -d --build
curl http://localhost:8000/health
```

Danach Integrationstest:
- Antwort kommt von Ollama
- Eintrag landet in PostgreSQL
- Knoten landen in Neo4j

---

# 14. Wahrscheinlichster Fehler in deinem Setup

Nicht die Installation, sondern die falsche Systemgrenze:

- Agent-Container wird gebaut
- Modell antwortet
- danach scheitert Persistenz oder Netzwerkauflösung

Deshalb zuerst diese drei Tests getrennt validieren:

```bash
curl http://ollama:11434/api/tags
psql -h postgres -U hermes_user -d hermes
cypher-shell -a bolt://neo4j:7687 -u neo4j -p 'PASS'
```

Erst danach den Agent starten.

---

# 15. Nächster stabiler Zielzustand

Ein funktionierender Compose-Service `hermes-agent`, der:

- Prompts via HTTP annimmt
- Antworten von Ollama generiert
- Runs in PostgreSQL speichert
- Beziehungen in Neo4j schreibt
- intern im Docker-Netz läuft
- nicht ungeschützt öffentlich erreichbar ist

Ich kann daraus direkt eine vollständige `docker-compose.yml` für deinen bestehenden Stack ableiten, mit den konkreten Service-Namen `ollama`, `postgres`, `neo4j` und `hermes-agent`.

### 4. Benutzer

docker läuft bereits mit ollama, presql, neo4j

### 5. Assistent

Ziel: vollständige Entfernung des Hermes-Agent aus deinem Docker-Stack inkl. Container, Images, Volumes, Netzwerkreferenzen und optionaler Datenreste.

---

## 1. Laufenden Container stoppen und entfernen

```bash
docker ps | grep hermes
```

```bash
docker stop hermes-agent
docker rm hermes-agent
```

Falls anderer Name verwendet wurde:

```bash
docker ps -a
docker rm -f <container_name>
```

---

## 2. Image entfernen

```bash
docker images | grep hermes
```

```bash
docker rmi hermes-agent
```

Falls Build-Tag anders:

```bash
docker rmi <image_id>
```

---

## 3. Compose-Service entfernen

Falls in `docker-compose.yml` definiert:

- gesamten Block `hermes-agent:` löschen
- danach:

```bash
docker compose down
docker compose up -d
```

---

## 4. Projektverzeichnis löschen

```bash
rm -rf /opt/hermes-agent
```

---

## 5. Netzwerk-Bereinigung

Prüfen, ob noch Referenzen existieren:

```bash
docker network inspect ai-stack
```

Wenn kein anderer Service betroffen:

```bash
docker network prune
```

---

## 6. PostgreSQL-Daten entfernen (optional)

Nur wenn Hermes-Daten nicht mehr benötigt werden:

```bash
docker exec -it postgres psql -U postgres
```

```sql
DROP DATABASE hermes;
DROP USER hermes_user;
```

Oder nur Tabelle löschen:

```sql
\c hermes
DROP TABLE agent_runs;
```

---

## 7. Neo4j-Daten entfernen (optional)

Nur Hermes-bezogene Knoten löschen:

```bash
docker exec -it neo4j cypher-shell -u neo4j -p 'PASS'
```

```cypher
MATCH (q:Query)-[r:GENERATED]->(a:Answer)
DELETE q, r, a;
```

---

## 8. Offene Ports prüfen

```bash
ss -tulpen | grep 8000
```

Falls noch gebunden → falscher Container aktiv.

---

## 9. Systemzustand validieren

```bash
docker ps
docker images
docker volume ls
```

Keine Einträge mit `hermes` mehr vorhanden.

---

## 10. Typische Restprobleme

- dangling images → `docker image prune`
- dangling volumes → `docker volume prune`
- alte env-files → manuell löschen
- reverse proxy config zeigt noch auf Port 8000 → entfernen

---

Endzustand:

- kein laufender Hermes-Container
- kein Hermes-Image
- keine offenen Ports
- keine DB-Referenzen (optional bereinigt)
- Docker-Stack konsistent ohne Agent-Service

### 6. Benutzer

hermes löschen
