---
title: "TTR Werte auslesen"
type: chatgpt_conversation
source: chatgpt
source_id: "68c983e8-75a0-8324-acb1-2a02fb93e8c5"
created: 2025-09-16
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
  - tischtennis
  - verein
---


# TTR Werte auslesen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68c983e8-75a0-8324-acb1-2a02fb93e8c5`
- Nachrichten: 52

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich möchte die ttr werte aus click-tt unserer liga auslesen

### 2. Benutzer

ChatGPT - TTR-Werte aus Click-TT auslesen



Du bist ein erfahrener Programmierer mit Kenntnissen in Webscraping und der Nutzung von APIs. Dein Ziel ist es, die TTR-Werte (Talent-Top-Ranglisten) aus Click-TT für eine bestimmte Liga auszulesen. Du hast Erfahrung mit Python, JavaScript oder einer anderen Programmiersprache, die du für diese Aufgabe verwenden möchtest.



Die Zielgruppe sind Programmierer oder Technologen, die an der Auswertung von Sportdaten interessiert sind, insbesondere im Rahmen von Tischtennis.



Du sollst eine Schritt-für-Schritt-Anleitung erstellen, wie man die TTR-Werte aus Click-TT ausliest. Beschreibe die notwendigen Schritte, wie das Finden der relevanten Daten, das Nutzen von Webscraping-Techniken oder APIs sowie das Verarbeiten der Ergebnisse in einem lesbaren Format. Der Prompt soll Variablen wie [Liga], [Sprache] und [Datenformat] enthalten, um die Antwort anpassbar zu machen.



Die Ausgabe soll in Form einer Anleitung im Fließtext erfolgen, idealerweise angereichert mit Codebeispielen und hilfreichen Erklärungen.

### 3. Assistent

Klar, lass uns die TTR-Werte aus click-TT nerd-sauber „anzapfen“. Es gibt zwei praxistaugliche Wege:

1) **Schnell & ohne Login:** die öffentliche „Mannschaftsmeldungen/Spielerliste“-Seite („groupPools“) pro Liga scrapen – dort stehen die **Q-TTR**-Werte jedes gemeldeten Spielers teamweise (ideal zur Analyse einer Liga). Beispiele zeigen die Spalten *Rang, Q-TTR, Name, Vorname* direkt auf der Ligaseite. citeturn7search0turn7search2turn7search3  
2) **Stabil & offiziell (empfohlen für Automatisierung):** die nuLiga/click-TT **REST-API** nutzen – speziell `…/myTT/rankings/group/{groupId}` liefert TTR-Rankings für eine Liga/Gruppe (OAuth2-Login nötig). Die API ist dokumentiert und enthält genau diese Endpunkte. citeturn3view0

Bevor wir loslegen, zwei Mini-Hinweise:  
• **TTR vs. Q-TTR:** Q-TTR (Quartalswerte) sind die offiziell melderelevanten Stichtagswerte; die „groupPools“-Seiten zeigen Q-TTR. Live-TTR/dynamische Werte bekommst du via API/myTischtennis nach Login. citeturn7search5turn0search21  
• **Recht & Fair Use:** beachte die Nutzungsbedingungen; keine aggressiven Parallel-Scrapes, respektiere robots.txt und Rate-Limits.

---

# Schritt-für-Schritt-Anleitung (mit Variablen [Liga], [Sprache], [Datenformat])

## 0) Was bedeutet [Liga]?
[Liga] kann eine der folgenden Formen sein:
- **A)** Die direkte click-TT-Gruppen-URL deiner Liga (z. B. `…/wa/groupPools?...&group=471869`), oder  
- **B)** Das Zahlen-**groupId** aus einer Liga-URL (`group=471869`) plus Saisonname (z. B. `WTTV 24/25`). Auf den „groupPools“-Seiten sieht man Q-TTR je Team. citeturn7search0turn7search3

[Sprache] steuert z. B. Spaltenüberschriften („de“/„en“).  
[Datenformat] ist deine Wunsch-Ausgabe: `json`, `csv` oder `markdown`.

---

## Weg 1: Q-TTR aus der Liga-Spielerliste („groupPools“) scrapen (ohne Login)

**Ziel:** Für **[Liga]** alle Teams und Spieler samt Q-TTR extrahieren und in **[Datenformat]** ausgeben.

**So findest du die Quelle:**  
Öffne die Liga → Menüpunkt „Mannschaftsmeldungen/Spielerliste“. Die URL enthält `…/wa/groupPools?championship=<SAISON>&displayTyp=<vorrunde|rueckrunde>&group=<GROUP_ID>`. Auf dieser Seite stehen je Team Tabellen mit **Q-TTR** je Spieler. Beispiele zeigen genau diese Struktur. citeturn7search0turn7search2

### Python-Beispiel
```python
# Variablen:
BASE_URL   = "[https://wttv.click-tt.de]"              # Domain deines Verbandsportals
SAISON     = "[WTTV 24/25]"                            # exakt wie in der URL, z.B. "WTTV 24/25"
RUNDE      = "[vorrunde]"                              # "vorrunde" oder "rueckrunde"
GROUP_ID   = "[471869]"                                # aus der URL (group=471869)
SPRACHE    = "[de]"                                    # z.B. "de" oder "en"
DATENFORMAT= "[json]"                                  # "json", "csv" oder "markdown"

import requests, re
from bs4 import BeautifulSoup
from collections import defaultdict
import csv, json, sys

def fetch_qttr_from_group_pools(base_url, saison, runde, group_id):
    params = {
        "championship": saison,
        "displayTyp": runde,
        "group": group_id
    }
    url = f"{base_url}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Teamabschnitte sind meist <h2> (Teamname) gefolgt von einer Tabelle
    results = []
    for h2 in soup.find_all(["h2", "h3"]):
        team = h2.get_text(strip=True)
        table = h2.find_next("table")
        if not table: 
            continue
        headers = [th.get_text(strip=True) for th in table.select("thead th")]
        # erwartete Spalten: Rang | Q-TTR | Name, Vorname | A | Status
        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if len(cols) < 3:
                continue
            # robuste Extraktion
            rang   = cols[0]
            qttr   = re.sub(r"[^\d\-]", "", cols[1])  # Zahl (kann fehlen bei Platzhaltern)
            name   = cols[2]                          # "Nachname, Vorname"
            anmerk = cols[3] if len(cols) > 3 else ""
            status = cols[4] if len(cols) > 4 else ""
            results.append({
                "team": team,
                "rang": rang,
                "qttr": int(qttr) if qttr.isdigit() else None,
                "name": name,
                "anmerkung": anmerk,
                "status": status
            })
    return results

data = fetch_qttr_from_group_pools(BASE_URL, SAISON, RUNDE, GROUP_ID)

# Ausgabe nach [Datenformat]
def emit(data, datenformat, sprache):
    # einfache Übersetzung der Header
    headers_de = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"]
    headers_en = ["Team","Slot","Q-TTR","Name","Note","Status"]
    headers = headers_de if sprache.lower().startswith("de") else headers_en

    if datenformat == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif datenformat == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(headers)
        for r in data:
            writer.writerow([r["team"], r["rang"], r["qttr"], r["name"], r["anmerkung"], r["status"]])
    elif datenformat == "markdown":
        print("| " + " | ".join(headers) + " |")
        print("|" + "|".join(["---"]*len(headers)) + "|")
        for r in data:
            print(f'| {r["team"]} | {r["rang"]} | {r["qttr"] if r["qttr"] is not None else ""} | {r["name"]} | {r["anmerkung"]} | {r["status"]} |')
    else:
        raise SystemExit("Unbekanntes Datenformat")

emit(data, DATENFORMAT, SPRACHE)
```

**Was das leistet:**  
- Liest die Liga-Spielerliste („groupPools“) aus und liefert **Q-TTR pro Spieler** je Team – exakt das, was click-TT öffentlich anzeigt. citeturn7search0turn7search2  
- Gibt die Daten in **[Datenformat]** aus, mit Spaltenlabels in **[Sprache]**.

**Edge-Cases & Tipps**  
- Manche Alt-Saisons sind datenschutzgeschützt (Login-Prompt): dann bekommst du statt Tabelle eine Freischaltmaske. Prüfe Response-Text und brich ab. citeturn7search4  
- Wenn „Weitere Spieler …“ Links auftauchen, sind die Zeilen oft trotzdem bereits im HTML (nur ein-/ausklappbar). Falls nicht, folge dem Link und mergen.  
- Achte auf Season-String & Runde exakt wie in der URL (z. B. `WTTV 24/25`, `vorrunde`).  

---

## Weg 2: Offizielle nuLiga/click-TT REST-API (mit OAuth2) für TTR-Rankings

**Wann nutzen?**  
Wenn du stabilen Zugriff brauchst, ggf. dynamische TTR-Infos, oder große Datenmengen. nuLiga stellt dokumentierte REST-Endpunkte bereit, darunter:  
- `GET /2014/myTT/rankings/group/{groupId}` → **TTR-Ranking für eine Gruppe (Liga)**  
- Diverse Hilfs-Endpunkte zu Verbänden/Seasons/Leagues/Groups/Teams. citeturn3view0

**Authentifizierung:**  
Die API hängt an der click-TT ID / nuLiga-OAuth2 (Loginseiten sind öffentlich sichtbar). Du holst dir per Authorization Code Flow ein `access_token` und setzt es als `Authorization: Bearer <token>` in den API-Calls. (Die OAuth-Endpoints sind unter der `…liga.nu`-ID-Domain verlinkt.) citeturn1search13turn1search17

**Vorgehen (skizziert):**
1. **groupId ermitteln:**  
   – Am schnellsten aus einer Liga-URL (`group=…`) oder über API-Navigation (`/2018/federations` → Seasons → Leagues → Meetings/Groups). citeturn3view0  
2. **Token holen:** OAuth2-Login via click-TT ID. (Client-Registrierung vorausgesetzt.) citeturn1search13  
3. **TTR anfragen:** `GET {API_HOST}/rs/2014/myTT/rankings/group/{groupId}`. Liefert TTR-Infos für alle Personen in der Gruppe/Liga. citeturn3view0

### Python-Snippet (mit Platzhaltern)
```python
import requests

API_HOST   = "https://hbde-portal.liga.nu"  # API-Host laut Doku
ACCESS_TOKEN = "[DEIN_OAUTH2_TOKEN]"        # via click-TT ID OAuth2 beschafft
GROUP_ID  = "[471869]"
SPRACHE   = "[de]"
DATENFORMAT = "[json]"

def get_group_ttr(api_host, token, group_id):
    url = f"{api_host}/rs/2014/myTT/rankings/group/{group_id}"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    return r.json()

payload = get_group_ttr(API_HOST, ACCESS_TOKEN, GROUP_ID)

# Je nach API-Schema Felder mappen (Bezeichner können je nach Version variieren)
rows = []
for person in payload.get("rankings", payload):    # flexibel
    rows.append({
        "personId":  person.get("internalId") or person.get("personId"),
        "name":      person.get("name"),
        "club":      person.get("clubName"),
        "team":      person.get("teamName"),
        "ttr":       person.get("ttr") or person.get("currentTtr") or person.get("qttr"),
        "stand":     person.get("rankingDate") or person.get("timestamp")
    })

# Ausgabe …
import json, csv, sys
if DATENFORMAT == "json":
    print(json.dumps(rows, ensure_ascii=False, indent=2))
elif DATENFORMAT == "csv":
    writer = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
    writer.writeheader(); writer.writerows(rows)
else:
    # markdown
    headers = rows[0].keys()
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"]*len(headers)) + "|")
    for r in rows:
        print("| " + " | ".join(str(r[h] or "") for h in headers) + " |")
```

**Warum API?**  
Du bekommst strukturierte Daten (keine HTML-Fragilität) und zusätzliche Endpunkte, z. B. Gruppen-/Team-Tabellen, Spieler-Statistiken, usw. – alles in einer sauber dokumentierten Oberfläche. citeturn3view0

---

## Qualität, Robustheit & kleine Extras

- **TTR-Kontext:** Die TTR-Rangliste wird vom DTTB/myTischtennis geführt; Q-TTR-Stichtage sind melderelevant. Für tiefe Einordnung siehe die offizielle Ranglistenbeschreibung/WO-Dokumente. citeturn0search21turn0search16  
- **Rate-Limits & Höflichkeit:** zwischen Requests schlafen (z. B. 0.5–1 s), Header setzen, Caching nutzen.  
- **Validierung:** Prüfe, ob die Seite statt Daten eine Login-Maske liefert, und brich mit erklärender Meldung ab. citeturn7search4  
- **Weiterverarbeitung:** Team-Mittelwerte, Streuungen, Top-N der Liga, oder Del­tas zwischen VR/RR – alles trivial, sobald du die Liste hast.

---

## JavaScript-Kurzvariante (Node.js mit Cheerio) für Weg 1
```js
// Variablen:
const BASE_URL = "[https://wttv.click-tt.de]";
const SAISON   = "[WTTV 24/25]";
const RUNDE    = "[vorrunde]";      // "vorrunde" | "rueckrunde"
const GROUP_ID = "[471869]";
const SPRACHE  = "[de]";
const FORMAT   = "[json]";          // "json" | "csv" | "markdown"

import axios from "axios";
import * as cheerio from "cheerio";

const url = `${BASE_URL}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools`;
const { data: html } = await axios.get(url, { params: {
  championship: SAISON, displayTyp: RUNDE, group: GROUP_ID
}});

const $ = cheerio.load(html);
const out = [];

$("h2, h3").each((_, h) => {
  const team = $(h).text().trim();
  const table = $(h).nextAll("table").first();
  if (!table.length) return;
  table.find("tbody tr").each((_, tr) => {
    const tds = $(tr).find("td");
    if (tds.length < 3) return;
    const rang  = $(tds[0]).text().trim();
    const qttr  = $(tds[1]).text().replace(/[^\d-]/g,"");
    const name  = $(tds[2]).text().trim();
    const anm   = tds[3] ? $(tds[3]).text().trim() : "";
    const status= tds[4] ? $(tds[4]).text().trim() : "";
    out.push({ team, rang, qttr: qttr ? Number(qttr) : null, name, anmerkung: anm, status });
  });
});

if (FORMAT === "json") {
  console.log(JSON.stringify(out, null, 2));
} else if (FORMAT === "csv") {
  const header = SPRACHE.startsWith("de") ?
    ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] :
    ["Team","Slot","Q-TTR","Name","Note","Status"];
  console.log(header.join(","));
  out.forEach(r => console.log([r.team, r.rang, r.qttr ?? "", r.name, r.anmerkung, r.status].join(",")));
} else {
  const header = SPRACHE.startsWith("de") ?
    ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] :
    ["Team","Slot","Q-TTR","Name","Note","Status"];
  console.log("| " + header.join(" | ") + " |");
  console.log("|" + header.map(()=> "---").join("|") + "|");
  out.forEach(r => console.log(`| ${r.team} | ${r.rang} | ${r.qttr ?? ""} | ${r.name} | ${r.anmerkung} | ${r.status} |`));
}
```

---

## Welche Variante solltest du nehmen?

- **Nur Liga-Q-TTR fürs Scouting/Reporting:** Weg 1 ist simpel und sofort nutzbar, weil die „groupPools“-Seite die Werte bereits zeigt. citeturn7search0turn7search2  
- **Langfristige Integration, mehr Kontext (Events/Matches/Spielerhistorie) oder Live-TTR:** Weg 2 mit der offiziellen REST-API ist die robuste Lösung; plane OAuth2 und saubere Client-Registrierung ein. citeturn3view0turn1search13

Wenn du magst, gebe ich dir eine **konkrete Start-URL** für eure [Liga] und setze die Werte für [Sprache] und [Datenformat] direkt in ein lauffähiges Skript — oder wir packen zusätzlich ein kleines Ranking-Dashboard oben drauf (Team-Mittel, Top-10 der Liga, Trends VR→RR).

### 4. Benutzer

weg 1

### 5. Assistent

Super — hier ist **Weg 1 (Scraping der öffentlichen „Mannschaftsmeldungen/Spielerliste“-Seite / `groupPools`)** als klare, reproduzierbare Anleitung mit lauffähigem Code. Du füllst nur die Platzhalter **[Liga]**, **[Sprache]**, **[Datenformat]** (und konkret: Domain, Saison, Runde, Group-ID).

---

# Ziel
Für **[Liga]** die Seite `groupPools` abrufen und alle Spieler samt **Q-TTR** teamweise extrahieren. Ausgabe in **[Datenformat]** (`json`, `csv`, `markdown`) mit Spaltenüberschriften in **[Sprache]** (`de`/`en`).

---

## 1) Parameter bestimmen (einmalig pro Liga)

- **Base-Domain** deines Verbandsportals, z. B. `https://wttv.click-tt.de` (je nach Verband: ttvn, rttv, batt, ttvwh, …).
- **Saison** exakt wie in der URL, z. B. `WTTV 24/25`.
- **Runde**: `vorrunde` oder `rueckrunde` (so steht’s in der URL).
- **Group-ID**: Zahl hinter `group=…` in der Liga-URL (z. B. `471869`).

Mit diesen Parametern ist die Ziel-Seite:
```
{BASE}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools?championship={SAISON}&displayTyp={RUNDE}&group={GROUP_ID}
```

---

## 2) Robust scrapen (Python, requests + BeautifulSoup)

Das Skript ist robust auf kleine HTML-Abweichungen: Es sucht Team-Überschriften und die nächste Tabelle, toleriert optionale Spalten, erkennt Q-TTR, entfernt Nicht-Ziffern sauber, prüft auf Login-/Fehlerseiten und exportiert in drei Formaten.

> Platzhalter: setze `BASE_URL`, `SAISON`, `RUNDE`, `GROUP_ID`, `SPRACHE`, `DATENFORMAT`.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrape Q-TTR aus click-TT groupPools.
Ausgabe als JSON/CSV/Markdown mit DE/EN-Headern.
"""

import argparse
import csv
import json
import re
import sys
import time
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    return (
        f"{base_url.rstrip('/')}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
        f"?championship={requests.utils.quote(saison)}"
        f"&displayTyp={runde}"
        f"&group={group_id}"
    )

def fetch_html(url: str, timeout: int = 30) -> str:
    headers = {
        # Freundlicher, „echter“ UA + leichtes Throttling
        "User-Agent": "Mozilla/5.0 (compatible; ttr-scraper/1.0; +https://example.org/bot-info)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    hints = [
        "anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
        "session abgelaufen", "access denied", "forbidden"
    ]
    for h in hints:
        if h in text:
            return h
    # Falls gar keine Tabellen vorhanden sind, ist evtl. die Seite leer/falsch
    if not soup.find("table"):
        return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Teams stehen typischerweise in H2/H3/H4, direkt gefolgt von einer Tabelle
    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team:
            continue

        # Nächste sinnvolle Tabelle
        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))
        if not table:
            continue

        # Header erkennen
        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        # Positionen potenzieller Spalten
        # Wir erlauben flexible Positionen, Q-TTR muss aber vorhanden sein
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            # Keine Q-TTR Spalte? Dann ist es nicht die richtige Tabelle
            continue

        # Rang und Name heuristisch finden
        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        # Name kann "Name, Vorname" oder getrennt sein
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)

        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr:
                continue

            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None

            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""

            # Optionale Zusatzspalten mitnehmen, wenn vorhanden
            extra = {}
            if len(cols) >= 5:
                # Häufig: Anmerkung, Status o.Ä.
                extra["anmerkung"] = cols[3]
                if len(cols) >= 5:
                    extra["status"] = cols[4]

            item = {
                "team": team,
                "rang": rang_val,
                "qttr": qttr_val,
                "name": name_val,
                **extra
            }

            # Nur „echte“ Zeilen (kein Summen-/Leerzeilen-Müll)
            if item["name"] or item["qttr"] is not None:
                results.append(item)

    return results

def export(rows: List[Dict], datenformat: str, sprache: str) -> None:
    if not rows:
        print("[]")
        return
    # Sprachen-Header
    headers_de = ["Team", "Rang", "Q-TTR", "Name", "Anmerkung", "Status"]
    headers_en = ["Team", "Slot", "Q-TTR", "Name", "Note", "Status"]
    headers = headers_de if sprache.lower().startswith("de") else headers_en

    # Reihen in ein kanonisches Feld-Set gießen
    def row_to_list(r):
        return [
            r.get("team", ""),
            r.get("rang", ""),
            r.get("qttr", ""),
            r.get("name", ""),
            r.get("anmerkung", ""),
            r.get("status", ""),
        ]

    if datenformat == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif datenformat == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(row_to_list(r))
    elif datenformat == "markdown":
        print("| " + " | ".join(headers) + " |")
        print("|" + "|".join(["---"] * len(headers)) + "|")
        for r in rows:
            vals = row_to_list(r)
            print("| " + " | ".join("" if v is None else str(v) for v in vals) + " |")
    else:
        raise SystemExit(f"Unbekanntes Datenformat: {datenformat}")

def main():
    ap = argparse.ArgumentParser(description="Q-TTR aus click-TT groupPools scrapen")
    ap.add_argument("--base-url", required=True, help="z.B. https://wttv.click-tt.de")
    ap.add_argument("--saison", required=True, help='z.B. "WTTV 24/25" (genau wie in der URL)')
    ap.add_argument("--runde", required=True, choices=["vorrunde", "rueckrunde"], help="Rundenkennzeichen")
    ap.add_argument("--group", required=True, help="Group-ID aus der Liga-URL (z.B. 471869)")
    ap.add_argument("--sprache", default="de", help="de|en (für Spaltenüberschriften)")
    ap.add_argument("--format", default="json", choices=["json", "csv", "markdown"], help="Ausgabeformat")
    ap.add_argument("--sleep", type=float, default=0.0, help="optionale Pause in Sekunden (Höflichkeit)")
    args = ap.parse_args()

    url = build_url(args.base_url, args.saison, args.runde, args.group)
    if args.sleep > 0:
        time.sleep(args.sleep)

    html = fetch_html(url)
    maybe_block = looks_like_login_or_error(html)
    if maybe_block:
        sys.stderr.write(f"Hinweis: Seite wirkt gesperrt/unerwartet ({maybe_block}). Prüfe URL/Permissions.\n")
        # Wir brechen bewusst ab, um keine halbgaren Daten auszugeben:
        sys.exit(2)

    rows = parse_group_pools(html)
    export(rows, args.format, args.sprache)

if __name__ == "__main__":
    main()
```

### Nutzung
```bash
python ttr_group_pools.py \
  --base-url "https://[VERBAND].click-tt.de" \
  --saison "[WTTV 24/25]" \
  --runde "[vorrunde]" \
  --group "[471869]" \
  --sprache "[de]" \
  --format "[csv]"
```

---

## 3) Datenqualität & typische Stolpersteine

- **Exakte Saison/Runde:** Nimm die Werte genau wie sie in der URL stehen (Leerzeichen, Groß-/Kleinschreibung).
- **Q-TTR vs. TTR:** `groupPools` zeigt Q-TTR (Stichtagswerte). Dynamische Live-TTR sind über die öffentliche Seite nicht zuverlässig verfügbar.
- **„Weitere Spieler…“-Blöcke:** Sind meist bereits im HTML; wenn nicht, sind sie als Link nachladbar. Du kannst das Skript erweitern, diese Links zu folgen und die Zeilen zu mergen.
- **Login/Schutz:** Manche Saisons/Verbände erfordern Login. Das Skript erkennt typische Login-/Block-Texte und bricht sauber ab.
- **Respektiere Nutzungsbedingungen:** Moderates Abrufintervall (`--sleep 0.5`), keine parallelen Hammer-Scrapes.

---

## 4) Optionale Extras

### Team-Aggregationen (Beispiel)
Füge am Ende nach `rows = parse_group_pools(html)` z. B. Mittelwerte je Team hinzu:
```python
from statistics import mean
team_avgs = {}
for team in sorted({r["team"] for r in rows}):
    tvals = [r["qttr"] for r in rows if r["team"] == team and isinstance(r["qttr"], int)]
    team_avgs[team] = mean(tvals) if tvals else None
print(json.dumps({"team_avg_qttr": team_avgs}, ensure_ascii=False, indent=2))
```

---

## 5) Kurz-Variante in Node.js (Cheerio)
Wenn du lieber JS nimmst, hier der Kern (identische Platzhalter, minimal gehalten):

```js
import axios from "axios";
import * as cheerio from "cheerio";

const BASE_URL = "https://[VERBAND].click-tt.de";
const SAISON   = "[WTTV 24/25]";
const RUNDE    = "[vorrunde]";                     // "vorrunde" | "rueckrunde"
const GROUP_ID = "[471869]";

const url = `${BASE_URL}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools` +
            `?championship=${encodeURIComponent(SAISON)}` +
            `&displayTyp=${RUNDE}&group=${GROUP_ID}`;

const { data: html } = await axios.get(url, {
  headers: { "User-Agent": "ttr-scraper/1.0" },
  timeout: 30000
});

const $ = cheerio.load(html);
const out = [];

$("h2, h3, h4").each((_, h) => {
  const team = $(h).text().trim();
  const table = $(h).nextAll("table").filter((_, t) => $(t).find("thead").length).first();
  if (!table.length) return;

  const headers = table.find("thead th").map((_, th) => $(th).text().trim().toLowerCase()).get();
  const idxQttr = headers.findIndex(h => h.includes("q-ttr") || h.includes("qttr"));
  if (idxQttr === -1) return;

  const idxRang = headers.findIndex(h => h.startsWith("rang") || h.startsWith("pos"));
  const idxName = headers.findIndex(h => h.includes("name"));

  table.find("tbody tr").each((_, tr) => {
    const cols = $(tr).find("td").map((__, td) => $(td).text().trim()).get();
    if (!cols.length) return;
    const qttr = (cols[idxQttr] || "").replace(/[^\d-]/g, "");
    out.push({
      team,
      rang:  (idxRang >= 0 ? cols[idxRang] : "") || "",
      qttr:  qttr ? Number(qttr) : null,
      name:  (idxName >= 0 ? cols[idxName] : "") || "",
      anmerkung: cols[3] || "",
      status:    cols[4] || ""
    });
  });
});

console.log(JSON.stringify(out, null, 2));
```

---

## Was jetzt?
Sag mir **[Liga]** (Domain + Saison + Runde + Group-ID), **[Sprache]** und **[Datenformat]** — dann setze ich dir die Platzhalter in ein fertiges Skript und (wenn du magst) ergänze Team-Durchschnitt, Top-10 und CSV-Export für Excel/BI.

### 6. Benutzer

implementire für die eingaben eine gui inkl. exit button

### 7. Assistent

Alles klar — hier ist **Weg 1** mit einer kleinen **GUI** für die Eingaben (inkl. **Exit-Button**). Das Tool lädt die `groupPools`-Seite deiner [Liga], extrahiert alle Spieler samt **Q-TTR** und zeigt eine Vorschau. Auf Wunsch speicherst du die Daten als **[Datenformat]** (`json`, `csv`, `markdown`).  
Benötigt: **Python 3.9+**, `requests`, `beautifulsoup4` (Tkinter ist bei Python dabei).

### Installation
```bash
pip install requests beautifulsoup4
```

### Start
```bash
python ttr_gui.py
```

---

## `ttr_gui.py`
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI zum Auslesen der Q-TTR-Werte aus click-TT (Weg 1: groupPools scrapen).

Funktionen:
- Eingabemaske für Base-URL, Saison, Runde, Group-ID, Sprache, Datenformat
- Abruf & Parsing (requests + BeautifulSoup)
- Vorschau in einer Tabelle
- Export als JSON/CSV/Markdown
- Exit-Button

Hinweis: Respektiere Nutzungsbedingungen/Rate-Limits der Portale.
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (
        f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
        f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}"
    )

def fetch_html(url: str, timeout: int = 30) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ttr-gui/1.0; +https://example.org/bot-info)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    hints = [
        "anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
        "session abgelaufen", "access denied", "forbidden"
    ]
    for h in hints:
        if h in text:
            return h
    if not soup.find("table"):
        return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict] = []

    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team:
            continue

        table = heading.find_next(
            lambda tag: tag.name == "table" and tag.find("thead")
        )
        if not table:
            continue

        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            # nicht die gewünschte Tabelle
            continue

        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)

        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr:
                continue

            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None

            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""

            # optionale Zusatzspalten, wenn vorhanden
            extra = {}
            if len(cols) >= 4:
                extra["anmerkung"] = cols[3]
            if len(cols) >= 5:
                extra["status"] = cols[4]

            item = {
                "team": team,
                "rang": rang_val,
                "qttr": qttr_val,
                "name": name_val,
                **extra
            }
            if item["name"] or item["qttr"] is not None:
                results.append(item)

    return results

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers_de = ["Team", "Rang", "Q-TTR", "Name", "Anmerkung", "Status"]
    headers_en = ["Team", "Slot", "Q-TTR", "Name", "Note", "Status"]
    headers = headers_de if sprache.lower().startswith("de") else headers_en

    def row_to_list(r: Dict) -> List:
        return [
            r.get("team", ""),
            r.get("rang", ""),
            r.get("qttr", ""),
            r.get("name", ""),
            r.get("anmerkung", ""),
            r.get("status", ""),
        ]

    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        # utf-8-sig für Excel-Kompatibilität
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for r in rows:
                w.writerow(row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows:
                vals = row_to_list(r)
                f.write("| " + " | ".join("" if v is None else str(v) for v in vals) + " |\n")
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        # Eingaben
        frm = ttk.Frame(root, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        for i in range(6):
            frm.columnconfigure(i, weight=1)

        self.var_base = tk.StringVar(value="https://wttv.click-tt.de")
        self.var_saison = tk.StringVar(value="WTTV 24/25")
        self.var_runde = tk.StringVar(value="vorrunde")
        self.var_group = tk.StringVar(value="")
        self.var_sprache = tk.StringVar(value="de")
        self.var_format = tk.StringVar(value="json")

        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=5, sticky="ew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)

        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde, values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        r += 1
        ttk.Label(frm, text="Group-ID (…group=####)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_group).grid(row=r, column=1, sticky="ew", padx=6, pady=3)

        ttk.Label(frm, text="Sprache").grid(row=r, column=2, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de", "en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Datenformat").grid(row=r, column=4, sticky="e")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format, values=["json", "csv", "markdown"], state="readonly")
        self.cmb_format.grid(row=r, column=5, sticky="ew", padx=6)

        # Buttons
        r += 1
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=r, column=0, columnspan=6, sticky="ew", pady=(6, 3))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        btn_frame.columnconfigure(3, weight=1)

        self.btn_fetch = ttk.Button(btn_frame, text="Abrufen", command=self.on_fetch)
        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")

        self.btn_export = ttk.Button(btn_frame, text="Speichern …", command=self.on_export, state="disabled")
        self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")

        self.btn_clear = ttk.Button(btn_frame, text="Leeren", command=self.on_clear)
        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")

        self.btn_exit = ttk.Button(btn_frame, text="Exit", command=root.destroy)
        self.btn_exit.grid(row=0, column=3, padx=4, sticky="ew")

        # Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word")
        self.txt_status.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team", "rang", "qttr", "name", "anmerkung", "status"), show="headings", height=12)
        for col, text in [
            ("team", "Team"),
            ("rang", "Rang"),
            ("qttr", "Q-TTR"),
            ("name", "Name"),
            ("anmerkung", "Anmerkung"),
            ("status", "Status"),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        # Resize behavior
        frm.rowconfigure(r-1, weight=0)   # status
        frm.rowconfigure(r,   weight=1)   # table

        # Datencontainer
        self.rows: List[Dict] = []

    # ------------- GUI Helpers -------------

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n")
        self.txt_status.see("end")

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.rows = []
        self.btn_export.config(state="disabled")

    # ------------- Actions -------------

    def on_fetch(self):
        base = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde = self.var_runde.get().strip()
        group = self.var_group.get().strip()

        if not base or not saison or not runde or not group:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Group-ID angeben.")
            return

        url = build_url(base, saison, runde, group)
        self.on_clear()
        self.log(f"Abruf: {url}")
        self.set_busy(True)

        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Group-ID)."))
                return
            # Optional: Team-Mittelwerte ins Log
            avgs = self._team_avgs(rows)
            self.root.after(0, lambda: self._update_rows(rows, avgs))
        except Exception as e:
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg)
        self.set_busy(False)
        self.btn_export.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        # Vorschau füllen
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(
                r.get("team",""),
                r.get("rang",""),
                r.get("qttr",""),
                r.get("name",""),
                r.get("anmerkung",""),
                r.get("status",""),
            ))
        # Team-Mittelwerte ins Statuslog
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False)
        self.btn_export.config(state="normal")

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen.")
            return
        fmt = self.var_format.get()
        sprache = self.var_sprache.get()
        ext = {"json": ".json", "csv": ".csv", "markdown": ".md"}[fmt]
        path = filedialog.asksaveasfilename(
            title="Speichern unter",
            defaultextension=ext,
            filetypes=[
                ("JSON", "*.json"),
                ("CSV", "*.csv"),
                ("Markdown", "*.md"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if not path:
            return
        try:
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

def main():
    root = tk.Tk()
    # kleines, angenehmes Default-Scaling
    try:
        if sys.platform.startswith("win"):
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass
    root.geometry("1000x600")
    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

---

### Nutzungshinweise
- **Base-URL** entspricht deinem Landes-/Verbandsportal, z. B. `https://wttv.click-tt.de`, `https://ttvn.click-tt.de`, etc.  
- **Saison/Runde** exakt wie in der Liga-URL (z. B. `WTTV 24/25`, `vorrunde`).  
- **Group-ID** ist die Zahl hinter `group=` in der Liga-URL.  
- Das Tool erkennt typische Login-/Block-Seiten und meldet das im Statusfeld.  
- **CSV** wird als `utf-8-sig` gespeichert, damit Excel die Umlaute korrekt liest.

Mögliche nächste Ausbaustufen: automatisches Folgen von „Weitere Spieler…“-Links, Proxys/Timeout-Tuning, sowie ein Kombi-Export, der zusätzlich Team-Aggregationen (Durchschnitt, Median, Top-N) mitschreibt.

### 8. Benutzer

base-url: https://ttbw.click-tt.de

### 9. Assistent

Nice — Base-URL ist gesetzt. Du brauchst am Skript nur **eine** Zeile anzupassen (Default-Wert der GUI) – alles andere bleibt gleich.

### Änderung im GUI-Skript (`ttr_gui.py`)
Ersetze in `__init__` die Zeile für `self.var_base` durch diese hier:
```python
self.var_base = tk.StringVar(value="https://ttbw.click-tt.de")
```

Fertig. Beim Start ist das Feld „Base-URL (Verband)“ dann bereits mit `https://ttbw.click-tt.de` befüllt.

---

### Kurz-Check: so nutzt du’s jetzt
1) `python ttr_gui.py` starten.  
2) In der GUI nur noch **Saison** (genau wie in der URL, z. B. `TTBW 24/25`), **Runde** (`vorrunde`/`rueckrunde`) und **Group-ID** (die Zahl hinter `group=` in der Liga-URL) eintragen.  
3) **Abrufen** → Vorschau checken → **Speichern …** (Format `json|csv|markdown`).  
4) **Exit** beendet das Tool.

Tipp fürs Finden der Group-ID: Liga im Browser öffnen → Menü „Mannschaftsmeldungen/Spielerliste“ → in der Adresszeile die Zahl hinter `group=` kopieren.

Wenn du mir Saison/Runde/Group-ID deiner Liga gibst, packe ich dir das Skript auf Wunsch fix & fertig mit allen Feldern vorbefüllt und optionalem CSV-Export für Excel.

### 10. Benutzer

Saison 2025/26, Runde vorrunde,

### 11. Assistent

Perfekt — ich setze dir die Defaults in der GUI auf deine Angaben.

### In `ttr_gui.py` diese drei Zeilen anpassen (im `__init__` der Klasse `TTRScraperGUI`)
```python
self.var_base   = tk.StringVar(value="https://ttbw.click-tt.de")
self.var_saison = tk.StringVar(value="TTBW 2025/26")   # exakt wie in der URL; falls dort z.B. "TTBW 25/26" steht, bitte anpassen
self.var_runde  = tk.StringVar(value="vorrunde")
```

Danach starten:
```bash
python ttr_gui.py
```

In der GUI trägst du nur noch die **Group-ID** ein (die Zahl hinter `group=` in der Liga-URL unter „Mannschaftsmeldungen/Spielerliste“), klickst **Abrufen**, prüfst die Vorschau und speicherst bei Bedarf als JSON/CSV/Markdown.  
Tipp: Wenn du mir die **Group-ID** nennst, setze ich dir auch die gleich als Default rein.

### 12. Benutzer

group-id: 494514

### 13. Assistent

Nice — hier ist die **fertig vorbefüllte GUI** für Weg 1 mit deinen Parametern:

- Base-URL: `https://ttbw.click-tt.de`  
- Saison: `TTBW 2025/26` *(falls die echte URL „TTBW 25/26“ schreibt, kannst du es im Feld anpassen)*  
- Runde: `vorrunde`  
- Group-ID: `494514`  
- Exit-Button ist drin.

Installiere einmalig `requests` und `beautifulsoup4`, starte dann das Skript.

```bash
pip install requests beautifulsoup4
python ttr_gui.py
```

---

## `ttr_gui.py`
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI zum Auslesen der Q-TTR-Werte aus click-TT (Weg 1: groupPools scrapen).

Voreinstellungen:
- Base-URL: https://ttbw.click-tt.de
- Saison:    TTBW 2025/26   (prüfe die Schreibweise in der echten URL, z.B. ggf. "TTBW 25/26")
- Runde:     vorrunde
- Group-ID:  494514

Funktionen:
- Eingabemaske für Base-URL, Saison, Runde, Group-ID, Sprache, Datenformat
- Abruf & Parsing (requests + BeautifulSoup)
- Vorschau in einer Tabelle
- Export als JSON/CSV/Markdown
- Exit-Button

Hinweis: Respektiere Nutzungsbedingungen/Rate-Limits der Portale.
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (
        f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
        f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}"
    )

def fetch_html(url: str, timeout: int = 30) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ttr-gui/1.0; +https://example.org/bot-info)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    hints = [
        "anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
        "session abgelaufen", "access denied", "forbidden"
    ]
    for h in hints:
        if h in text:
            return h
    if not soup.find("table"):
        return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict] = []

    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team:
            continue

        table = heading.find_next(
            lambda tag: tag.name == "table" and tag.find("thead")
        )
        if not table:
            continue

        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            # nicht die gewünschte Tabelle
            continue

        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)

        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr:
                continue

            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None

            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""

            # optionale Zusatzspalten, wenn vorhanden
            extra = {}
            if len(cols) >= 4:
                extra["anmerkung"] = cols[3]
            if len(cols) >= 5:
                extra["status"] = cols[4]

            item = {
                "team": team,
                "rang": rang_val,
                "qttr": qttr_val,
                "name": name_val,
                **extra
            }
            if item["name"] or item["qttr"] is not None:
                results.append(item)

    return results

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers_de = ["Team", "Rang", "Q-TTR", "Name", "Anmerkung", "Status"]
    headers_en = ["Team", "Slot", "Q-TTR", "Name", "Note", "Status"]
    headers = headers_de if sprache.lower().startswith("de") else headers_en

    def row_to_list(r: Dict) -> List:
        return [
            r.get("team", ""),
            r.get("rang", ""),
            r.get("qttr", ""),
            r.get("name", ""),
            r.get("anmerkung", ""),
            r.get("status", ""),
        ]

    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        # utf-8-sig für Excel-Kompatibilität
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for r in rows:
                w.writerow(row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows:
                vals = row_to_list(r)
                f.write("| " + " | ".join("" if v is None else str(v) for v in vals) + " |\n")
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        # Eingaben
        frm = ttk.Frame(root, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        for i in range(6):
            frm.columnconfigure(i, weight=1)

        # Voreinstellungen nach Vorgabe:
        self.var_base   = tk.StringVar(value="https://ttbw.click-tt.de")
        self.var_saison = tk.StringVar(value="TTBW 2025/26")  # ggf. in der echten URL "TTBW 25/26"
        self.var_runde  = tk.StringVar(value="vorrunde")
        self.var_group  = tk.StringVar(value="494514")
        self.var_sprache = tk.StringVar(value="de")
        self.var_format  = tk.StringVar(value="json")

        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=5, sticky="ew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)

        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde, values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        r += 1
        ttk.Label(frm, text="Group-ID (…group=####)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_group).grid(row=r, column=1, sticky="ew", padx=6, pady=3)

        ttk.Label(frm, text="Sprache").grid(row=r, column=2, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de", "en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Datenformat").grid(row=r, column=4, sticky="e")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format, values=["json", "csv", "markdown"], state="readonly")
        self.cmb_format.grid(row=r, column=5, sticky="ew", padx=6)

        # Buttons
        r += 1
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=r, column=0, columnspan=6, sticky="ew", pady=(6, 3))
        for i in range(4):
            btn_frame.columnconfigure(i, weight=1)

        self.btn_fetch = ttk.Button(btn_frame, text="Abrufen", command=self.on_fetch)
        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")

        self.btn_export = ttk.Button(btn_frame, text="Speichern …", command=self.on_export, state="disabled")
        self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")

        self.btn_clear = ttk.Button(btn_frame, text="Leeren", command=self.on_clear)
        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")

        self.btn_exit = ttk.Button(btn_frame, text="Exit", command=root.destroy)
        self.btn_exit.grid(row=0, column=3, padx=4, sticky="ew")

        # Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word")
        self.txt_status.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team", "rang", "qttr", "name", "anmerkung", "status"), show="headings", height=12)
        for col, text in [
            ("team", "Team"),
            ("rang", "Rang"),
            ("qttr", "Q-TTR"),
            ("name", "Name"),
            ("anmerkung", "Anmerkung"),
            ("status", "Status"),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        # Resize behavior
        frm.rowconfigure(r-1, weight=0)   # status
        frm.rowconfigure(r,   weight=1)   # table

        # Datencontainer
        self.rows: List[Dict] = []

    # ------------- GUI Helpers -------------

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n")
        self.txt_status.see("end")

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.rows = []
        self.btn_export.config(state="disabled")

    # ------------- Actions -------------

    def on_fetch(self):
        base = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde = self.var_runde.get().strip()
        group = self.var_group.get().strip()

        if not base or not saison or not runde or not group:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Group-ID angeben.")
            return

        url = build_url(base, saison, runde, group)
        self.on_clear()
        self.log(f"Abruf: {url}")
        self.set_busy(True)

        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Group-ID)."))
                return
            avgs = self._team_avgs(rows)
            self.root.after(0, lambda: self._update_rows(rows, avgs))
        except Exception as e:
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs: Dict[str, Optional[float]] = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg)
        self.set_busy(False)
        self.btn_export.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        # Vorschau füllen
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(
                r.get("team",""),
                r.get("rang",""),
                r.get("qttr",""),
                r.get("name",""),
                r.get("anmerkung",""),
                r.get("status",""),
            ))
        # Team-Mittelwerte ins Statuslog
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False)
        self.btn_export.config(state="normal")

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen.")
            return
        fmt = self.var_format.get()
        sprache = self.var_sprache.get()
        ext = {"json": ".json", "csv": ".csv", "markdown": ".md"}[fmt]
        path = filedialog.asksaveasfilename(
            title="Speichern unter",
            defaultextension=ext,
            filetypes=[
                ("JSON", "*.json"),
                ("CSV", "*.csv"),
                ("Markdown", "*.md"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if not path:
            return
        try:
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

def main():
    root = tk.Tk()
    # optionales DPI-Scaling für Windows
    try:
        if sys.platform.startswith("win"):
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass
    root.geometry("1000x600")
    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

---

Starten, **Abrufen** klicken, Vorschau checken, als `json/csv/markdown` speichern, **Exit** beendet das Tool.  
Für die nächste Evolutionsstufe lohnt sich ein Auto-Fetch der „Weitere Spieler…“-Links sowie ein Button „Team-Mittel/Top-10 exportieren“.

### 14. Benutzer

erstelle eine commit test in deutsch

### 15. Benutzer

erstelle einen commit text in deutsch

### 16. Assistent

```text
feat(gui): Tkinter-GUI für click-TT Q-TTR-Scraper + Export

- Neue Desktop-GUI (ttr_gui.py) für Weg 1 (groupPools-Scraping)
- Eingabefelder: Base-URL, Saison, Runde, Group-ID, Sprache, Datenformat
- Voreinstellungen: Base-URL https://ttbw.click-tt.de, Saison "TTBW 2025/26", Runde "vorrunde", Group-ID 494514
- Vorschau-Tabelle (Treeview) mit Team, Rang, Q-TTR, Name, Anmerkung, Status
- Export als JSON/CSV/Markdown (CSV als UTF-8-SIG für Excel)
- Buttons: Abrufen, Speichern, Leeren, Exit; Status-Log integriert
- Fehlerbehandlung: Erkennung von Login-/Blockseiten, robuster Parser
- Zusatz: Team-Mittelwerte (Q-TTR) im Statusbereich
```

Wenn du ein anderes Commit-Schema (z. B. ohne Conventional Commits) bevorzugst, liefere ich dir gern eine passende Variante oder eine Kurzfassung für „squash merges“.

### 17. Benutzer

neuer code: #!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

GUI zum Auslesen der Q-TTR-Werte aus click-TT (Weg 1: groupPools scrapen).



Voreinstellungen:

- Base-URL: https://ttbw.click-tt.de

- Saison:    TTBW 2025/26   (prüfe die Schreibweise in der echten URL, z.B. ggf. "TTBW 25/26")

- Runde:     vorrunde

- Group-ID:  494514



Funktionen:

- Eingabemaske für Base-URL, Saison, Runde, Group-ID, Sprache, Datenformat

- Abruf & Parsing (requests + BeautifulSoup)

- Vorschau in einer Tabelle

- Export als JSON/CSV/Markdown

- Exit-Button



Hinweis: Respektiere Nutzungsbedingungen/Rate-Limits der Portale.

"""



import csv

import json

import re

import sys

import threading

from statistics import mean

from typing import Dict, List, Optional

from urllib.parse import quote

import os



import requests

from bs4 import BeautifulSoup



import tkinter as tk

from tkinter import ttk, messagebox, filedialog



CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".ttrscraper_config.json")



def save_config(config: dict):

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:

        json.dump(config, f, ensure_ascii=False, indent=2)



def load_config() -> dict:

    if os.path.exists(CONFIG_PATH):

        with open(CONFIG_PATH, "r", encoding="utf-8") as f:

            return json.load(f)

    return {}



# -------------------------------

# Scraping-Logik (Weg 1)

# -------------------------------



def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:

    base = base_url.rstrip("/")

    return (

        f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"

        f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}"

    )



def fetch_html(url: str, timeout: int = 30) -> str:

    headers = {

        "User-Agent": "Mozilla/5.0 (compatible; ttr-gui/1.0; +https://example.org/bot-info)"

    }

    resp = requests.get(url, headers=headers, timeout=timeout)

    resp.raise_for_status()

    return resp.text



def looks_like_login_or_error(html: str) -> Optional[str]:

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True).lower()

    hints = [

        "anmeldung", "login", "zugriff verweigert", "nicht berechtigt",

        "session abgelaufen", "access denied", "forbidden"

    ]

    for h in hints:

        if h in text:

            return h

    if not soup.find("table"):

        return "keine tabellen gefunden"

    return None



def parse_group_pools(html: str) -> List[Dict]:

    soup = BeautifulSoup(html, "html.parser")

    results: List[Dict] = []



    for heading in soup.find_all(["h2", "h3", "h4"]):

        team = heading.get_text(strip=True)

        if not team:

            continue



        table = heading.find_next(

            lambda tag: tag.name == "table" and tag.find("thead")

        )

        if not table:

            continue



        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]

        try:

            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)

        except StopIteration:

            # nicht die gewünschte Tabelle

            continue



        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)

        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)



        for row in table.select("tbody tr"):

            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]

            if not cols or len(cols) <= idx_qttr:

                continue



            qttr_raw = cols[idx_qttr]

            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)

            qttr_val = int(qttr_num) if qttr_num.isdigit() else None



            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""

            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""



            # optionale Zusatzspalten, wenn vorhanden

            extra = {}

            if len(cols) >= 4:

                extra["anmerkung"] = cols[3]

            if len(cols) >= 5:

                extra["status"] = cols[4]



            item = {

                "team": team,

                "rang": rang_val,

                "qttr": qttr_val,

                "name": name_val,

                **extra

            }

            if item["name"] or item["qttr"] is not None:

                results.append(item)



    return results



def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:

    headers_de = ["Team", "Rang", "Q-TTR", "Name", "Anmerkung", "Status"]

    headers_en = ["Team", "Slot", "Q-TTR", "Name", "Note", "Status"]

    headers = headers_de if sprache.lower().startswith("de") else headers_en



    def row_to_list(r: Dict) -> List:

        return [

            r.get("team", ""),

            r.get("rang", ""),

            r.get("qttr", ""),

            r.get("name", ""),

            r.get("anmerkung", ""),

            r.get("status", ""),

        ]



    if datenformat == "json":

        with open(path, "w", encoding="utf-8") as f:

            json.dump(rows, f, ensure_ascii=False, indent=2)

    elif datenformat == "csv":

        # utf-8-sig für Excel-Kompatibilität

        with open(path, "w", encoding="utf-8-sig", newline="") as f:

            w = csv.writer(f)

            w.writerow(headers)

            for r in rows:

                w.writerow(row_to_list(r))

    elif datenformat == "markdown":

        with open(path, "w", encoding="utf-8") as f:

            f.write("| " + " | ".join(headers) + " |\n")

            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")

            for r in rows:

                vals = row_to_list(r)

                f.write("| " + " | ".join("" if v is None else str(v) for v in vals) + " |\n")

    else:

        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")



# -------------------------------

# GUI

# -------------------------------



class TTRScraperGUI:

    def __init__(self, root: tk.Tk):

        self.root = root

        root.title("click-TT Q-TTR Scraper (Weg 1)")



        # Eingaben

        frm = ttk.Frame(root, padding=12)

        frm.grid(row=0, column=0, sticky="nsew")



        root.columnconfigure(0, weight=1)

        root.rowconfigure(0, weight=1)

        for i in range(6):

            frm.columnconfigure(i, weight=1)



        # Voreinstellungen nach Vorgabe oder aus Config:

        config = load_config()

        self.var_base   = tk.StringVar(value=config.get("base", "https://ttbw.click-tt.de"))

        self.var_saison = tk.StringVar(value=config.get("saison", "TTBW 2025/26"))

        self.var_runde  = tk.StringVar(value=config.get("runde", "vorrunde"))

        self.var_group  = tk.StringVar(value=config.get("group", "494514"))

        self.var_sprache = tk.StringVar(value=config.get("sprache", "de"))

        self.var_format  = tk.StringVar(value=config.get("format", "json"))



        r = 0

        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")

        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=5, sticky="ew", padx=6, pady=3)



        r += 1

        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")

        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)



        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")

        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde, values=["vorrunde", "rueckrunde"], state="readonly")

        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)



        r += 1

        ttk.Label(frm, text="Group-ID (…group=####)").grid(row=r, column=0, sticky="w")

        ttk.Entry(frm, textvariable=self.var_group).grid(row=r, column=1, sticky="ew", padx=6, pady=3)



        ttk.Label(frm, text="Sprache").grid(row=r, column=2, sticky="e")

        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de", "en"], state="readonly")

        self.cmb_sprache.grid(row=r, column=3, sticky="ew", padx=6)



        ttk.Label(frm, text="Datenformat").grid(row=r, column=4, sticky="e")

        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format, values=["json", "csv", "markdown"], state="readonly")

        self.cmb_format.grid(row=r, column=5, sticky="ew", padx=6)



        # Buttons

        r += 1

        btn_frame = ttk.Frame(frm)

        btn_frame.grid(row=r, column=0, columnspan=6, sticky="ew", pady=(6, 3))

        for i in range(5):

            btn_frame.columnconfigure(i, weight=1)



        self.btn_fetch = ttk.Button(btn_frame, text="Abrufen", command=self.on_fetch)

        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")



        self.btn_export = ttk.Button(btn_frame, text="Speichern …", command=self.on_export, state="disabled")

        self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")



        self.btn_clear = ttk.Button(btn_frame, text="Leeren", command=self.on_clear)

        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")



        self.btn_settings = ttk.Button(btn_frame, text="Einstellung", command=self.on_settings)

        self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")



        self.btn_exit = ttk.Button(btn_frame, text="Exit", command=root.destroy)

        self.btn_exit.grid(row=0, column=4, padx=4, sticky="ew")



        # Status + Vorschau

        r += 1

        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")

        self.txt_status = tk.Text(frm, height=5, wrap="word")

        self.txt_status.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)



        r += 1

        ttk.Label(frm, text="Vorschau").grid(row=r, column=0, sticky="w")

        self.tree = ttk.Treeview(frm, columns=("team", "rang", "qttr", "name", "anmerkung", "status"), show="headings", height=12)

        for col, text in [

            ("team", "Team"),

            ("rang", "Rang"),

            ("qttr", "Q-TTR"),

            ("name", "Name"),

            ("anmerkung", "Anmerkung"),

            ("status", "Status"),

        ]:

            self.tree.heading(col, text=text)

            self.tree.column(col, stretch=True, width=120)

        self.tree.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)



        # Resize behavior

        frm.rowconfigure(r-1, weight=0)   # status

        frm.rowconfigure(r,   weight=1)   # table



        # Datencontainer

        self.rows: List[Dict] = []



    # ------------- GUI Helpers -------------



    def log(self, msg: str):

        self.txt_status.insert("end", msg + "\n")

        self.txt_status.see("end")



    def set_busy(self, busy: bool):

        state = "disabled" if busy else "normal"

        self.btn_fetch.config(state=state)

        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))



    def on_clear(self):

        self.txt_status.delete("1.0", "end")

        for i in self.tree.get_children():

            self.tree.delete(i)

        self.rows = []

        self.btn_export.config(state="disabled")



    # ------------- Actions -------------



    def on_fetch(self):

        base = self.var_base.get().strip()

        saison = self.var_saison.get().strip()

        runde = self.var_runde.get().strip()

        group = self.var_group.get().strip()



        if not base or not saison or not runde or not group:

            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Group-ID angeben.")

            return



        url = build_url(base, saison, runde, group)

        self.on_clear()

        self.log(f"Abruf: {url}")

        self.set_busy(True)



        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()



    def _fetch_thread(self, url: str):

        try:

            html = fetch_html(url)

            issue = looks_like_login_or_error(html)

            if issue:

                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))

                return

            rows = parse_group_pools(html)

            if not rows:

                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Group-ID)."))

                return

            avgs = self._team_avgs(rows)

            self.root.after(0, lambda: self._update_rows(rows, avgs))

        except Exception as e:

            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))



    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:

        avgs: Dict[str, Optional[float]] = {}

        teams = sorted({r["team"] for r in rows})

        for t in teams:

            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]

            avgs[t] = (mean(vals) if vals else None)

        return avgs



    def _abort(self, msg: str):

        self.log(msg)

        self.set_busy(False)

        self.btn_export.config(state="disabled")



    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):

        self.rows = rows

        # Vorschau füllen

        for i in self.tree.get_children():

            self.tree.delete(i)

        for r in rows:

            self.tree.insert("", "end", values=(

                r.get("team",""),

                r.get("rang",""),

                r.get("qttr",""),

                r.get("name",""),

                r.get("anmerkung",""),

                r.get("status",""),

            ))

        # Team-Mittelwerte ins Statuslog

        self.log(f"{len(rows)} Zeilen geladen.")

        self.log("Team-Mittel (Q-TTR):")

        for t, v in avgs.items():

            self.log(f"  • {t}: {'' if v is None else round(v,1)}")

        self.set_busy(False)

        self.btn_export.config(state="normal")



    def on_export(self):

        if not self.rows:

            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen.")

            return

        fmt = self.var_format.get()

        sprache = self.var_sprache.get()

        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md"}

        if fmt not in ext_map:

            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}")

            return

        ext = ext_map[fmt]

        path = filedialog.asksaveasfilename(

            title="Speichern unter",

            defaultextension=ext,

            filetypes=[

                ("JSON", "*.json"),

                ("CSV", "*.csv"),

                ("Markdown", "*.md"),

                ("Alle Dateien", "*.*"),

            ],

        )

        if not path:

            return

        try:

            export_rows(self.rows, fmt, sprache, path)

            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")

        except Exception as e:

            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")



    def on_settings(self):

        # Einfaches Dialogfenster zum Speichern der aktuellen Konfiguration

        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):

            config = {

                "base": self.var_base.get(),

                "saison": self.var_saison.get(),

                "runde": self.var_runde.get(),

                "group": self.var_group.get(),

                "sprache": self.var_sprache.get(),

                "format": self.var_format.get(),

            }

            try:

                save_config(config)

                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")

            except Exception as e:

                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")



def main():

    root = tk.Tk()

    # optionales DPI-Scaling für Windows

    try:

        if sys.platform.startswith("win"):

            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)  # type: ignore

    except Exception:

        pass

    root.geometry("1000x600")

    app = TTRScraperGUI(root)

    root.mainloop()



if __name__ == "__main__":

    main()

### 18. Assistent

```text
feat(gui): Persistente Einstellungen + Settings-Button, verbesserter Export

- lädt Standardwerte aus ~/.ttrscraper_config.json (CONFIG_PATH)
- neuer Button „Einstellung“ zum Speichern der aktuellen Konfiguration
- Voreinstellungen: Base-URL https://ttbw.click-tt.de, Saison „TTBW 2025/26“, Runde „vorrunde“, Group-ID 494514
- Export: Validierung des Formats (json/csv/markdown) via ext_map; bessere Fehlermeldungen
- CSV-Export als UTF-8-SIG für Excel; Markdown/JSON unverändert
- robustes Parsing (Q-TTR/Rang/Name) und Erkennung von Login-/Blockseiten beibehalten
- UI/UX: Status-Log, Vorschau-Table, Threading mit root.after, Exit-/Leeren-/Speichern-Buttons

Hinweis: Bestehende Nutzer können ihre Defaults einmalig über „Einstellung“ speichern (Schreibrechte im Home-Verzeichnis erforderlich).
```

### 19. Benutzer

ich möchte die group id über ein pulldown wechseln können. die Einträge des Pulldown sollen über eine konfig seite pflegbar sein. hier möchte ich die Gruppe zb Kreisliga C2 eingeben können mit ihrer ID. Im Pulldown steht dann die Gruppe und für die suche wird die ID verwendet

### 20. Assistent

Hier ist dein GUI-Update: **Gruppen-Pulldown** mit frei pflegbaren Einträgen über eine **Konfig-Seite**. Im Dropdown siehst du die Bezeichnung (z. B. „Kreisliga C2“), für den Abruf wird automatisch die hinterlegte **Group-ID** verwendet. Die Einträge werden in `~/.ttrscraper_config.json` gespeichert.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI zum Auslesen der Q-TTR-Werte aus click-TT (Weg 1: groupPools scrapen).

Neu:
- Gruppen-Dropdown (Bezeichnung -> Group-ID)
- "Gruppen …"-Dialog zum Pflegen (Hinzufügen/Ändern/Löschen) der Einträge
- Ausgewählte Gruppe steuert die Suche (ID wird intern verwendet)
- Beides persistent in ~/.ttrscraper_config.json

Voreinstellungen:
- Base-URL: https://ttbw.click-tt.de
- Saison:    TTBW 2025/26   (prüfe die Schreibweise in der echten URL, ggf. "TTBW 25/26")
- Runde:     vorrunde
- Standard-Gruppe (Beispiel): Kreisliga C2 -> 494514
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote
import os

import requests
from bs4 import BeautifulSoup

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".ttrscraper_config.json")

# -------------------------------
# Config-IO
# -------------------------------

def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (
        f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
        f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}"
    )

def fetch_html(url: str, timeout: int = 30) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ttr-gui/1.1; +https://example.org/bot-info)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    hints = ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
             "session abgelaufen", "access denied", "forbidden"]
    for h in hints:
        if h in text:
            return h
    if not soup.find("table"):
        return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict] = []

    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team:
            continue

        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))
        if not table:
            continue

        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            continue

        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)

        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr:
                continue

            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None

            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""

            extra = {}
            if len(cols) >= 4:
                extra["anmerkung"] = cols[3]
            if len(cols) >= 5:
                extra["status"] = cols[4]

            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}
            if item["name"] or item["qttr"] is not None:
                results.append(item)

    return results

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers_de = ["Team", "Rang", "Q-TTR", "Name", "Anmerkung", "Status"]
    headers_en = ["Team", "Slot", "Q-TTR", "Name", "Note", "Status"]
    headers = headers_de if sprache.lower().startswith("de") else headers_en

    def row_to_list(r: Dict) -> List:
        return [r.get("team",""), r.get("rang",""), r.get("qttr",""),
                r.get("name",""), r.get("anmerkung",""), r.get("status","")]

    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for r in rows:
                w.writerow(row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows:
                vals = row_to_list(r)
                f.write("| " + " | ".join("" if v is None else str(v) for v in vals) + " |\n")
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        # Container
        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        for i in range(6): frm.columnconfigure(i, weight=1)

        # Config laden + Defaults
        cfg = load_config()
        self.groups: List[Dict[str,str]] = cfg.get("groups", [{"label": "Kreisliga C2", "id": "494514"}])

        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))
        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))
        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))
        # sichtbare Auswahl nach Label, ID wird intern gehalten/angezeigt
        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))
        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))
        self.var_group_label = tk.StringVar(value=default_label)
        self.var_group_id    = tk.StringVar(value=default_id)
        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))
        self.var_format  = tk.StringVar(value=cfg.get("format","json"))

        # --- Zeile: Base-URL
        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=5, sticky="ew", padx=6, pady=3)

        # --- Zeile: Saison / Runde
        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)

        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,
                                      values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        # --- Zeile: Gruppe (Dropdown) + ID-View
        r += 1
        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")
        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,
                                      values=self._group_labels(), state="readonly")
        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)

        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")
        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")
        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)

        # --- Zeile: Datenformat
        r += 1
        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,
                                       values=["json","csv","markdown"], state="readonly")
        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)

        # --- Button-Zeile
        r += 1
        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=6, sticky="ew", pady=(6,3))
        for i in range(6): btn_frame.columnconfigure(i, weight=1)

        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",       command=self.on_fetch);    self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")
        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",   command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")
        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",        command=self.on_clear);    self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")
        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",   command=self.on_settings); self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")
        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",     command=self.on_groups);   self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")
        self.btn_exit     = ttk.Button(btn_frame, text="Exit",          command=root.destroy);     self.btn_exit.grid(row=0, column=5, padx=4, sticky="ew")

        # --- Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=12)
        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:
            self.tree.heading(col, text=text); self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        frm.rowconfigure(r-1, weight=0)  # status
        frm.rowconfigure(r,   weight=1)  # table

        self.rows: List[Dict] = []
        # beim Start sicherstellen, dass ID zur Auswahl passt
        self._sync_group_id_to_label()

    # -------------------- Helpers --------------------

    def _group_labels(self) -> List[str]:
        return [g.get("label","") for g in self.groups]

    def _group_map(self) -> Dict[str,str]:
        return {g.get("label",""): g.get("id","") for g in self.groups}

    def _sync_group_id_to_label(self):
        gid = self._group_map().get(self.var_group_label.get().strip(), "")
        self.var_group_id.set(gid)

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.rows = []; self.btn_export.config(state="disabled")

    # -------------------- Actions --------------------

    def on_group_selected(self, _evt=None):
        self._sync_group_id_to_label()

    def on_fetch(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return

        url = build_url(base, saison, runde, gid)
        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))
                return
            avgs = self._team_avgs(rows)
            self.root.after(0, lambda: self._update_rows(rows, avgs))
        except Exception as e:
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs: Dict[str, Optional[float]] = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),
                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False); self.btn_export.config(state="normal")

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return
        fmt = self.var_format.get(); sprache = self.var_sprache.get()
        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md"}
        if fmt not in ext_map:
            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return
        path = filedialog.asksaveasfilename(title="Speichern unter", defaultextension=ext_map[fmt],
                                            filetypes=[("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")])
        if not path: return
        try:
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    def on_settings(self):
        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):
            try:
                self._save_current_config()
                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")

    def on_groups(self):
        # Dialog zum Verwalten der Gruppen (Label<->ID)
        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()
        dlg.geometry("560x380")
        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)
        # Tree
        cols = ("label","id")
        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)
        tree.heading("label", text="Bezeichnung")
        tree.heading("id",    text="Group-ID")
        tree.column("label", stretch=True, width=320)
        tree.column("id",    stretch=False, width=120)
        tree.pack(fill="both", expand=True, pady=(0,8))

        # Form
        form = ttk.Frame(container); form.pack(fill="x", pady=4)
        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")
        var_label = tk.StringVar()
        ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")
        var_id = tk.StringVar()
        ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)
        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))

        # Buttons
        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))
        def refresh_tree():
            for i in tree.get_children(): tree.delete(i)
            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))
        def select_from_tree(_evt=None):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values")
            var_label.set(vals[0]); var_id.set(vals[1])
        def add_or_update():
            label = var_label.get().strip()
            gid   = var_id.get().strip()
            if not label or not gid:
                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return
            if not gid.isdigit():
                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"):
                    return
            # prüfen, ob Label existiert -> Update, sonst Add
            for g in self.groups:
                if g.get("label","") == label:
                    g["id"] = gid
                    break
            else:
                self.groups.append({"label": label, "id": gid})
            refresh_tree(); self._refresh_group_dropdown()
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values")
            label = vals[0]
            self.groups = [g for g in self.groups if g.get("label","") != label]
            refresh_tree(); self._refresh_group_dropdown()
        def save_and_close():
            # Wenn aktuelle Auswahl einem gelöschten Label entspricht: leere ID setzen
            if self.var_group_label.get() not in self._group_labels():
                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")
            self._sync_group_id_to_label()
            try:
                self._save_current_config()
                messagebox.showinfo("Gespeichert", "Gruppen gespeichert.")
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Gruppen nicht speichern:\n{e}")

        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)
        ttk.Button(btns, text="Schließen & Speichern", command=save_and_close).pack(side="right", padx=4)

        tree.bind("<<TreeviewSelect>>", select_from_tree)
        refresh_tree()

    def _refresh_group_dropdown(self):
        self.cmb_group.config(values=self._group_labels())
        # Auswahl beibehalten, falls vorhanden
        if self.var_group_label.get() not in self._group_labels() and self._group_labels():
            self.var_group_label.set(self._group_labels()[0])
        self._sync_group_id_to_label()

    def _save_current_config(self):
        config = {
            "base": self.var_base.get(),
            "saison": self.var_saison.get(),
            "runde": self.var_runde.get(),
            "group_label": self.var_group_label.get(),
            "group": self.var_group_id.get(),
            "sprache": self.var_sprache.get(),
            "format": self.var_format.get(),
            "groups": self.groups,
        }
        save_config(config)

def main():
    root = tk.Tk()
    # optionales DPI-Scaling Windows
    try:
        if sys.platform.startswith("win"):
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass
    root.geometry("1000x600")
    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

Kurz benutzen: Starte das Script, wähle im **Gruppe**-Dropdown z. B. „Kreisliga C2“. Über **Gruppen …** pflegst du Bezeichnung ↔ ID (Hinzufügen/Aktualisieren/Löschen); gespeichert wird alles in `~/.ttrscraper_config.json`. Danach „Abrufen“ – die Suche nutzt automatisch die passende **Group-ID**.

### 21. Benutzer

was könnte ich noch optimieren

### 22. Assistent

Hier sind die sinnvollsten Optimierungen — pragmatisch, stabil, nerdfreundlich:

## Robustheit & Netzwerk
- **Retries mit Backoff:** vermeidet Abbrüche bei kurzen Aussetzern.
  ```python
  import requests
  from requests.adapters import HTTPAdapter
  from urllib3.util.retry import Retry

  def make_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=0.8,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET",))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "ttr-gui/1.2"})
    return s
  # dann: resp = make_session().get(url, timeout=30)
  ```
- **Antworten cachen (Entwicklung & Rate-Limit):**
  ```bash
  pip install requests-cache
  ```
  ```python
  import requests_cache
  requests_cache.install_cache("ttr_cache", expire_after=1800)  # 30 Minuten
  ```
- **Accept-Language setzen:** reduziert zufällige Layout-/Sprachwechsel.
  ```python
  s.headers["Accept-Language"] = "de-DE,de;q=0.9,en;q=0.5"
  ```

## Parser-Sicherheit
- **LXML nutzen** für Geschwindigkeit/Strenge: `pip install lxml` und `BeautifulSoup(html, "lxml")`.
- **Fallback-Strategie für Tabellen-Findung:** erst per „Q-TTR“-Spalte, dann per Tabellen-Caption/Überschrift; brich nur ab, wenn beide Pfade scheitern.
- **Name spalten:** „Nachname, Vorname“ sauber trennen und zusätzliche Felder ausgeben.

## UX der GUI
- **Dropdown sortierbar & suchbar:** Quickfilter über Entry-Feld; auf Eingabe live filtern.
- **Spaltensortierung in der Vorschau:** Klick auf Header sortiert auf/ab.
  ```python
  def make_treeview_sortable(tree):
      for col in tree["columns"]:
          tree.heading(col, text=tree.heading(col, "text"),
                       command=lambda c=col: sort_by(tree, c, False))

  def sort_by(tree, col, descending):
      data = [(tree.set(k, col), k) for k in tree.get_children("")]
      try:
          data.sort(key=lambda t: float(t[0].replace(",", ".")))
      except ValueError:
          data.sort(key=lambda t: t[0])
      if descending: data.reverse()
      for idx, item in enumerate(data):
          tree.move(item[1], "", idx)
      tree.heading(col, command=lambda: sort_by(tree, col, not descending))
  ```
- **„Im Browser öffnen“**: Button, der die aktuell generierte URL startet (`webbrowser.open(url)`).
- **Fenstergröße & Spaltenbreiten merken**: beim Beenden in die Config schreiben und beim Start wiederherstellen.
- **Gruppen-Dialog Quality of Life:** Deduplizierung (case-insensitive), Warnung bei leeren Labels, Undo (letzter Löschvorgang rückgängig machen).

## Export & Daten-Workflow
- **XLSX-Export** mit sauberer Typisierung:
  ```bash
  pip install openpyxl
  ```
  ```python
  from openpyxl import Workbook
  def export_xlsx(rows, path):
      wb = Workbook(); ws = wb.active; ws.title = "Q-TTR"
      ws.append(["Team","Rang","Q-TTR","Name","Anmerkung","Status"])
      for r in rows:
          ws.append([r.get("team"), r.get("rang"), r.get("qttr"),
                     r.get("name"), r.get("anmerkung"), r.get("status")])
      wb.save(path)
  ```
- **Aggregationen mitschreiben** (zweites Blatt „Stats“: Team-Mittel, Min/Max, Top-N).
- **Clipboard-Export**: Auswahl oder ganze Tabelle per `clipboard_clear()`/`clipboard_append()`.

## Architektur & Codequalität
- **Dataclasses** statt nackter Dicts:
  ```python
  from dataclasses import dataclass
  @dataclass
  class PlayerRow:
      team: str; rang: str; qttr: Optional[int]; name: str
      anmerkung: str = ""; status: str = ""
  ```
- **Modularisieren:** `scrape.py`, `export.py`, `gui.py`, `config.py`. So kannst du den Scraper auch headless im CI laufen lassen.
- **Typprüfung & Linting:** `pip install mypy ruff black` und einfache CI-Checks.
- **Konfig-Pfad plattformgerecht:** `pip install platformdirs`, dann `PlatformDirs("ttrscraper", "yourname").user_config_path` statt hartem `~`.

## Fehler-Handling & Telemetrie
- **Gezielte Exceptions:** differenziere `Timeout`, `ConnectionError`, `HTTPError` und zeige nutzerfreundliche Hinweise.
- **Rotierendes Logfile** (`logging.handlers.RotatingFileHandler`) plus „Debug“-Checkbox in der GUI.
- **Sanfte Abbrüche:** Netzwerk-Thread sauber stoppen, Buttons reaktivieren, Fokus zurück auf „Abrufen“.

## Performance & Etikette
- **Exponential Backoff** hast du oben; ergänze kurze **Jitter**-Komponente gegen Thundering Herd.
- **Minimale Parallelität** nur, wenn du Zusatzlinks folgst („Weitere Spieler…“). Sonst Single-Request belassen.
- **Cache invalidieren** bei Saison-/Rundenwechsel.

## Komfort-Features
- **Auto-Fetch beim Gruppenwechsel** (optional, per Checkbox).
- **Favoriten markieren** (Stern in der Gruppenliste; Favoriten zuerst im Dropdown).
- **Schnellstart-Profile**: mehrere Presets (z. B. „Vorrunde 25/26“, „Rückrunde 25/26“) in der Config.

## Tests
- **Parser-Tests mit HTML-Fixtures:** speichere eine echte `groupPools`-Seite und schreibe Pytest-Tests gegen `parse_group_pools()`.
- **HTTP-Mocks** mit `responses` oder `requests-mock` für Timeout/HTTP-500/429.
- **Snapshot-Tests** für Exportformate (CSV/Markdown/XLSX).

---

Wenn du magst, liefere ich dir eine inkrementelle Patch-Version mit: Retries+Cache, sortierbarer Treeview, XLSX-Export, und plattformneutralem Config-Pfad — kompakt integriert und ohne dein bestehendes Verhalten zu brechen.

### 23. Benutzer

ja bitte

### 24. Assistent

Hier ist die **inkrementelle Version** mit deinen gewünschten Verbesserungen – kompakt eingebaut und abwärtskompatibel:

- **HTTP-Robustheit:** Retries mit Exponential-Backoff  
- **Caching:** 30 Minuten Response-Cache (entlastet Server & macht die GUI „snappier“)  
- **Sortierbare Tabelle:** Klick auf Spaltenkopf sortiert auf/ab (Q-TTR numerisch)  
- **XLSX-Export:** sauber typisiert für Excel/BI  
- **Plattformneutrale Config:** `platformdirs` statt hartem `~`-Pfad

### Setup
```bash
pip install requests beautifulsoup4 requests-cache openpyxl platformdirs
```

### `ttr_gui.py`
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
click-TT Q-TTR Scraper (Weg 1, groupPools) – GUI

Add-ons:
- Robustes HTTP (Retries + Backoff)
- Response-Caching (30 Min)
- Sortierbare Vorschau-Tabelle
- XLSX-Export
- Plattformneutrale Config (platformdirs)
- Gruppen-Pulldown mit Konfig-Dialog (Label -> Group-ID, persistent)

Voreinstellungen:
- Base-URL: https://ttbw.click-tt.de
- Saison:    TTBW 2025/26   (ggf. Schreibweise an echte URL anpassen)
- Runde:     vorrunde
- Beispiel-Gruppe: Kreisliga C2 -> 494514
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote
from pathlib import Path
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache
from bs4 import BeautifulSoup
from openpyxl import Workbook
from platformdirs import PlatformDirs

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# -------------------------------
# Config (plattformneutral)
# -------------------------------

APP_NAME   = "ttrscraper"
APP_AUTHOR = "ttc"  # beliebig (Hersteller/Organisation)
_dirs = PlatformDirs(APP_NAME, APP_AUTHOR)
CONFIG_DIR  = Path(_dirs.user_config_path)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# -------------------------------
# HTTP: Session mit Retry + Cache
# -------------------------------

def make_session() -> requests.Session:
    # CachedSession: 30 min Cache, nützlich bei wiederholten Abrufen derselben Liga
    s = requests_cache.CachedSession(
        cache_name=str(CONFIG_DIR / "http_cache"),
        expire_after=1800,           # 30 Minuten
        allowable_methods=("GET",),  # nur GET cachen
        stale_if_error=True
    )
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"])
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update({
        "User-Agent": "ttr-gui/1.3 (+https://example.org/bot-info)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5"
    })
    return s

SESSION = make_session()

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (
        f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
        f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}"
    )

def fetch_html(url: str, timeout: int = 30) -> str:
    resp = SESSION.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")  # schneller/robuster (lxml)
    text = soup.get_text(" ", strip=True).lower()
    hints = ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
             "session abgelaufen", "access denied", "forbidden"]
    for h in hints:
        if h in text:
            return h
    if not soup.find("table"):
        return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict] = []

    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team:
            continue

        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))
        if not table:
            continue

        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            continue

        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)

        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr:
                continue

            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None

            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""

            extra = {}
            if len(cols) >= 4:
                extra["anmerkung"] = cols[3]
            if len(cols) >= 5:
                extra["status"] = cols[4]

            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}
            if item["name"] or item["qttr"] is not None:
                results.append(item)

    return results

# -------------------------------
# Export (JSON/CSV/MD/XLSX)
# -------------------------------

def export_xlsx(rows: List[Dict], path: str, sprache: str):
    headers_de = ["Team", "Rang", "Q-TTR", "Name", "Anmerkung", "Status"]
    headers_en = ["Team", "Slot", "Q-TTR", "Name", "Note", "Status"]
    headers = headers_de if sprache.lower().startswith("de") else headers_en

    wb = Workbook()
    ws = wb.active
    ws.title = "Q-TTR"
    ws.append(headers)
    for r in rows:
        ws.append([
            r.get("team", ""), r.get("rang", ""),
            r.get("qttr", ""), r.get("name", ""),
            r.get("anmerkung",""), r.get("status","")
        ])
    # optional: schmale Auto-Breite
    for col in ws.columns:
        maxlen = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(10, maxlen + 2), 40)
    wb.save(path)

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers_de = ["Team", "Rang", "Q-TTR", "Name", "Anmerkung", "Status"]
    headers_en = ["Team", "Slot", "Q-TTR", "Name", "Note", "Status"]
    headers = headers_de if sprache.lower().startswith("de") else headers_en

    def row_to_list(r: Dict) -> List:
        return [r.get("team",""), r.get("rang",""), r.get("qttr",""),
                r.get("name",""), r.get("anmerkung",""), r.get("status","")]

    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for r in rows:
                w.writerow(row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows:
                vals = row_to_list(r)
                f.write("| " + " | ".join("" if v is None else str(v) for v in vals) + " |\n")
    elif datenformat == "xlsx":
        export_xlsx(rows, path, sprache)
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        # Container
        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        for i in range(6): frm.columnconfigure(i, weight=1)

        # Config laden + Defaults
        cfg = load_config()
        self.groups: List[Dict[str,str]] = cfg.get("groups", [{"label": "Kreisliga C2", "id": "494514"}])

        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))
        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))
        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))
        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))
        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))
        self.var_group_label = tk.StringVar(value=default_label)
        self.var_group_id    = tk.StringVar(value=default_id)
        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))
        self.var_format  = tk.StringVar(value=cfg.get("format","json"))

        # --- Zeile: Base-URL
        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=5, sticky="ew", padx=6, pady=3)

        # --- Zeile: Saison / Runde
        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)

        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,
                                      values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        # --- Zeile: Gruppe (Dropdown) + ID-View
        r += 1
        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")
        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,
                                      values=self._group_labels(), state="readonly")
        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)

        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")
        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")
        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)

        # --- Zeile: Datenformat (inkl. XLSX)
        r += 1
        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,
                                       values=["json","csv","markdown","xlsx"], state="readonly")
        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)

        # --- Buttons
        r += 1
        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=6, sticky="ew", pady=(6,3))
        for i in range(6): btn_frame.columnconfigure(i, weight=1)

        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",       command=self.on_fetch);    self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")
        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",   command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")
        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",        command=self.on_clear);    self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")
        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",   command=self.on_settings); self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")
        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",     command=self.on_groups);   self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")
        self.btn_exit     = ttk.Button(btn_frame, text="Exit",          command=root.destroy);     self.btn_exit.grid(row=0, column=5, padx=4, sticky="ew")

        # --- Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau (klickbare Spaltenköpfe zum Sortieren)").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=12)
        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:
            self.tree.heading(col, text=text)
            self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        frm.rowconfigure(r-1, weight=0)  # status
        frm.rowconfigure(r,   weight=1)  # table

        self.rows: List[Dict] = []
        self._make_treeview_sortable(self.tree)
        self._sync_group_id_to_label()

    # -------------------- Helpers --------------------

    def _group_labels(self) -> List[str]:
        return [g.get("label","") for g in self.groups]

    def _group_map(self) -> Dict[str,str]:
        return {g.get("label",""): g.get("id","") for g in self.groups}

    def _sync_group_id_to_label(self):
        gid = self._group_map().get(self.var_group_label.get().strip(), "")
        self.var_group_id.set(gid)

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.rows = []; self.btn_export.config(state="disabled")

    # Treeview-Sortierung
    def _make_treeview_sortable(self, tree: ttk.Treeview):
        for col in tree["columns"]:
            tree.heading(col, text=tree.heading(col, "text"),
                         command=lambda c=col: self._sort_by(tree, c, False))

    def _sort_by(self, tree: ttk.Treeview, col: str, descending: bool):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        def _num(v):
            try:
                return float(str(v).replace(",", "."))
            except Exception:
                return None
        # numerisch sortieren, wenn möglich (insb. Q-TTR)
        if any(_num(v) is not None for v,_ in data):
            data.sort(key=lambda t: (_num(t[0]) is None, _num(t[0]) or 0.0))
        else:
            data.sort(key=lambda t: str(t[0]).lower())
        if descending: data.reverse()
        for idx, item in enumerate(data):
            tree.move(item[1], "", idx)
        tree.heading(col, command=lambda: self._sort_by(tree, col, not descending))

    # -------------------- Actions --------------------

    def on_group_selected(self, _evt=None):
        self._sync_group_id_to_label()

    def on_fetch(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return

        url = build_url(base, saison, runde, gid)
        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))
                return
            avgs = self._team_avgs(rows)
            self.root.after(0, lambda: self._update_rows(rows, avgs))
        except Exception as e:
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs: Dict[str, Optional[float]] = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),
                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False); self.btn_export.config(state="normal")

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return
        fmt = self.var_format.get(); sprache = self.var_sprache.get()
        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "xlsx": ".xlsx"}
        if fmt not in ext_map:
            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return
        path = filedialog.asksaveasfilename(
            title="Speichern unter",
            defaultextension=ext_map[fmt],
            filetypes=[("Excel", "*.xlsx"), ("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")]
        )
        if not path: return
        try:
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    def on_settings(self):
        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):
            try:
                self._save_current_config()
                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")

    def on_groups(self):
        # Dialog zum Verwalten der Gruppen (Label<->ID)
        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()
        dlg.geometry("560x380")
        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)
        # Tree
        cols = ("label","id")
        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)
        tree.heading("label", text="Bezeichnung")
        tree.heading("id",    text="Group-ID")
        tree.column("label", stretch=True, width=320)
        tree.column("id",    stretch=False, width=120)
        tree.pack(fill="both", expand=True, pady=(0,8))

        # Form
        form = ttk.Frame(container); form.pack(fill="x", pady=4)
        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")
        var_label = tk.StringVar()
        ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")
        var_id = tk.StringVar()
        ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)
        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))

        # Buttons
        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))
        def refresh_tree():
            for i in tree.get_children(): tree.delete(i)
            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))
        def select_from_tree(_evt=None):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values")
            var_label.set(vals[0]); var_id.set(vals[1])
        def add_or_update():
            label = var_label.get().strip()
            gid   = var_id.get().strip()
            if not label or not gid:
                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return
            if not gid.isdigit():
                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"):
                    return
            for g in self.groups:
                if g.get("label","") == label:
                    g["id"] = gid
                    break
            else:
                self.groups.append({"label": label, "id": gid})
            refresh_tree(); self._refresh_group_dropdown()
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values")
            label = vals[0]
            self.groups = [g for g in self.groups if g.get("label","") != label]
            refresh_tree(); self._refresh_group_dropdown()
        def save_and_close():
            if self.var_group_label.get() not in self._group_labels():
                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")
            self._sync_group_id_to_label()
            try:
                self._save_current_config()
                messagebox.showinfo("Gespeichert", "Gruppen gespeichert.")
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Gruppen nicht speichern:\n{e}")

        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)
        ttk.Button(btns, text="Schließen & Speichern", command=save_and_close).pack(side="right", padx=4)

        tree.bind("<<TreeviewSelect>>", select_from_tree)
        refresh_tree()

    def _refresh_group_dropdown(self):
        self.cmb_group.config(values=self._group_labels())
        if self.var_group_label.get() not in self._group_labels() and self._group_labels():
            self.var_group_label.set(self._group_labels()[0])
        self._sync_group_id_to_label()

    def _save_current_config(self):
        config = {
            "base": self.var_base.get(),
            "saison": self.var_saison.get(),
            "runde": self.var_runde.get(),
            "group_label": self.var_group_label.get(),
            "group": self.var_group_id.get(),
            "sprache": self.var_sprache.get(),
            "format": self.var_format.get(),
            "groups": self.groups,
        }
        save_config(config)

def main():
    root = tk.Tk()
    # optionales DPI-Scaling Windows
    try:
        if sys.platform.startswith("win"):
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass
    root.geometry("1000x600")
    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

Mini-Hinweise:
- **Cache-Hit**: In der Konsole von `requests-cache` wird nix angezeigt; wenn du magst, kannst du `SESSION.cache.clear()` einbauen oder den Cache durch Profilwechsel (andere Saison/Gruppe) umgehen.  
- **Sortieren**: Spaltenköpfe sind toggelbar; Q-TTR wird numerisch korrekt sortiert, leere Werte landen unten.  
- **XLSX**: Auto-Spaltenbreiten sind konservativ (10–40 Zeichen).  

Wenn du zusätzlich „Im Browser öffnen“, Auto-Fetch beim Gruppenwechsel oder ein zweites Tabellenblatt mit Team-Aggregationen im XLSX möchtest, packe ich das direkt dazu.

### 25. Benutzer

ja bitte

### 26. Assistent

Sauber! Hier ist die **erweiterte Version** mit den drei gewünschten Features:

- Button **„Im Browser öffnen“** (öffnet die aktuell berechnete groupPools-URL)  
- **Auto-Abruf beim Gruppenwechsel** (per Checkbox aktivierbar)  
- **XLSX-Export mit zweitem Blatt „Stats“** (Team-Mittel/Min/Max/Count + Top-10 der Liga)

> Abhängigkeiten (wie zuvor):  
> `pip install requests beautifulsoup4 requests-cache openpyxl platformdirs`

---

## `ttr_gui.py` (aktualisiert)
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
click-TT Q-TTR Scraper (Weg 1, groupPools) – GUI v1.4

Neu:
- Button „Im Browser öffnen“ (aktuelle URL)
- Auto-Abruf beim Gruppenwechsel (Checkbox)
- XLSX-Export mit 2. Blatt „Stats“ (Team-Aggregate + Top-10)

Bestehendes:
- Robustes HTTP (Retries + Cache)
- Sortierbare Tabelle
- Gruppen-Pulldown + Konfig-Dialog (Label->ID)
- Plattformneutrale Config (platformdirs)
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote
from pathlib import Path
import webbrowser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache
from bs4 import BeautifulSoup
from openpyxl import Workbook
from platformdirs import PlatformDirs

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# -------------------------------
# Config (plattformneutral)
# -------------------------------

APP_NAME, APP_AUTHOR = "ttrscraper", "ttc"
_dirs = PlatformDirs(APP_NAME, APP_AUTHOR)
CONFIG_DIR  = Path(_dirs.user_config_path); CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}

# -------------------------------
# HTTP: Session mit Retry + Cache
# -------------------------------

def make_session() -> requests.Session:
    s = requests_cache.CachedSession(
        cache_name=str(CONFIG_DIR / "http_cache"),
        expire_after=1800, allowable_methods=("GET",), stale_if_error=True
    )
    retry = Retry(total=3, backoff_factor=0.8,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET"]))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter); s.mount("http://", adapter)
    s.headers.update({
        "User-Agent": "ttr-gui/1.4 (+https://example.org/bot-info)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5"
    })
    return s

SESSION = make_session()

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
            f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}")

def fetch_html(url: str, timeout: int = 30) -> str:
    resp = SESSION.get(url, timeout=timeout); resp.raise_for_status(); return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    for h in ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
              "session abgelaufen", "access denied", "forbidden"]:
        if h in text: return h
    if not soup.find("table"): return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team: continue
        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))
        if not table: continue
        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            continue
        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)
        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr: continue
            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None
            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""
            extra = {}
            if len(cols) >= 4: extra["anmerkung"] = cols[3]
            if len(cols) >= 5: extra["status"] = cols[4]
            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}
            if item["name"] or item["qttr"] is not None: results.append(item)
    return results

# -------------------------------
# Export (JSON/CSV/MD/XLSX)
# -------------------------------

def _row_to_list(r: Dict) -> List:
    return [r.get("team",""), r.get("rang",""), r.get("qttr",""),
            r.get("name",""), r.get("anmerkung",""), r.get("status","")]

def _compute_team_stats(rows: List[Dict]) -> List[Dict]:
    stats = []
    teams = sorted({r["team"] for r in rows})
    for t in teams:
        vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
        if not vals:
            stats.append({"Team": t, "Anzahl": 0, "Ø Q-TTR": None, "Min": None, "Max": None})
        else:
            stats.append({"Team": t, "Anzahl": len(vals), "Ø Q-TTR": round(mean(vals), 1),
                          "Min": min(vals), "Max": max(vals)})
    return stats

def _top_n(rows: List[Dict], n: int = 10) -> List[Dict]:
    valids = [r for r in rows if isinstance(r.get("qttr"), int)]
    valids.sort(key=lambda r: r["qttr"], reverse=True)
    out = []
    for i, r in enumerate(valids[:n], 1):
        out.append({"#": i, "Name": r.get("name",""), "Team": r.get("team",""), "Q-TTR": r.get("qttr")})
    return out

def export_xlsx(rows: List[Dict], path: str, sprache: str):
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    wb = Workbook()
    ws = wb.active; ws.title = "Q-TTR"
    ws.append(headers)
    for r in rows: ws.append(_row_to_list(r))
    # Spaltenbreiten
    for col in ws.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(10, maxlen + 2), 40)

    # Blatt "Stats"
    ws2 = wb.create_sheet("Stats")
    # Team-Aggregate
    ws2.append(["Team","Anzahl","Ø Q-TTR","Min","Max"])
    for s in _compute_team_stats(rows):
        ws2.append([s["Team"], s["Anzahl"], s["Ø Q-TTR"], s["Min"], s["Max"]])
    # Leerzeile, dann Top-10
    ws2.append([])
    ws2.append(["Top-10 (Liga)"])
    ws2.append(["#","Name","Team","Q-TTR"])
    for t in _top_n(rows, 10):
        ws2.append([t["#"], t["Name"], t["Team"], t["Q-TTR"]])
    # Spaltenbreiten "Stats"
    for col in ws2.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws2.column_dimensions[col[0].column_letter].width = min(max(8, maxlen + 2), 40)

    wb.save(path)

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(headers)
            for r in rows: w.writerow(_row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows: f.write("| " + " | ".join("" if v is None else str(v) for v in _row_to_list(r)) + " |\n")
    elif datenformat == "xlsx":
        export_xlsx(rows, path, sprache)
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        # Container
        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        for i in range(6): frm.columnconfigure(i, weight=1)

        # Config laden + Defaults
        cfg = load_config()
        self.groups: List[Dict[str,str]] = cfg.get("groups", [{"label": "Kreisliga C2", "id": "494514"}])
        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))
        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))
        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))
        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))
        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))
        self.var_group_label = tk.StringVar(value=default_label)
        self.var_group_id    = tk.StringVar(value=default_id)
        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))
        self.var_format  = tk.StringVar(value=cfg.get("format","json"))
        self.var_autofetch = tk.BooleanVar(value=cfg.get("autofetch", False))

        # --- Zeile: Base-URL
        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=5, sticky="ew", padx=6, pady=3)

        # --- Zeile: Saison / Runde
        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)
        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,
                                      values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        # --- Zeile: Gruppe (Dropdown) + ID-View + Sprache
        r += 1
        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")
        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,
                                      values=self._group_labels(), state="readonly")
        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)

        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")
        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")
        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)

        # --- Zeile: Datenformat
        r += 1
        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,
                                       values=["json","csv","markdown","xlsx"], state="readonly")
        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)

        # --- Buttons (7 Spalten)
        r += 1
        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=6, sticky="ew", pady=(6,3))
        for i in range(7): btn_frame.columnconfigure(i, weight=1)

        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",           command=self.on_fetch);        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")
        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",       command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")
        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",            command=self.on_clear);        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")
        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",       command=self.on_settings);     self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")
        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",         command=self.on_groups);       self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")
        self.chk_autof    = ttk.Checkbutton(btn_frame, text="Auto-Abruf beim Gruppenwechsel", variable=self.var_autofetch)
        self.chk_autof.grid(row=0, column=5, padx=4, sticky="w")
        self.btn_browser  = ttk.Button(btn_frame, text="Im Browser öffnen", command=self.on_open_browser); self.btn_browser.grid(row=0, column=6, padx=4, sticky="ew")

        # --- Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau (Spaltenkopf klicken zum Sortieren)").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=12)
        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:
            self.tree.heading(col, text=text); self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        frm.rowconfigure(r-1, weight=0)  # status
        frm.rowconfigure(r,   weight=1)  # table

        self.rows: List[Dict] = []
        self._make_treeview_sortable(self.tree)
        self._sync_group_id_to_label()

    # -------------------- Helpers --------------------

    def _group_labels(self) -> List[str]: return [g.get("label","") for g in self.groups]
    def _group_map(self) -> Dict[str,str]: return {g.get("label",""): g.get("id","") for g in self.groups}
    def _sync_group_id_to_label(self):
        gid = self._group_map().get(self.var_group_label.get().strip(), "")
        self.var_group_id.set(gid)

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.rows = []; self.btn_export.config(state="disabled")

    # Sortierung
    def _make_treeview_sortable(self, tree: ttk.Treeview):
        for col in tree["columns"]:
            tree.heading(col, text=tree.heading(col, "text"),
                         command=lambda c=col: self._sort_by(tree, c, False))

    def _sort_by(self, tree: ttk.Treeview, col: str, descending: bool):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        def _num(v):
            try: return float(str(v).replace(",", "."))
            except Exception: return None
        if any(_num(v) is not None for v,_ in data):
            data.sort(key=lambda t: (_num(t[0]) is None, _num(t[0]) or 0.0))
        else:
            data.sort(key=lambda t: str(t[0]).lower())
        if descending: data.reverse()
        for idx, item in enumerate(data): tree.move(item[1], "", idx)
        tree.heading(col, command=lambda: self._sort_by(tree, col, not descending))

    # -------------------- Actions --------------------

    def on_group_selected(self, _evt=None):
        self._sync_group_id_to_label()
        # Auto-Abruf nur, wenn nicht gerade ein Abruf läuft
        if self.var_autofetch.get() and str(self.btn_fetch["state"]) != "disabled":
            self.root.after(80, self.on_fetch)

    def on_open_browser(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()
        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return
        url = build_url(base, saison, runde, gid)
        webbrowser.open(url)
        self.log(f"Im Browser geöffnet: {url}")

    def on_fetch(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return

        url = build_url(base, saison, runde, gid)
        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))
                return
            avgs = self._team_avgs(rows)
            self.root.after(0, lambda: self._update_rows(rows, avgs))
        except Exception as e:
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs: Dict[str, Optional[float]] = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),
                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False); self.btn_export.config(state="normal")

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return
        fmt = self.var_format.get(); sprache = self.var_sprache.get()
        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "xlsx": ".xlsx"}
        if fmt not in ext_map:
            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return
        path = filedialog.asksaveasfilename(
            title="Speichern unter",
            defaultextension=ext_map[fmt],
            filetypes=[("Excel","*.xlsx"), ("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")]
        )
        if not path: return
        try:
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    def on_settings(self):
        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):
            try:
                self._save_current_config()
                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")

    def on_groups(self):
        # Dialog zum Verwalten der Gruppen (Label<->ID)
        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()
        dlg.geometry("560x380")
        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)
        cols = ("label","id")
        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)
        tree.heading("label", text="Bezeichnung"); tree.heading("id", text="Group-ID")
        tree.column("label", stretch=True, width=320); tree.column("id", stretch=False, width=120)
        tree.pack(fill="both", expand=True, pady=(0,8))

        form = ttk.Frame(container); form.pack(fill="x", pady=4)
        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")
        var_label = tk.StringVar(); ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")
        var_id = tk.StringVar(); ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)
        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))

        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))
        def refresh_tree():
            for i in tree.get_children(): tree.delete(i)
            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))
        def select_from_tree(_evt=None):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values"); var_label.set(vals[0]); var_id.set(vals[1])
        def add_or_update():
            label = var_label.get().strip(); gid = var_id.get().strip()
            if not label or not gid:
                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return
            if not gid.isdigit():
                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"): return
            for g in self.groups:
                if g.get("label","") == label:
                    g["id"] = gid; break
            else:
                self.groups.append({"label": label, "id": gid})
            refresh_tree(); self._refresh_group_dropdown()
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            label = tree.item(sel[0], "values")[0]
            self.groups = [g for g in self.groups if g.get("label","") != label]
            refresh_tree(); self._refresh_group_dropdown()
        def save_and_close():
            if self.var_group_label.get() not in self._group_labels():
                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")
            self._sync_group_id_to_label()
            try:
                self._save_current_config()
                messagebox.showinfo("Gespeichert", "Gruppen gespeichert."); dlg.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Gruppen nicht speichern:\n{e}")

        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)
        ttk.Button(btns, text="Schließen & Speichern", command=save_and_close).pack(side="right", padx=4)

        tree.bind("<<TreeviewSelect>>", select_from_tree)
        refresh_tree()

    def _refresh_group_dropdown(self):
        self.cmb_group.config(values=self._group_labels())
        if self.var_group_label.get() not in self._group_labels() and self._group_labels():
            self.var_group_label.set(self._group_labels()[0])
        self._sync_group_id_to_label()

    def _save_current_config(self):
        config = {
            "base": self.var_base.get(),
            "saison": self.var_saison.get(),
            "runde": self.var_runde.get(),
            "group_label": self.var_group_label.get(),
            "group": self.var_group_id.get(),
            "sprache": self.var_sprache.get(),
            "format": self.var_format.get(),
            "groups": self.groups,
            "autofetch": bool(self.var_autofetch.get()),
        }
        save_config(config)

def main():
    root = tk.Tk()
    try:
        import ctypes, sys as _sys
        if _sys.platform.startswith("win"):
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass
    root.geometry("1100x620")
    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

---

### Was sich ändert (praktisch):
- **„Im Browser öffnen“** baut exakt die URL, die auch der Abruf nutzt – ideal zum visuellen Gegencheck.  
- **Auto-Abruf** feuert nach Auswahlwechsel (mit kleinem Delay) nur, wenn kein Abruf läuft.  
- **XLSX „Stats“**:  
  - Tabelle mit `Team | Anzahl | Ø Q-TTR | Min | Max`  
  - darunter `Top-10 (Liga)` mit Rang, Name, Team, Q-TTR.

Wenn du magst, erweitere ich die Stats noch um **Median** und **Perzentile** oder packe **Team-Mittel als zusätzliches Feld** in die Haupttabelle.

### 27. Benutzer

die einstellung der Gruppen id soll in einer seperaten datei gruppen gespeichert werden

### 28. Assistent

Hier ist die Version mit **getrennter Gruppen-Datei** – die Gruppen (Label ↔ Group-ID) werden **nicht mehr** in `config.json`, sondern separat in **`gruppen.json`** im plattformneutralen Config-Ordner gespeichert. Bestehende Einträge in `config.json` werden beim ersten Start **automatisch migriert**.

- Config-Pfad (Linux/macOS/Windows sauber): via `platformdirs`
- Neue Funktionen: `load_groups()`, `save_groups()`, Migration
- Der Gruppen-Dialog liest/schreibt nur noch `gruppen.json`
- `config.json` enthält weiterhin deine übrigen Settings (Base-URL, Saison, Runde, Auswahl etc.)

> Abhängigkeiten (unverändert):  
> `pip install requests beautifulsoup4 requests-cache openpyxl platformdirs`

---

## `ttr_gui.py`
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
click-TT Q-TTR Scraper (Weg 1, groupPools) – GUI v1.5

Neu:
- Gruppen werden in separater Datei gespeichert: gruppen.json
- Automatische Migration: vorhandene "groups" in config.json -> gruppen.json

Bereits vorhanden:
- Robustes HTTP (Retries + Cache)
- Sortierbare Tabelle
- XLSX-Export mit Blatt "Stats" (Team-Aggregate + Top-10)
- Gruppen-Pulldown + Konfig-Dialog (Label->ID)
- Plattformneutrale Config (platformdirs)
- "Im Browser öffnen" + optionaler Auto-Abruf beim Gruppenwechsel
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote
from pathlib import Path
import webbrowser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache
from bs4 import BeautifulSoup
from openpyxl import Workbook
from platformdirs import PlatformDirs

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# -------------------------------
# Config (plattformneutral)
# -------------------------------

APP_NAME, APP_AUTHOR = "ttrscraper", "ttc"
_dirs = PlatformDirs(APP_NAME, APP_AUTHOR)
CONFIG_DIR  = Path(_dirs.user_config_path); CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"
GROUPS_PATH = CONFIG_DIR / "gruppen.json"     # <-- separate Gruppen-Datei

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}

def save_groups(groups: List[Dict[str, str]]):
    # einfache Validierung + Sortierung nach Label
    cleaned = []
    seen = set()
    for g in groups:
        label = (g.get("label") or "").strip()
        gid   = (g.get("id") or "").strip()
        if not label or not gid:
            continue
        key = (label.lower(), gid)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"label": label, "id": gid})
    cleaned.sort(key=lambda x: x["label"].lower())
    GROUPS_PATH.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")

def load_groups(default: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    # 1) bevorzugt: gruppen.json
    if GROUPS_PATH.exists():
        try:
            data = json.loads(GROUPS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    # 2) Migration: aus config.json (falls dort noch gespeichert)
    cfg = load_config()
    if isinstance(cfg.get("groups"), list) and cfg["groups"]:
        save_groups(cfg["groups"])
        # Optional: alte Gruppen im Config-Inhalt ignorieren – wir speichern sie nicht mehr zurück.
        return cfg["groups"]
    # 3) Fallback-Default
    if default is None:
        default = [{"label": "Kreisliga C2", "id": "494514"}]
    save_groups(default)
    return default

# -------------------------------
# HTTP: Session mit Retry + Cache
# -------------------------------

def make_session() -> requests.Session:
    s = requests_cache.CachedSession(
        cache_name=str(CONFIG_DIR / "http_cache"),
        expire_after=1800, allowable_methods=("GET",), stale_if_error=True
    )
    retry = Retry(total=3, backoff_factor=0.8,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET"]))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter); s.mount("http://", adapter)
    s.headers.update({
        "User-Agent": "ttr-gui/1.5 (+https://example.org/bot-info)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5"
    })
    return s

SESSION = make_session()

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
            f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}")

def fetch_html(url: str, timeout: int = 30) -> str:
    resp = SESSION.get(url, timeout=timeout); resp.raise_for_status(); return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    for h in ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
              "session abgelaufen", "access denied", "forbidden"]:
        if h in text: return h
    if not soup.find("table"): return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team: continue
        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))
        if not table: continue
        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            continue
        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)
        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr: continue
            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None
            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""
            extra = {}
            if len(cols) >= 4: extra["anmerkung"] = cols[3]
            if len(cols) >= 5: extra["status"] = cols[4]
            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}
            if item["name"] or item["qttr"] is not None: results.append(item)
    return results

# -------------------------------
# Export (JSON/CSV/MD/XLSX)
# -------------------------------

def _row_to_list(r: Dict) -> List:
    return [r.get("team",""), r.get("rang",""), r.get("qttr",""),
            r.get("name",""), r.get("anmerkung",""), r.get("status","")]

def _compute_team_stats(rows: List[Dict]) -> List[Dict]:
    stats = []
    teams = sorted({r["team"] for r in rows})
    for t in teams:
        vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
        if not vals:
            stats.append({"Team": t, "Anzahl": 0, "Ø Q-TTR": None, "Min": None, "Max": None})
        else:
            stats.append({"Team": t, "Anzahl": len(vals), "Ø Q-TTR": round(mean(vals), 1),
                          "Min": min(vals), "Max": max(vals)})
    return stats

def _top_n(rows: List[Dict], n: int = 10) -> List[Dict]:
    valids = [r for r in rows if isinstance(r.get("qttr"), int)]
    valids.sort(key=lambda r: r["qttr"], reverse=True)
    out = []
    for i, r in enumerate(valids[:n], 1):
        out.append({"#": i, "Name": r.get("name",""), "Team": r.get("team",""), "Q-TTR": r.get("qttr")})
    return out

def export_xlsx(rows: List[Dict], path: str, sprache: str):
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active; ws.title = "Q-TTR"
    ws.append(headers)
    for r in rows: ws.append(_row_to_list(r))
    # Spaltenbreiten
    for col in ws.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(10, maxlen + 2), 40)

    # Blatt "Stats"
    ws2 = wb.create_sheet("Stats")
    ws2.append(["Team","Anzahl","Ø Q-TTR","Min","Max"])
    for s in _compute_team_stats(rows):
        ws2.append([s["Team"], s["Anzahl"], s["Ø Q-TTR"], s["Min"], s["Max"]])
    ws2.append([]); ws2.append(["Top-10 (Liga)"]); ws2.append(["#","Name","Team","Q-TTR"])
    for t in _top_n(rows, 10):
        ws2.append([t["#"], t["Name"], t["Team"], t["Q-TTR"]])
    for col in ws2.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws2.column_dimensions[col[0].column_letter].width = min(max(8, maxlen + 2), 40)
    wb.save(path)

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(headers)
            for r in rows: w.writerow(_row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows: f.write("| " + " | ".join("" if v is None else str(v) for v in _row_to_list(r)) + " |\n")
    elif datenformat == "xlsx":
        export_xlsx(rows, path, sprache)
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        # Container
        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        for i in range(6): frm.columnconfigure(i, weight=1)

        # Config laden + Defaults
        cfg = load_config()
        self.groups: List[Dict[str,str]] = load_groups()  # <-- separate Datei
        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))
        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))
        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))
        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))
        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))
        self.var_group_label = tk.StringVar(value=default_label)
        self.var_group_id    = tk.StringVar(value=default_id)
        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))
        self.var_format  = tk.StringVar(value=cfg.get("format","json"))
        self.var_autofetch = tk.BooleanVar(value=cfg.get("autofetch", False))

        # --- Zeile: Base-URL
        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=5, sticky="ew", padx=6, pady=3)

        # --- Zeile: Saison / Runde
        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)
        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,
                                      values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        # --- Zeile: Gruppe (Dropdown) + ID-View + Sprache
        r += 1
        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")
        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,
                                      values=self._group_labels(), state="readonly")
        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)

        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")
        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")
        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)

        # --- Zeile: Datenformat
        r += 1
        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,
                                       values=["json","csv","markdown","xlsx"], state="readonly")
        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)

        # --- Buttons
        r += 1
        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=6, sticky="ew", pady=(6,3))
        for i in range(7): btn_frame.columnconfigure(i, weight=1)

        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",           command=self.on_fetch);        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")
        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",       command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")
        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",            command=self.on_clear);        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")
        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",       command=self.on_settings);     self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")
        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",         command=self.on_groups);       self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")
        self.chk_autof    = ttk.Checkbutton(btn_frame, text="Auto-Abruf beim Gruppenwechsel", variable=self.var_autofetch)
        self.chk_autof.grid(row=0, column=5, padx=4, sticky="w")
        self.btn_browser  = ttk.Button(btn_frame, text="Im Browser öffnen", command=self.on_open_browser); self.btn_browser.grid(row=0, column=6, padx=4, sticky="ew")

        # --- Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau (Spaltenkopf klicken zum Sortieren)").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=12)
        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:
            self.tree.heading(col, text=text); self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=5, sticky="nsew", padx=6, pady=3)

        frm.rowconfigure(r-1, weight=0)  # status
        frm.rowconfigure(r,   weight=1)  # table

        self.rows: List[Dict] = []
        self._make_treeview_sortable(self.tree)
        self._sync_group_id_to_label()

    # -------------------- Helpers --------------------

    def _group_labels(self) -> List[str]: return [g.get("label","") for g in self.groups]
    def _group_map(self) -> Dict[str,str]: return {g.get("label",""): g.get("id","") for g in self.groups}
    def _sync_group_id_to_label(self):
        gid = self._group_map().get(self.var_group_label.get().strip(), "")
        self.var_group_id.set(gid)

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.rows = []; self.btn_export.config(state="disabled")

    # Sortierung
    def _make_treeview_sortable(self, tree: ttk.Treeview):
        for col in tree["columns"]:
            tree.heading(col, text=tree.heading(col, "text"),
                         command=lambda c=col: self._sort_by(tree, c, False))

    def _sort_by(self, tree: ttk.Treeview, col: str, descending: bool):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        def _num(v):
            try: return float(str(v).replace(",", "."))
            except Exception: return None
        if any(_num(v) is not None for v,_ in data):
            data.sort(key=lambda t: (_num(t[0]) is None, _num(t[0]) or 0.0))
        else:
            data.sort(key=lambda t: str(t[0]).lower())
        if descending: data.reverse()
        for idx, item in enumerate(data): tree.move(item[1], "", idx)
        tree.heading(col, command=lambda: self._sort_by(tree, col, not descending))

    # -------------------- Actions --------------------

    def on_group_selected(self, _evt=None):
        self._sync_group_id_to_label()
        if self.var_autofetch.get() and str(self.btn_fetch["state"]) != "disabled":
            self.root.after(80, self.on_fetch)

    def on_open_browser(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()
        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return
        url = build_url(base, saison, runde, gid)
        webbrowser.open(url)
        self.log(f"Im Browser geöffnet: {url}")

    def on_fetch(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return

        url = build_url(base, saison, runde, gid)
        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))
                return
            avgs = self._team_avgs(rows)
            self.root.after(0, lambda: self._update_rows(rows, avgs))
        except Exception as e:
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs: Dict[str, Optional[float]] = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),
                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False); self.btn_export.config(state="normal")

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return
        fmt = self.var_format.get(); sprache = self.var_sprache.get()
        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "xlsx": ".xlsx"}
        if fmt not in ext_map:
            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return
        path = filedialog.asksaveasfilename(
            title="Speichern unter",
            defaultextension=ext_map[fmt],
            filetypes=[("Excel","*.xlsx"), ("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")]
        )
        if not path: return
        try:
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    def on_settings(self):
        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):
            try:
                self._save_current_config()
                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")

    def on_groups(self):
        # Dialog zum Verwalten der Gruppen (Label<->ID) – persistiert in gruppen.json
        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()
        dlg.geometry("560x380")
        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)
        cols = ("label","id")
        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)
        tree.heading("label", text="Bezeichnung"); tree.heading("id", text="Group-ID")
        tree.column("label", stretch=True, width=320); tree.column("id", stretch=False, width=120)
        tree.pack(fill="both", expand=True, pady=(0,8))

        form = ttk.Frame(container); form.pack(fill="x", pady=4)
        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")
        var_label = tk.StringVar(); ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")
        var_id = tk.StringVar(); ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)
        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))

        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))
        def refresh_tree():
            for i in tree.get_children(): tree.delete(i)
            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))
        def select_from_tree(_evt=None):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values"); var_label.set(vals[0]); var_id.set(vals[1])
        def add_or_update():
            label = var_label.get().strip(); gid = var_id.get().strip()
            if not label or not gid:
                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return
            if not gid.isdigit():
                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"): return
            for g in self.groups:
                if g.get("label","") == label:
                    g["id"] = gid; break
            else:
                self.groups.append({"label": label, "id": gid})
            save_groups(self.groups)             # <-- direkt speichern
            refresh_tree(); self._refresh_group_dropdown()
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            label = tree.item(sel[0], "values")[0]
            self.groups = [g for g in self.groups if g.get("label","") != label]
            save_groups(self.groups)             # <-- direkt speichern
            refresh_tree(); self._refresh_group_dropdown()
        def close_dialog():
            # Auswahl synchronisieren + config (ohne groups) speichern
            if self.var_group_label.get() not in self._group_labels():
                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")
            self._sync_group_id_to_label()
            try:
                self._save_current_config()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Konfiguration nicht speichern:\n{e}")

        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)
        ttk.Button(btns, text="Schließen", command=close_dialog).pack(side="right", padx=4)

        tree.bind("<<TreeviewSelect>>", select_from_tree)
        refresh_tree()

    def _refresh_group_dropdown(self):
        self.cmb_group.config(values=self._group_labels())
        if self.var_group_label.get() not in self._group_labels() and self._group_labels():
            self.var_group_label.set(self._group_labels()[0])
        self._sync_group_id_to_label()

    def _save_current_config(self):
        # Gruppen werden NICHT mehr in config.json gespeichert
        config = {
            "base": self.var_base.get(),
            "saison": self.var_saison.get(),
            "runde": self.var_runde.get(),
            "group_label": self.var_group_label.get(),
            "group": self.var_group_id.get(),
            "sprache": self.var_sprache.get(),
            "format": self.var_format.get(),
            "autofetch": bool(self.var_autofetch.get()),
        }
        save_config(config)

def main():
    root = tk.Tk()
    try:
        import ctypes, sys as _sys
        if _sys.platform.startswith("win"):
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass
    root.geometry("1100x620")
    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

---

### Wo liegen die Dateien?
- **Config-Ordner:** `platformdirs` legt ihn systemgerecht an. Beispiele:  
  - Windows: `C:\Users\<Du>\AppData\Local\ttrscraper\ttrscraper\`  
  - macOS: `~/Library/Application Support/ttrscraper/`  
  - Linux: `~/.config/ttrscraper/`
- **`config.json`**: übrige Einstellungen (Base-URL, Saison, Runde, Auswahl, Format, Autofetch …)  
- **`gruppen.json`**: Liste aus Objekten `{"label": "<Bezeichnung>", "id": "<Group-ID>"}`

Wenn du lieber einen **frei wählbaren Speicherort** für `gruppen.json` hättest (z. B. in einem geteilten Netzordner), baue ich dir einen Datei-Picker in den Gruppen-Dialog ein und merke mir den Pfad in `config.json`.

### 29. Benutzer

ja bitte

### 30. Assistent

Hier ist die Version mit **frei wählbarem Speicherort für `gruppen.json`** – direkt über den **Gruppen-Dialog** setzbar und in der `config.json` gemerkt. Wenn am neuen Ort bereits eine `gruppen.json` liegt, wird sie geladen; sonst werden deine aktuellen Gruppen dorthin geschrieben.

- Neuer Config-Key: `groups_path`
- `gruppen.json` wird **nur** dort gelesen/geschrieben
- Migration von alten Gruppen aus `config.json` bleibt erhalten

> Abhängigkeiten (wie gehabt):  
> `pip install requests beautifulsoup4 requests-cache openpyxl platformdirs`

---

## `ttr_gui.py` (v1.6)
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
click-TT Q-TTR Scraper (Weg 1, groupPools) – GUI v1.6

Neu:
- Frei wählbarer Speicherort für gruppen.json (im Gruppen-Dialog)
- Pfad wird in config.json als "groups_path" gemerkt
- Wenn am neuen Pfad bereits gruppen.json existiert: laden; sonst aktuelle Gruppen dorthin speichern

Bestehendes:
- Robustes HTTP (Retries + Cache)
- Sortierbare Tabelle
- XLSX-Export mit Blatt "Stats" (Team-Aggregate + Top-10)
- Gruppen-Pulldown + Konfig-Dialog (Label->ID)
- Plattformneutrale Config (platformdirs)
- "Im Browser öffnen" + optionaler Auto-Abruf beim Gruppenwechsel
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote
from pathlib import Path
import webbrowser
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache
from bs4 import BeautifulSoup
from openpyxl import Workbook
from platformdirs import PlatformDirs

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# -------------------------------
# Config (plattformneutral)
# -------------------------------

APP_NAME, APP_AUTHOR = "ttrscraper", "ttc"
_dirs = PlatformDirs(APP_NAME, APP_AUTHOR)
CONFIG_DIR  = Path(_dirs.user_config_path); CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"
# Hinweis: Standard-Ort der Gruppen-Datei, falls kein Pfad in config.json gesetzt:
DEFAULT_GROUPS_PATH = CONFIG_DIR / "gruppen.json"

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _normalize_path(p: str) -> Path:
    # ~ und relative Pfade robust behandeln, Ordner nicht voraussetzen
    return Path(os.path.expanduser(p)).absolute()

def get_groups_path_from_config(cfg: Optional[dict] = None) -> Path:
    if cfg is None:
        cfg = load_config()
    p = cfg.get("groups_path")
    if p:
        try:
            return _normalize_path(p)
        except Exception:
            return DEFAULT_GROUPS_PATH
    return DEFAULT_GROUPS_PATH

def save_groups(groups: List[Dict[str, str]], path: Optional[Path] = None):
    if path is None:
        path = get_groups_path_from_config()
    # einfache Validierung + Sortierung
    cleaned = []
    seen = set()
    for g in groups:
        label = (g.get("label") or "").strip()
        gid   = (g.get("id") or "").strip()
        if not label or not gid:
            continue
        key = (label.lower(), gid)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"label": label, "id": gid})
    cleaned.sort(key=lambda x: x["label"].lower())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")

def load_groups(default: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    # 1) bevorzugter Pfad aus config.json
    cfg = load_config()
    groups_path = get_groups_path_from_config(cfg)
    if groups_path.exists():
        try:
            data = json.loads(groups_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    # 2) Migration: alte "groups" aus config.json
    if isinstance(cfg.get("groups"), list) and cfg["groups"]:
        save_groups(cfg["groups"], groups_path)
        return cfg["groups"]
    # 3) Fallback-Default
    if default is None:
        default = [{"label": "Kreisliga C2", "id": "494514"}]
    save_groups(default, groups_path)
    return default

# -------------------------------
# HTTP: Session mit Retry + Cache
# -------------------------------

def make_session() -> requests.Session:
    s = requests_cache.CachedSession(
        cache_name=str(CONFIG_DIR / "http_cache"),
        expire_after=1800, allowable_methods=("GET",), stale_if_error=True
    )
    retry = Retry(total=3, backoff_factor=0.8,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET"]))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter); s.mount("http://", adapter)
    s.headers.update({
        "User-Agent": "ttr-gui/1.6 (+https://example.org/bot-info)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5"
    })
    return s

SESSION = make_session()

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
            f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}")

def fetch_html(url: str, timeout: int = 30) -> str:
    resp = SESSION.get(url, timeout=timeout); resp.raise_for_status(); return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    for h in ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
              "session abgelaufen", "access denied", "forbidden"]:
        if h in text: return h
    if not soup.find("table"): return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team: continue
        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))
        if not table: continue
        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            continue
        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)
        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr: continue
            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None
            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""
            extra = {}
            if len(cols) >= 4: extra["anmerkung"] = cols[3]
            if len(cols) >= 5: extra["status"] = cols[4]
            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}
            if item["name"] or item["qttr"] is not None: results.append(item)
    return results

# -------------------------------
# Export (JSON/CSV/MD/XLSX)
# -------------------------------

def _row_to_list(r: Dict) -> List:
    return [r.get("team",""), r.get("rang",""), r.get("qttr",""),
            r.get("name",""), r.get("anmerkung",""), r.get("status","")]

def _compute_team_stats(rows: List[Dict]) -> List[Dict]:
    stats = []
    teams = sorted({r["team"] for r in rows})
    for t in teams:
        vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
        if not vals:
            stats.append({"Team": t, "Anzahl": 0, "Ø Q-TTR": None, "Min": None, "Max": None})
        else:
            stats.append({"Team": t, "Anzahl": len(vals), "Ø Q-TTR": round(mean(vals), 1),
                          "Min": min(vals), "Max": max(vals)})
    return stats

def _top_n(rows: List[Dict], n: int = 10) -> List[Dict]:
    valids = [r for r in rows if isinstance(r.get("qttr"), int)]
    valids.sort(key=lambda r: r["qttr"], reverse=True)
    out = []
    for i, r in enumerate(valids[:n], 1):
        out.append({"#": i, "Name": r.get("name",""), "Team": r.get("team",""), "Q-TTR": r.get("qttr")})
    return out

def export_xlsx(rows: List[Dict], path: str, sprache: str):
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    wb = Workbook()
    ws = wb.active; ws.title = "Q-TTR"
    ws.append(headers)
    for r in rows: ws.append(_row_to_list(r))
    # Spaltenbreiten
    for col in ws.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(10, maxlen + 2), 40)

    # Blatt "Stats"
    ws2 = wb.create_sheet("Stats")
    ws2.append(["Team","Anzahl","Ø Q-TTR","Min","Max"])
    for s in _compute_team_stats(rows):
        ws2.append([s["Team"], s["Anzahl"], s["Ø Q-TTR"], s["Min"], s["Max"]])
    ws2.append([]); ws2.append(["Top-10 (Liga)"]); ws2.append(["#","Name","Team","Q-TTR"])
    for t in _top_n(rows, 10):
        ws2.append([t["#"], t["Name"], t["Team"], t["Q-TTR"]])
    for col in ws2.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws2.column_dimensions[col[0].column_letter].width = min(max(8, maxlen + 2), 40)
    wb.save(path)

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(headers)
            for r in rows: w.writerow(_row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows: f.write("| " + " | ".join("" if v is None else str(v) for v in _row_to_list(r)) + " |\n")
    elif datenformat == "xlsx":
        export_xlsx(rows, path, sprache)
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        # Container
        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        for i in range(7): frm.columnconfigure(i, weight=1)

        # Config laden + Defaults
        cfg = load_config()
        self.groups: List[Dict[str,str]] = load_groups()  # separate Datei
        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))
        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))
        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))
        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))
        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))
        self.var_group_label = tk.StringVar(value=default_label)
        self.var_group_id    = tk.StringVar(value=default_id)
        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))
        self.var_format  = tk.StringVar(value=cfg.get("format","json"))
        self.var_autofetch = tk.BooleanVar(value=cfg.get("autofetch", False))
        self.groups_path = get_groups_path_from_config(cfg)  # Path-Objekt

        # --- Zeile: Base-URL
        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=6, sticky="ew", padx=6, pady=3)

        # --- Zeile: Saison / Runde
        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)
        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,
                                      values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        # --- Zeile: Gruppe (Dropdown) + ID-View + Sprache
        r += 1
        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")
        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,
                                      values=self._group_labels(), state="readonly")
        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)

        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")
        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")
        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)

        # --- Zeile: Datenformat
        r += 1
        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,
                                       values=["json","csv","markdown","xlsx"], state="readonly")
        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)

        # --- Buttons
        r += 1
        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=7, sticky="ew", pady=(6,3))
        for i in range(8): btn_frame.columnconfigure(i, weight=1)

        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",           command=self.on_fetch);        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")
        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",       command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")
        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",            command=self.on_clear);        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")
        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",       command=self.on_settings);     self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")
        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",         command=self.on_groups);       self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")
        self.chk_autof    = ttk.Checkbutton(btn_frame, text="Auto-Abruf beim Gruppenwechsel", variable=self.var_autofetch)
        self.chk_autof.grid(row=0, column=5, padx=4, sticky="w")
        self.btn_browser  = ttk.Button(btn_frame, text="Im Browser öffnen", command=self.on_open_browser); self.btn_browser.grid(row=0, column=6, padx=4, sticky="ew")
        # Anzeige des Gruppen-Pfads + Button
        self.lbl_gpath    = ttk.Label(btn_frame, text=f"Gruppen-Datei: {self.groups_path}")
        self.lbl_gpath.grid(row=0, column=7, padx=6, sticky="w")

        r += 1
        path_frame = ttk.Frame(frm); path_frame.grid(row=r, column=0, columnspan=7, sticky="ew", pady=(0,6))
        for i in range(2): path_frame.columnconfigure(i, weight=(0 if i==0 else 1))
        ttk.Button(path_frame, text="Speicherort für Gruppen …", command=self.on_pick_groups_path).grid(row=0, column=0, padx=4, sticky="w")
        ttk.Label(path_frame, text="(wird in config.json als groups_path gespeichert)").grid(row=0, column=1, sticky="w")

        # --- Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=6, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau (Spaltenkopf klicken zum Sortieren)").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=12)
        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:
            self.tree.heading(col, text=text); self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=6, sticky="nsew", padx=6, pady=3)

        frm.rowconfigure(r-1, weight=0)  # status
        frm.rowconfigure(r,   weight=1)  # table

        self.rows: List[Dict] = []
        self._make_treeview_sortable(self.tree)
        self._sync_group_id_to_label()

    # -------------------- Helpers --------------------

    def _group_labels(self) -> List[str]: return [g.get("label","") for g in self.groups]
    def _group_map(self) -> Dict[str,str]: return {g.get("label",""): g.get("id","") for g in self.groups}
    def _sync_group_id_to_label(self):
        gid = self._group_map().get(self.var_group_label.get().strip(), "")
        self.var_group_id.set(gid)

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.rows = []; self.btn_export.config(state="disabled")

    # Sortierung
    def _make_treeview_sortable(self, tree: ttk.Treeview):
        for col in tree["columns"]:
            tree.heading(col, text=tree.heading(col, "text"),
                         command=lambda c=col: self._sort_by(tree, c, False))

    def _sort_by(self, tree: ttk.Treeview, col: str, descending: bool):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        def _num(v):
            try: return float(str(v).replace(",", "."))
            except Exception: return None
        if any(_num(v) is not None for v,_ in data):
            data.sort(key=lambda t: (_num(t[0]) is None, _num(t[0]) or 0.0))
        else:
            data.sort(key=lambda t: str(t[0]).lower())
        if descending: data.reverse()
        for idx, item in enumerate(data): tree.move(item[1], "", idx)
        tree.heading(col, command=lambda: self._sort_by(tree, col, not descending))

    # -------------------- Actions --------------------

    def on_group_selected(self, _evt=None):
        self._sync_group_id_to_label()
        if self.var_autofetch.get() and str(self.btn_fetch["state"]) != "disabled":
            self.root.after(80, self.on_fetch)

    def on_open_browser(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()
        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return
        url = build_url(base, saison, runde, gid)
        webbrowser.open(url)
        self.log(f"Im Browser geöffnet: {url}")

    def on_fetch(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return

        url = build_url(base, saison, runde, gid)
        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))
                return
            avgs = self._team_avgs(rows)
            self.root.after(0, lambda: self._update_rows(rows, avgs))
        except Exception as e:
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs: Dict[str, Optional[float]] = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),
                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False); self.btn_export.config(state="normal")

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return
        fmt = self.var_format.get(); sprache = self.var_sprache.get()
        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "xlsx": ".xlsx"}
        if fmt not in ext_map:
            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return
        path = filedialog.asksaveasfilename(
            title="Speichern unter",
            defaultextension=ext_map[fmt],
            filetypes=[("Excel","*.xlsx"), ("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")]
        )
        if not path: return
        try:
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    def on_settings(self):
        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):
            try:
                self._save_current_config()
                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")

    def on_groups(self):
        # Dialog zum Verwalten der Gruppen (Label<->ID) – persistiert in frei wählbarer gruppen.json
        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()
        dlg.geometry("620x420")
        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)
        cols = ("label","id")
        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)
        tree.heading("label", text="Bezeichnung"); tree.heading("id", text="Group-ID")
        tree.column("label", stretch=True, width=360); tree.column("id", stretch=False, width=140)
        tree.pack(fill="both", expand=True, pady=(0,8))

        # Pfadanzeige + Button im Dialog
        path_frame = ttk.Frame(container); path_frame.pack(fill="x", pady=(0,8))
        lbl = ttk.Label(path_frame, text=f"Datei: {self.groups_path}")
        lbl.pack(side="left", padx=(0,6))
        def pick_path():
            # Standard: aktuelles Verzeichnis der bestehenden Datei (oder Config-Ordner)
            initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)
            initial_file = self.groups_path.name if self.groups_path else "gruppen.json"
            chosen = filedialog.asksaveasfilename(
                title="Speicherort für gruppen.json wählen",
                initialdir=initial_dir,
                initialfile=initial_file,
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]
            )
            if not chosen:
                return
            new_path = _normalize_path(chosen)
            # Wenn Datei existiert und gültig -> laden, sonst aktuelle Gruppen dorthin speichern
            try:
                if Path(new_path).exists():
                    data = json.loads(Path(new_path).read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        self.groups = data
                else:
                    save_groups(self.groups, new_path)
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")
                return
            # Pfad übernehmen und in config.json merken
            self.groups_path = new_path
            cfg = load_config(); cfg["groups_path"] = str(new_path)
            save_config(cfg)
            # UI aktualisieren
            lbl.config(text=f"Datei: {self.groups_path}")
            self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")
            refresh_tree(); self._refresh_group_dropdown()

        ttk.Button(path_frame, text="Speicherort wählen …", command=pick_path).pack(side="left")

        # Formular
        form = ttk.Frame(container); form.pack(fill="x", pady=4)
        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")
        var_label = tk.StringVar(); ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")
        var_id = tk.StringVar(); ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)
        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))

        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))
        def refresh_tree():
            for i in tree.get_children(): tree.delete(i)
            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))
        def select_from_tree(_evt=None):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values"); var_label.set(vals[0]); var_id.set(vals[1])
        def add_or_update():
            label = var_label.get().strip(); gid = var_id.get().strip()
            if not label or not gid:
                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return
            if not gid.isdigit():
                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"): return
            for g in self.groups:
                if g.get("label","") == label:
                    g["id"] = gid; break
            else:
                self.groups.append({"label": label, "id": gid})
            save_groups(self.groups, self.groups_path)
            refresh_tree(); self._refresh_group_dropdown()
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            label = tree.item(sel[0], "values")[0]
            self.groups = [g for g in self.groups if g.get("label","") != label]
            save_groups(self.groups, self.groups_path)
            refresh_tree(); self._refresh_group_dropdown()
        def close_dialog():
            if self.var_group_label.get() not in self._group_labels():
                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")
            self._sync_group_id_to_label()
            try:
                self._save_current_config()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Konfiguration nicht speichern:\n{e}")

        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)
        ttk.Button(btns, text="Schließen", command=close_dialog).pack(side="right", padx=4)

        tree.bind("<<TreeviewSelect>>", select_from_tree)
        refresh_tree()

    def _refresh_group_dropdown(self):
        self.cmb_group.config(values=self._group_labels())
        if self.var_group_label.get() not in self._group_labels() and self._group_labels():
            self.var_group_label.set(self._group_labels()[0])
        self._sync_group_id_to_label()

    def _save_current_config(self):
        config = load_config()
        # bestehenden groups_path beibehalten
        config.update({
            "base": self.var_base.get(),
            "saison": self.var_saison.get(),
            "runde": self.var_runde.get(),
            "group_label": self.var_group_label.get(),
            "group": self.var_group_id.get(),
            "sprache": self.var_sprache.get(),
            "format": self.var_format.get(),
            "autofetch": bool(self.var_autofetch.get()),
            "groups_path": str(self.groups_path),
        })
        save_config(config)

def main():
    root = tk.Tk()
    try:
        import ctypes, sys as _sys
        if _sys.platform.startswith("win"):
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass
    root.geometry("1120x640")
    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

---

Kurz zur Nutzung:
- Öffne **Gruppen …** → Button **„Speicherort wählen …“** → Zielpfad für `gruppen.json` wählen.  
- Liegt dort schon eine Datei, wird sie geladen; sonst werden deine aktuellen Gruppen dorthin gespeichert.  
- Der Pfad steht in der Statuszeile und wird in `config.json` unter `groups_path` gemerkt.

### 31. Benutzer

neuer code: #!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

click-TT Q-TTR Scraper (Weg 1, groupPools) – GUI v1.6



Neu:

- Frei wählbarer Speicherort für gruppen.json (im Gruppen-Dialog)

- Pfad wird in config.json als "groups_path" gemerkt

- Wenn am neuen Pfad bereits gruppen.json existiert: laden; sonst aktuelle Gruppen dorthin speichern



Bestehendes:

- Robustes HTTP (Retries + Cache)

- Sortierbare Tabelle

- XLSX-Export mit Blatt "Stats" (Team-Aggregate + Top-10)

- Gruppen-Pulldown + Konfig-Dialog (Label->ID)

- Plattformneutrale Config (platformdirs)

- "Im Browser öffnen" + optionaler Auto-Abruf beim Gruppenwechsel

"""



import csv

import json

import re

import sys

import threading

from statistics import mean

from typing import Dict, List, Optional

from urllib.parse import quote

from pathlib import Path

import webbrowser

import os



import requests

from requests.adapters import HTTPAdapter

from urllib3.util.retry import Retry

import requests_cache

from bs4 import BeautifulSoup

from openpyxl import Workbook

from platformdirs import PlatformDirs



import tkinter as tk

from tkinter import ttk, messagebox, filedialog



# -------------------------------

# Config (plattformneutral)

# -------------------------------



APP_NAME, APP_AUTHOR = "ttrscraper", "ttc"

_dirs = PlatformDirs(APP_NAME, APP_AUTHOR)

CONFIG_DIR  = Path(_dirs.user_config_path); CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = CONFIG_DIR / "config.json"

# Hinweis: Standard-Ort der Gruppen-Datei, falls kein Pfad in config.json gesetzt:

DEFAULT_GROUPS_PATH = CONFIG_DIR / "gruppen.json"



def save_config(config: dict):

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")



def load_config() -> dict:

    if CONFIG_PATH.exists():

        try:

            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

        except Exception:

            pass

    return {}



def _normalize_path(p: str) -> Path:

    # ~ und relative Pfade robust behandeln, Ordner nicht voraussetzen

    return Path(os.path.expanduser(p)).absolute()



def get_groups_path_from_config(cfg: Optional[dict] = None) -> Path:

    if cfg is None:

        cfg = load_config()

    p = cfg.get("groups_path")

    if p:

        try:

            return _normalize_path(p)

        except Exception:

            return DEFAULT_GROUPS_PATH

    return DEFAULT_GROUPS_PATH



def save_groups(groups: List[Dict[str, str]], path: Optional[Path] = None):

    if path is None:

        path = get_groups_path_from_config()

    # einfache Validierung + Sortierung

    cleaned = []

    seen = set()

    for g in groups:

        label = (g.get("label") or "").strip()

        gid   = (g.get("id") or "").strip()

        if not label or not gid:

            continue

        key = (label.lower(), gid)

        if key in seen:

            continue

        seen.add(key)

        cleaned.append({"label": label, "id": gid})

    cleaned.sort(key=lambda x: x["label"].lower())

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")



def load_groups(default: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:

    cfg = load_config()

    groups_path = get_groups_path_from_config(cfg)

    if groups_path.exists():

        try:

            data = json.loads(groups_path.read_text(encoding="utf-8"))

            if isinstance(data, list):

                return data

        except Exception:

            pass

    # Migration oder Default wie gehabt...

    if isinstance(cfg.get("groups"), list) and cfg["groups"]:

        save_groups(cfg["groups"], groups_path)

        return cfg["groups"]

    if default is None:

        default = [{"label": "Kreisliga C2", "id": "494514"}]

    save_groups(default, groups_path)

    return default



# -------------------------------

# HTTP: Session mit Retry + Cache

# -------------------------------



def make_session() -> requests.Session:

    s = requests_cache.CachedSession(

        cache_name=str(CONFIG_DIR / "http_cache"),

        expire_after=1800, allowable_methods=("GET",), stale_if_error=True

    )

    retry = Retry(total=3, backoff_factor=0.8,

                  status_forcelist=(429, 500, 502, 503, 504),

                  allowed_methods=frozenset(["GET"]))

    adapter = HTTPAdapter(max_retries=retry)

    s.mount("https://", adapter); s.mount("http://", adapter)

    s.headers.update({

        "User-Agent": "ttr-gui/1.6 (+https://example.org/bot-info)",

        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5"

    })

    return s



SESSION = make_session()



# -------------------------------

# Scraping-Logik (Weg 1)

# -------------------------------



def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:

    base = base_url.rstrip("/")

    return (f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"

            f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}")



def fetch_html(url: str, timeout: int = 30) -> str:

    resp = SESSION.get(url, timeout=timeout); resp.raise_for_status(); return resp.text



def looks_like_login_or_error(html: str) -> Optional[str]:

    soup = BeautifulSoup(html, "lxml")

    text = soup.get_text(" ", strip=True).lower()

    for h in ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",

              "session abgelaufen", "access denied", "forbidden"]:

        if h in text: return h

    if not soup.find("table"): return "keine tabellen gefunden"

    return None



def parse_group_pools(html: str) -> List[Dict]:

    soup = BeautifulSoup(html, "lxml")

    results: List[Dict] = []

    for heading in soup.find_all(["h2", "h3", "h4"]):

        team = heading.get_text(strip=True)

        if not team: continue

        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))

        if not table: continue

        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]

        try:

            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)

        except StopIteration:

            continue

        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)

        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)

        for row in table.select("tbody tr"):

            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]

            if not cols or len(cols) <= idx_qttr: continue

            qttr_raw = cols[idx_qttr]

            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)

            qttr_val = int(qttr_num) if qttr_num.isdigit() else None

            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""

            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""

            extra = {}

            if len(cols) >= 4: extra["anmerkung"] = cols[3]

            if len(cols) >= 5: extra["status"] = cols[4]

            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}

            if item["name"] or item["qttr"] is not None: results.append(item)

    return results



# -------------------------------

# Export (JSON/CSV/MD/XLSX)

# -------------------------------



def _row_to_list(r: Dict) -> List:

    return [r.get("team",""), r.get("rang",""), r.get("qttr",""),

            r.get("name",""), r.get("anmerkung",""), r.get("status","")]



def _compute_team_stats(rows: List[Dict]) -> List[Dict]:

    stats = []

    teams = sorted({r["team"] for r in rows})

    for t in teams:

        vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]

        if not vals:

            stats.append({"Team": t, "Anzahl": 0, "Ø Q-TTR": None, "Min": None, "Max": None})

        else:

            stats.append({"Team": t, "Anzahl": len(vals), "Ø Q-TTR": round(mean(vals), 1),

                          "Min": min(vals), "Max": max(vals)})

    return stats



def _top_n(rows: List[Dict], n: int = 10) -> List[Dict]:

    valids = [r for r in rows if isinstance(r.get("qttr"), int)]

    valids.sort(key=lambda r: r["qttr"], reverse=True)

    out = []

    for i, r in enumerate(valids[:n], 1):

        out.append({"#": i, "Name": r.get("name",""), "Team": r.get("team",""), "Q-TTR": r.get("qttr")})

    return out



def export_xlsx(rows: List[Dict], path: str, sprache: str):

    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \

              else ["Team","Slot","Q-TTR","Name","Note","Status"]



    wb = Workbook()

    ws = wb.active; ws.title = "Q-TTR"

    ws.append(headers)

    for r in rows: ws.append(_row_to_list(r))

    # Spaltenbreiten

    for col in ws.columns:

        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)

        ws.column_dimensions[col[0].column_letter].width = min(max(10, maxlen + 2), 40)



    # Blatt "Stats"

    ws2 = wb.create_sheet("Stats")

    ws2.append(["Team","Anzahl","Ø Q-TTR","Min","Max"])

    for s in _compute_team_stats(rows):

        ws2.append([s["Team"], s["Anzahl"], s["Ø Q-TTR"], s["Min"], s["Max"]])

    ws2.append([]); ws2.append(["Top-10 (Liga)"]); ws2.append(["#","Name","Team","Q-TTR"])

    for t in _top_n(rows, 10):

        ws2.append([t["#"], t["Name"], t["Team"], t["Q-TTR"]])

    for col in ws2.columns:

        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)

        ws2.column_dimensions[col[0].column_letter].width = min(max(8, maxlen + 2), 40)

    wb.save(path)



def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:

    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \

              else ["Team","Slot","Q-TTR","Name","Note","Status"]



    if datenformat == "json":

        with open(path, "w", encoding="utf-8") as f:

            json.dump(rows, f, ensure_ascii=False, indent=2)

    elif datenformat == "csv":

        with open(path, "w", encoding="utf-8-sig", newline="") as f:

            w = csv.writer(f); w.writerow(headers)

            for r in rows: w.writerow(_row_to_list(r))

    elif datenformat == "markdown":

        with open(path, "w", encoding="utf-8") as f:

            f.write("| " + " | ".join(headers) + " |\n")

            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")

            for r in rows: f.write("| " + " | ".join("" if v is None else str(v) for v in _row_to_list(r)) + " |\n")

    elif datenformat == "xlsx":

        export_xlsx(rows, path, sprache)

    else:

        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")



# -------------------------------

# GUI

# -------------------------------



class TTRScraperGUI:

    def __init__(self, root: tk.Tk):

        self.root = root

        root.title("click-TT Q-TTR Scraper (Weg 1)")



        # Container

        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")

        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)

        for i in range(7): frm.columnconfigure(i, weight=1)



        # Config laden + Defaults

        cfg = load_config()

        self.groups: List[Dict[str,str]] = load_groups()  # separate Datei

        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))

        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))

        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))

        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))

        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))

        self.var_group_label = tk.StringVar(value=default_label)

        self.var_group_id    = tk.StringVar(value=default_id)

        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))

        self.var_format  = tk.StringVar(value=cfg.get("format","json"))

        self.var_autofetch = tk.BooleanVar(value=cfg.get("autofetch", False))

        self.groups_path = get_groups_path_from_config(cfg)  # Path-Objekt



        # --- Zeile: Base-URL

        r = 0

        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")

        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=6, sticky="ew", padx=6, pady=3)



        # --- Zeile: Saison / Runde

        r += 1

        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")

        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)

        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")

        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,

                                      values=["vorrunde", "rueckrunde"], state="readonly")

        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)



        # --- Zeile: Gruppe (Dropdown) + ID-View + Sprache

        r += 1

        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")

        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,

                                      values=self._group_labels(), state="readonly")

        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)

        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)



        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")

        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")

        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)



        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")

        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")

        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)



        # --- Zeile: Datenformat

        r += 1

        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")

        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,

                                       values=["json","csv","markdown","xlsx"], state="readonly")

        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)



        # --- Buttons

        r += 1

        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=7, sticky="ew", pady=(6,3))

        for i in range(8): btn_frame.columnconfigure(i, weight=1)



        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",           command=self.on_fetch);        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")

        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",       command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")

        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",            command=self.on_clear);        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")

        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",       command=self.on_settings);     self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")

        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",         command=self.on_groups);       self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")

        self.chk_autof    = ttk.Checkbutton(btn_frame, text="Auto-Abruf beim Gruppenwechsel", variable=self.var_autofetch)

        self.chk_autof.grid(row=0, column=5, padx=4, sticky="w")

        self.btn_browser  = ttk.Button(btn_frame, text="Im Browser öffnen", command=self.on_open_browser); self.btn_browser.grid(row=0, column=6, padx=4, sticky="ew")

        # Anzeige des Gruppen-Pfads + Button

        self.lbl_gpath    = ttk.Label(btn_frame, text=f"Gruppen-Datei: {self.groups_path}")

        self.lbl_gpath.grid(row=0, column=7, padx=6, sticky="w")



        r += 1

        path_frame = ttk.Frame(frm); path_frame.grid(row=r, column=0, columnspan=7, sticky="ew", pady=(0,6))

        for i in range(2): path_frame.columnconfigure(i, weight=(0 if i==0 else 1))

        ttk.Button(path_frame, text="Speicherort für Gruppen …", command=self.on_pick_groups_path).grid(row=0, column=0, padx=4, sticky="w")

        ttk.Label(path_frame, text="(wird in config.json als groups_path gespeichert)").grid(row=0, column=1, sticky="w")



        # --- Status + Vorschau

        r += 1

        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")

        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=6, sticky="nsew", padx=6, pady=3)



        r += 1

        ttk.Label(frm, text="Vorschau (Spaltenkopf klicken zum Sortieren)").grid(row=r, column=0, sticky="w")

        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=12)

        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:

            self.tree.heading(col, text=text); self.tree.column(col, stretch=True, width=120)

        self.tree.grid(row=r, column=1, columnspan=6, sticky="nsew", padx=6, pady=3)



        frm.rowconfigure(r-1, weight=0)  # status

        frm.rowconfigure(r,   weight=1)  # table



        self.rows: List[Dict] = []

        self._make_treeview_sortable(self.tree)

        self._sync_group_id_to_label()



    # -------------------- Helpers --------------------



    def _group_labels(self) -> List[str]: return [g.get("label","") for g in self.groups]

    def _group_map(self) -> Dict[str,str]: return {g.get("label",""): g.get("id","") for g in self.groups}

    def _sync_group_id_to_label(self):

        gid = self._group_map().get(self.var_group_label.get().strip(), "")

        self.var_group_id.set(gid)



    def log(self, msg: str):

        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")



    def set_busy(self, busy: bool):

        state = "disabled" if busy else "normal"

        self.btn_fetch.config(state=state)

        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))



    def on_clear(self):

        self.txt_status.delete("1.0", "end")

        for i in self.tree.get_children(): self.tree.delete(i)

        self.rows = []; self.btn_export.config(state="disabled")



    # Sortierung

    def _make_treeview_sortable(self, tree: ttk.Treeview):

        for col in tree["columns"]:

            tree.heading(col, text=tree.heading(col, "text"),

                         command=lambda c=col: self._sort_by(tree, c, False))



    def _sort_by(self, tree: ttk.Treeview, col: str, descending: bool):

        data = [(tree.set(k, col), k) for k in tree.get_children("")]

        def _num(v):

            try: return float(str(v).replace(",", "."))

            except Exception: return None

        if any(_num(v) is not None for v,_ in data):

            data.sort(key=lambda t: (_num(t[0]) is None, _num(t[0]) or 0.0))

        else:

            data.sort(key=lambda t: str(t[0]).lower())

        if descending: data.reverse()

        for idx, item in enumerate(data): tree.move(item[1], "", idx)

        tree.heading(col, command=lambda: self._sort_by(tree, col, not descending))



    # -------------------- Actions --------------------



    def on_group_selected(self, _evt=None):

        self._sync_group_id_to_label()

        if self.var_autofetch.get() and str(self.btn_fetch["state"]) != "disabled":

            self.root.after(80, self.on_fetch)



    def on_open_browser(self):

        base   = self.var_base.get().strip()

        saison = self.var_saison.get().strip()

        runde  = self.var_runde.get().strip()

        label  = self.var_group_label.get().strip()

        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:

            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")

            return

        url = build_url(base, saison, runde, gid)

        webbrowser.open(url)

        self.log(f"Im Browser geöffnet: {url}")



    def on_fetch(self):

        base   = self.var_base.get().strip()

        saison = self.var_saison.get().strip()

        runde  = self.var_runde.get().strip()

        label  = self.var_group_label.get().strip()

        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()



        if not base or not saison or not runde or not gid:

            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")

            return



        url = build_url(base, saison, runde, gid)

        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)

        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()



    def _fetch_thread(self, url: str):

        try:

            html = fetch_html(url)

            issue = looks_like_login_or_error(html)

            if issue:

                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))

                return

            rows = parse_group_pools(html)

            if not rows:

                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))

                return

            avgs = self._team_avgs(rows)

            self.root.after(0, lambda: self._update_rows(rows, avgs))

        except Exception as e:

            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))



    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:

        avgs: Dict[str, Optional[float]] = {}

        teams = sorted({r["team"] for r in rows})

        for t in teams:

            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]

            avgs[t] = (mean(vals) if vals else None)

        return avgs



    def _abort(self, msg: str):

        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled")



    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):

        self.rows = rows

        for i in self.tree.get_children(): self.tree.delete(i)

        for r in rows:

            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),

                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))

        self.log(f"{len(rows)} Zeilen geladen.")

        self.log("Team-Mittel (Q-TTR):")

        for t, v in avgs.items():

            self.log(f"  • {t}: {'' if v is None else round(v,1)}")

        self.set_busy(False); self.btn_export.config(state="normal")



    def on_export(self):

        if not self.rows:

            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return

        fmt = self.var_format.get(); sprache = self.var_sprache.get()

        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "xlsx": ".xlsx"}

        if fmt not in ext_map:

            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return

        path = filedialog.asksaveasfilename(

            title="Speichern unter",

            defaultextension=ext_map[fmt],

            filetypes=[("Excel","*.xlsx"), ("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")]

        )

        if not path: return

        try:

            export_rows(self.rows, fmt, sprache, path)

            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")

        except Exception as e:

            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")



    def on_pick_groups_path(self):

        # Dialog zum Auswählen des Speicherorts für gruppen.json

        initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)

        initial_file = self.groups_path.name if self.groups_path else "gruppen.json"

        chosen = filedialog.asksaveasfilename(

            title="Speicherort für gruppen.json wählen",

            initialdir=initial_dir,

            initialfile=initial_file,

            defaultextension=".json",

            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]

        )

        if not chosen:

            return

        new_path = _normalize_path(chosen)

        # Wenn Datei existiert und gültig -> laden, sonst aktuelle Gruppen dorthin speichern

        try:

            if Path(new_path).exists():

                data = json.loads(Path(new_path).read_text(encoding="utf-8"))

                if isinstance(data, list):

                    self.groups = data

            else:

                save_groups(self.groups, new_path)

        except Exception as e:

            messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")

            return

        # Pfad übernehmen und in config.json merken

        self.groups_path = new_path

        cfg = load_config(); cfg["groups_path"] = str(new_path)

        save_config(cfg)

        # UI aktualisieren

        self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")

        self._refresh_group_dropdown()



    def on_settings(self):

        # Konfiguration speichern

        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):

            cfg = load_config()

            cfg.update({

                "base": self.var_base.get(),

                "saison": self.var_saison.get(),

                "runde": self.var_runde.get(),

                "group_label": self.var_group_label.get(),

                "group": self.var_group_id.get(),

                "sprache": self.var_sprache.get(),

                "format": self.var_format.get(),

                "autofetch": self.var_autofetch.get(),

                "groups_path": str(self.groups_path),

            })

            try:

                save_config(cfg)

                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")

            except Exception as e:

                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")



    def on_groups(self):

        # Dialog zum Verwalten der Gruppen (Label<->ID) – persistiert in frei wählbarer gruppen.json

        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()

        dlg.geometry("620x420")

        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)

        cols = ("label","id")

        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)

        tree.heading("label", text="Bezeichnung"); tree.heading("id", text="Group-ID")

        tree.column("label", stretch=True, width=360); tree.column("id", stretch=False, width=140)

        tree.pack(fill="both", expand=True, pady=(0,8))



        # Pfadanzeige + Button im Dialog

        path_frame = ttk.Frame(container); path_frame.pack(fill="x", pady=(0,8))

        lbl = ttk.Label(path_frame, text=f"Datei: {self.groups_path}")

        lbl.pack(side="left", padx=(0,6))

        def pick_path():

            # Standard: aktuelles Verzeichnis der bestehenden Datei (oder Config-Ordner)

            initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)

            initial_file = self.groups_path.name if self.groups_path else "gruppen.json"

            chosen = filedialog.asksaveasfilename(

                title="Speicherort für gruppen.json wählen",

                initialdir=initial_dir,

                initialfile=initial_file,

                defaultextension=".json",

                filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]

            )

            if not chosen:

                return

            new_path = _normalize_path(chosen)

            # Wenn Datei existiert und gültig -> laden, sonst aktuelle Gruppen dorthin speichern

            try:

                if Path(new_path).exists():

                    data = json.loads(Path(new_path).read_text(encoding="utf-8"))

                    if isinstance(data, list):

                        self.groups = data

                else:

                    save_groups(self.groups, new_path)

            except Exception as e:

                messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")

                return

            # Pfad übernehmen und in config.json merken

            self.groups_path = new_path

            cfg = load_config(); cfg["groups_path"] = str(new_path)

            save_config(cfg)

            # UI aktualisieren

            lbl.config(text=f"Datei: {self.groups_path}")

            self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")

            refresh_tree(); self._refresh_group_dropdown()



        ttk.Button(path_frame, text="Speicherort wählen …", command=pick_path).pack(side="left")



        # Formular

        form = ttk.Frame(container); form.pack(fill="x", pady=4)

        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")

        var_label = tk.StringVar(); ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")

        var_id = tk.StringVar(); ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)

        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))



        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))

        def refresh_tree():

            for i in tree.get_children(): tree.delete(i)

            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))

        def select_from_tree(_evt=None):

            sel = tree.selection()

            if not sel: return

            vals = tree.item(sel[0], "values"); var_label.set(vals[0]); var_id.set(vals[1])

        def add_or_update():

            label = var_label.get().strip(); gid = var_id.get().strip()

            if not label or not gid:

                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return

            if not gid.isdigit():

                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"): return

            for g in self.groups:

                if g.get("label","") == label:

                    g["id"] = gid; break

            else:

                self.groups.append({"label": label, "id": gid})

            save_groups(self.groups, self.groups_path)

            refresh_tree(); self._refresh_group_dropdown()

        def delete_selected():

            sel = tree.selection()

            if not sel: return

            label = tree.item(sel[0], "values")[0]

            self.groups = [g for g in self.groups if g.get("label","") != label]

            save_groups(self.groups, self.groups_path)

            refresh_tree(); self._refresh_group_dropdown()

        def close_dialog():

            if self.var_group_label.get() not in self._group_labels():

                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")

            self._sync_group_id_to_label()

            try:

                self._save_current_config()

                dlg.destroy()

            except Exception as e:

                messagebox.showerror("Fehler", f"Konnte Konfiguration nicht speichern:\n{e}")



        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)

        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)

        ttk.Button(btns, text="Schließen", command=close_dialog).pack(side="right", padx=4)



        tree.bind("<<TreeviewSelect>>", select_from_tree)

        refresh_tree()



    def _refresh_group_dropdown(self):

        self.cmb_group.config(values=self._group_labels())

        if self.var_group_label.get() not in self._group_labels() and self._group_labels():

            self.var_group_label.set(self._group_labels()[0])

        self._sync_group_id_to_label()



    def _save_current_config(self):

        config = load_config()

        # bestehenden groups_path beibehalten

        config.update({

            "base": self.var_base.get(),

            "saison": self.var_saison.get(),

            "runde": self.var_runde.get(),

            "group_label": self.var_group_label.get(),

            "group": self.var_group_id.get(),

            "sprache": self.var_sprache.get(),

            "format": self.var_format.get(),

            "autofetch": bool(self.var_autofetch.get()),

            "groups_path": str(self.groups_path),

        })

        save_config(config)



def main():

    root = tk.Tk()

    try:

        import ctypes, sys as _sys

        if _sys.platform.startswith("win"):

            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore

    except Exception:

        pass

    root.geometry("1120x640")

    app = TTRScraperGUI(root)

    root.mainloop()



if __name__ == "__main__":

    main()

### 32. Assistent

```text
feat(groups): frei wählbarer Speicherort für gruppen.json + Persistenz in config

- Neuer Config-Key `groups_path`; Fallback ist weiterhin der platformdirs-Config-Ordner
- Hauptfenster: Button „Speicherort für Gruppen …“ + Anzeige des aktiven Pfads (lbl_gpath)
- Gruppen-Dialog: zusätzlicher Pfad-Picker; lädt vorhandene `gruppen.json`, sonst initialisiert sie mit aktuellen Gruppen
- Lese-/Schreibpfad vollständig zentralisiert: `load_groups()`/`save_groups()` nutzen konfigurierten Pfad
- Pfadbehandlung robuster: `_normalize_path()` (unterstützt `~` und relative Pfade)
- Konfigurationsspeicherung aktualisiert (`on_settings`, `_save_current_config`) inkl. `groups_path`
- UI-Refresh nach Pfadwechsel (Dropdown neu befüllen, ID-Sync); Auto-Abruf bleibt erhalten
- HTTP-Header-Version auf `ttr-gui/1.6` angehoben
- Abwärtskompatible Migration aus `config.json["groups"]` weiterhin aktiv

Hinweis:
- Keine Breaking Changes: Ohne gesetzten `groups_path` wird automatisch der Standardpfad verwendet.
```

### 33. Benutzer

gibt es noch verbesserungen

### 34. Assistent

Hier sind die nächst-sinnvollen Upgrades für deine v1.6 – fokussiert auf Stabilität, UX und „Data Engineering“. Ich gebe dir pro Punkt einen kurzen Code-Block, der sich ohne große Umbauten einklinken lässt.

---

## 1) Live-Filter für die Tabelle (Name/Team/Q-TTR)
Praktisch zum schnellen Sichten. Der Filter arbeitet auf `self.rows` und rendert nur passende Zeilen.

**UI ergänzen (unter die Buttons):**
```python
# nach path_frame ...
r += 1
filter_bar = ttk.Frame(frm); filter_bar.grid(row=r, column=0, columnspan=7, sticky="ew", pady=(0,6))
for i in range(6): filter_bar.columnconfigure(i, weight=(1 if i in (1,3,5) else 0))
ttk.Label(filter_bar, text="Filter:").grid(row=0, column=0, sticky="e")
self.var_filter = tk.StringVar()
ttk.Entry(filter_bar, textvariable=self.var_filter).grid(row=0, column=1, sticky="ew", padx=6)
ttk.Label(filter_bar, text="Q-TTR ≥").grid(row=0, column=2, sticky="e")
self.var_qmin = tk.StringVar(); ttk.Entry(filter_bar, textvariable=self.var_qmin, width=7).grid(row=0, column=3, sticky="w")
ttk.Label(filter_bar, text="≤").grid(row=0, column=4, sticky="e")
self.var_qmax = tk.StringVar(); ttk.Entry(filter_bar, textvariable=self.var_qmax, width=7).grid(row=0, column=5, sticky="w")
ttk.Button(filter_bar, text="Anwenden", command=self.apply_filter).grid(row=0, column=6, padx=6)
ttk.Button(filter_bar, text="Filter löschen", command=lambda: [self.var_filter.set(""), self.var_qmin.set(""), self.var_qmax.set(""), self.apply_filter()]).grid(row=0, column=7)
```

**Logik:**
```python
def apply_filter(self):
    term = self.var_filter.get().strip().lower()
    try:
        qmin = int(self.var_qmin.get()) if self.var_qmin.get().strip() else None
    except ValueError:
        qmin = None
    try:
        qmax = int(self.var_qmax.get()) if self.var_qmax.get().strip() else None
    except ValueError:
        qmax = None

    # Tabelle leeren
    for i in self.tree.get_children(): self.tree.delete(i)

    for r in self.rows:
        name = str(r.get("name","")).lower()
        team = str(r.get("team","")).lower()
        qttr = r.get("qttr", None)
        if term and (term not in name and term not in team):
            continue
        if qmin is not None and (not isinstance(qttr, int) or qttr < qmin):
            continue
        if qmax is not None and (not isinstance(qttr, int) or qttr > qmax):
            continue
        self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),
                                            r.get("name",""), r.get("anmerkung",""), r.get("status","")))
```

Tipp: Nach `self._update_rows(...)` am Ende `self.apply_filter()` rufen, damit Filter auch nach neuem Abruf aktiv bleibt.

---

## 2) Abbrechen-Button für laufenden Abruf
Du kannst HTTP nicht hart „killen“, aber du kannst die Ergebnisse ignorieren und die UI sofort freigeben.

**State + Button:**
```python
# im __init__
self._cancel_flag = False
self.btn_cancel = ttk.Button(btn_frame, text="Abbrechen", command=self.on_cancel, state="disabled")
self.btn_cancel.grid(row=0, column=8, padx=4, sticky="ew")
```

**Busy-Handling anpassen:**
```python
def set_busy(self, busy: bool):
    state = "disabled" if busy else "normal"
    self.btn_fetch.config(state=state)
    self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))
    self.btn_cancel.config(state=("normal" if busy else "disabled"))
    self._cancel_flag = False if busy else self._cancel_flag
```

**Cancel-Action:**
```python
def on_cancel(self):
    self._cancel_flag = True
    self.log("Abruf wird abgebrochen …")
```

**Thread respektiert Cancel:**
```python
def _fetch_thread(self, url: str):
    try:
        html = fetch_html(url)
        if self._cancel_flag:  # nach Netz-IO sofort checken
            self.root.after(0, lambda: self._abort("Abgebrochen."))
            return
        issue = looks_like_login_or_error(html)
        if issue:
            self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
            return
        rows = parse_group_pools(html)
        if self._cancel_flag:
            self.root.after(0, lambda: self._abort("Abgebrochen."))
            return
        if not rows:
            self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))
            return
        avgs = self._team_avgs(rows)
        if self._cancel_flag:
            self.root.after(0, lambda: self._abort("Abgebrochen."))
            return
        self.root.after(0, lambda: self._update_rows(rows, avgs))
    except Exception as e:
        self.root.after(0, lambda: self._abort(f"Fehler: {e}"))
```

---

## 3) Rotierendes Logfile + Debug-Switch
Hilfreich bei sporadischen Layout-Änderungen. Logs landen im platformdirs-Ordner.

**Setup:**
```python
import logging
from logging.handlers import RotatingFileHandler

LOG_PATH = CONFIG_DIR / "ttrscraper.log"
logger = logging.getLogger("ttr")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_PATH, maxBytes=512_000, backupCount=3, encoding="utf-8")
fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)

# Beispielhafte Nutzung:
# logger.info("URL: %s", url)
# logger.exception("Fetch failed")
```

**Debug-Checkbox in der UI (optional):**
```python
self.var_debug = tk.BooleanVar(value=False)
ttk.Checkbutton(btn_frame, text="Debug-Log", variable=self.var_debug).grid(row=0, column=9, padx=4, sticky="w")
# Dann vor kritischen Stellen:
if self.var_debug.get(): logger.info("Parse headers: %s", headers)
```

---

## 4) CLI-Modus (Headless) für Automationen/CI
Gleiches Parsing, kein Tk. Ideal für Cron/CI, ohne dein GUI zu ändern.

**Am Anfang von `main()` ergänzen:**
```python
import argparse

def run_cli():
    p = argparse.ArgumentParser(description="Q-TTR aus click-TT (groupPools) exportieren")
    p.add_argument("--base", required=True)
    p.add_argument("--saison", required=True)
    p.add_argument("--runde", required=True, choices=["vorrunde","rueckrunde"])
    p.add_argument("--group", required=True, help="Group-ID")
    p.add_argument("--format", default="json", choices=["json","csv","markdown","xlsx"])
    p.add_argument("--sprache", default="de", choices=["de","en"])
    p.add_argument("--out", required=True, help="Zieldatei")
    args = p.parse_args()

    url = build_url(args.base, args.saison, args.runde, args.group)
    html = fetch_html(url)
    issue = looks_like_login_or_error(html)
    if issue: raise SystemExit(f"Fehler: {issue}")
    rows = parse_group_pools(html)
    if not rows: raise SystemExit("Keine Q-TTR-Daten gefunden.")
    export_rows(rows, args.format, args.sprache, args.out)

if __name__ == "__main__":
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        run_cli()
        sys.exit(0)
    # ... sonst GUI wie bisher
```

---

## 5) Parquet-Export für Analytics (Pandas/Arrow)
Für BI-Pipelines praktischer als CSV.

**Install:**
```bash
pip install pandas pyarrow
```

**Export ergänzen:**
```python
elif datenformat == "parquet":
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_parquet(path, index=False)
```

**Dropdown erweitern:** `values=["json","csv","markdown","xlsx","parquet"]`

---

## 6) Schema-Versionierung & Validierung für `config.json`/`gruppen.json`
Damit künftige Migrationsschritte kontrolliert laufen.

**Kleine Validatoren:**
```python
CONFIG_SCHEMA_VERSION = 1
GROUPS_SCHEMA_VERSION = 1

def validate_config(cfg: dict) -> dict:
    if "schema_version" not in cfg:
        cfg["schema_version"] = 1  # Migrationen könnten hier greifen
    # Pflichtfelder vorbelegen
    cfg.setdefault("base", "https://ttbw.click-tt.de")
    cfg.setdefault("saison", "TTBW 2025/26")
    cfg.setdefault("runde", "vorrunde")
    return cfg

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return validate_config(cfg)
        except Exception:
            pass
    return validate_config({})
```

**Für Gruppen:**
```python
def save_groups(groups: List[Dict[str,str]], path: Optional[Path] = None):
    # ...
    payload = {"schema_version": GROUPS_SCHEMA_VERSION, "groups": cleaned}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def load_groups(...):
    # ...
    if groups_path.exists():
        data = json.loads(groups_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "groups" in data:
            return data["groups"]
        if isinstance(data, list):  # Backward-compat
            return data
```

---

## 7) UX-Leckerbissen
- **Kontextmenü** für Tabelle (Copy row / Copy cell):
  ```python
  def _init_tree_context_menu(self):
      self._menu = tk.Menu(self.root, tearoff=0)
      self._menu.add_command(label="Zeile kopieren", command=self._copy_row)
      self.tree.bind("<Button-3>", lambda e: (self.tree.identify_row(e.y) and self._menu.tk_popup(e.x_root, e.y_root)))
  def _copy_row(self):
      sel = self.tree.selection()
      if not sel: return
      vals = self.tree.item(sel[0], "values")
      self.root.clipboard_clear(); self.root.clipboard_append("\t".join(str(v) for v in vals))
  ```
- **Tastatur-Shortcuts:**  
  ```python
  self.root.bind("<Control-s>", lambda e: self.on_export())
  self.root.bind("<Control-f>", lambda e: [self.var_filter.set(""), self.apply_filter()])
  ```
- **Dark-Mode-freundlich:** `ttk.Style().theme_use("clam")` und optionale Farben; oder `ttkbootstrap` einsetzen (optional).

---

## 8) Parser-Härtung gegen Layout-Drift
- Spaltenerkennung toleranter: akzeptiere auch Varianten wie `"Q TTR"`, `"Q • TTR"`, `"QTTR"`.
  ```python
  def _matches_qttr(h: str) -> bool:
      h = re.sub(r"\W+", "", h.lower())
      return h in ("qttr", "qttrwert", "qttrpunkte")
  # dann: idx_qttr = next(i for i,h in enumerate(headers) if _matches_qttr(h))
  ```
- Fallback, falls `<thead>` fehlt: nimm die erste Tabelle mit einer numerisch dominierten Spalte, deren Überschrift „TTR“ enthält. So bricht es nicht, wenn Vereine „eigenartige“ Templates nutzen.

---

## 9) „Offline“-Modus / HTML-Schnappschuss
Für Debug & Reproduzierbarkeit: HTML der Quelle optional mitschreiben.

```python
self.var_save_html = tk.BooleanVar(value=False)
ttk.Checkbutton(btn_frame, text="HTML mitloggen", variable=self.var_save_html).grid(row=0, column=10, padx=4, sticky="w")

# im _fetch_thread nach fetch:
if self.var_save_html.get():
    snap_path = CONFIG_DIR / "snapshots"; snap_path.mkdir(exist_ok=True)
    (snap_path / "last_groupPools.html").write_text(html, encoding="utf-8")
```

---

## 10) Kleine Sicherheits-/Netiquette-Extras
- **Jitter beim Caching-Revalidate** und konservative Timeouts (du hast schon Retries).  
- **Robots/AGB respektieren**: Button „Pausieren 2s“ bei Batch-Abrufen, falls du künftig mehrere Gruppen nacheinander ziehst.

---

Das sind Upgrades, die unmittelbar Mehrwert bringen, ohne dein Fundament zu verbiegen. Wenn du möchtest, fasse ich 1) Live-Filter, 2) Abbrechen-Button und 3) Rotierendes Log in einen fertigen Patch für deine v1.6 zusammen.

### 35. Benutzer

ja bitte und füge noch die möglichkeit hintzu das suchergebnis auszudrucken

### 36. Assistent

Hier ist deine **v1.7** als kompletter Drop-in:  
neu dabei sind **Live-Filter**, **Abbrechen-Button**, **rotierendes Log mit Debug-Switch** und **Drucken des aktuellen Suchergebnisses (sichtbare/gefüilterte Zeilen) als PDF** mit optionalem Direktdruck.

**Zusatzpaket:**
```bash
pip install requests beautifulsoup4 requests-cache openpyxl platformdirs reportlab
```

---

## `ttr_gui.py` (v1.7)
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
click-TT Q-TTR Scraper (Weg 1, groupPools) – GUI v1.7

Neu:
- Live-Filter (Text + Q-TTR Min/Max) für die Tabelle
- Abbrechen-Button für laufenden Abruf (non-blocking, Ergebnisse werden verworfen)
- Rotierendes Logfile + Debug-Schalter
- Drucken: sichtbare (gefilterte) Zeilen als PDF exportieren und (sofern möglich) direkt an den Drucker senden

Bestehendes:
- Frei wählbarer Speicherort für gruppen.json (Pfad in config.json: groups_path)
- Robustes HTTP (Retries + Cache)
- Sortierbare Tabelle
- XLSX-Export mit Blatt "Stats" (Team-Aggregate + Top-10)
- Gruppen-Pulldown + Konfig-Dialog (Label->ID)
- Plattformneutrale Config (platformdirs)
- "Im Browser öffnen" + optionaler Auto-Abruf beim Gruppenwechsel
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote
from pathlib import Path
import webbrowser
import os
import subprocess
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache
from bs4 import BeautifulSoup
from openpyxl import Workbook
from platformdirs import PlatformDirs

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Logging (rotierendes Log) ------------------------------------------------
import logging
from logging.handlers import RotatingFileHandler

APP_NAME, APP_AUTHOR = "ttrscraper", "ttc"
_dirs = PlatformDirs(APP_NAME, APP_AUTHOR)
CONFIG_DIR  = Path(_dirs.user_config_path); CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_GROUPS_PATH = CONFIG_DIR / "gruppen.json"
LOG_PATH = CONFIG_DIR / "ttrscraper.log"

logger = logging.getLogger("ttr")
logger.setLevel(logging.INFO)
_handler = RotatingFileHandler(LOG_PATH, maxBytes=512_000, backupCount=3, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
if not logger.handlers:
    logger.addHandler(_handler)

# -------------------------------
# Config / Gruppen
# -------------------------------

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("config.json kann nicht gelesen werden")
    return {}

def _normalize_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).absolute()

def get_groups_path_from_config(cfg: Optional[dict] = None) -> Path:
    if cfg is None:
        cfg = load_config()
    p = cfg.get("groups_path")
    if p:
        try:
            return _normalize_path(p)
        except Exception:
            return DEFAULT_GROUPS_PATH
    return DEFAULT_GROUPS_PATH

def save_groups(groups: List[Dict[str, str]], path: Optional[Path] = None):
    if path is None:
        path = get_groups_path_from_config()
    cleaned, seen = [], set()
    for g in groups:
        label = (g.get("label") or "").strip()
        gid   = (g.get("id") or "").strip()
        if not label or not gid:  # skip leere
            continue
        key = (label.lower(), gid)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"label": label, "id": gid})
    cleaned.sort(key=lambda x: x["label"].lower())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")

def load_groups(default: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    cfg = load_config()
    groups_path = get_groups_path_from_config(cfg)
    if groups_path.exists():
        try:
            data = json.loads(groups_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            logger.exception("gruppen.json kann nicht gelesen werden")
    # Migration / Default
    if isinstance(cfg.get("groups"), list) and cfg["groups"]:
        save_groups(cfg["groups"], groups_path)
        return cfg["groups"]
    if default is None:
        default = [{"label": "Kreisliga C2", "id": "494514"}]
    save_groups(default, groups_path)
    return default

# -------------------------------
# HTTP: Session mit Retry + Cache
# -------------------------------

def make_session() -> requests.Session:
    s = requests_cache.CachedSession(
        cache_name=str(CONFIG_DIR / "http_cache"),
        expire_after=1800, allowable_methods=("GET",), stale_if_error=True
    )
    retry = Retry(total=3, backoff_factor=0.8,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET"]))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter); s.mount("http://", adapter)
    s.headers.update({
        "User-Agent": "ttr-gui/1.7 (+https://example.org/bot-info)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5"
    })
    return s

SESSION = make_session()

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
            f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}")

def fetch_html(url: str, timeout: int = 30) -> str:
    resp = SESSION.get(url, timeout=timeout); resp.raise_for_status()
    return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    for h in ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
              "session abgelaufen", "access denied", "forbidden"]:
        if h in text: return h
    if not soup.find("table"): return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team: continue
        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))
        if not table: continue
        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            continue
        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)
        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr: continue
            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None
            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""
            extra = {}
            if len(cols) >= 4: extra["anmerkung"] = cols[3]
            if len(cols) >= 5: extra["status"] = cols[4]
            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}
            if item["name"] or item["qttr"] is not None: results.append(item)
    return results

# -------------------------------
# Export (JSON/CSV/MD/XLSX)
# -------------------------------

def _row_to_list(r: Dict) -> List:
    return [r.get("team",""), r.get("rang",""), r.get("qttr",""),
            r.get("name",""), r.get("anmerkung",""), r.get("status","")]

def _compute_team_stats(rows: List[Dict]) -> List[Dict]:
    stats = []
    teams = sorted({r["team"] for r in rows})
    for t in teams:
        vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
        if not vals:
            stats.append({"Team": t, "Anzahl": 0, "Ø Q-TTR": None, "Min": None, "Max": None})
        else:
            stats.append({"Team": t, "Anzahl": len(vals), "Ø Q-TTR": round(mean(vals), 1),
                          "Min": min(vals), "Max": max(vals)})
    return stats

def _top_n(rows: List[Dict], n: int = 10) -> List[Dict]:
    valids = [r for r in rows if isinstance(r.get("qttr"), int)]
    valids.sort(key=lambda r: r["qttr"], reverse=True)
    out = []
    for i, r in enumerate(valids[:n], 1):
        out.append({"#": i, "Name": r.get("name",""), "Team": r.get("team",""), "Q-TTR": r.get("qttr")})
    return out

def export_xlsx(rows: List[Dict], path: str, sprache: str):
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]
    wb = Workbook()
    ws = wb.active; ws.title = "Q-TTR"
    ws.append(headers)
    for r in rows: ws.append(_row_to_list(r))
    for col in ws.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(10, maxlen + 2), 40)
    ws2 = wb.create_sheet("Stats")
    ws2.append(["Team","Anzahl","Ø Q-TTR","Min","Max"])
    for s in _compute_team_stats(rows):
        ws2.append([s["Team"], s["Anzahl"], s["Ø Q-TTR"], s["Min"], s["Max"]])
    ws2.append([]); ws2.append(["Top-10 (Liga)"]); ws2.append(["#","Name","Team","Q-TTR"])
    for t in _top_n(rows, 10):
        ws2.append([t["#"], t["Name"], t["Team"], t["Q-TTR"]])
    for col in ws2.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws2.column_dimensions[col[0].column_letter].width = min(max(8, maxlen + 2), 40)
    wb.save(path)

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]
    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(headers)
            for r in rows: w.writerow(_row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows: f.write("| " + " | ".join("" if v is None else str(v) for v in _row_to_list(r)) + " |\n")
    elif datenformat == "xlsx":
        export_xlsx(rows, path, sprache)
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# Drucken (PDF erzeugen + OS-Print)
# -------------------------------

def pdf_from_rows(rows: List[Dict], out_path: Path, titel: str = "Q-TTR Ergebnisse", sprache: str = "de"):
    # Minimaler Report mit ReportLab
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    data = [headers]
    for r in rows:
        data.append(_row_to_list(r))

    doc = SimpleDocTemplate(str(out_path), pagesize=landscape(A4), leftMargin=18, rightMargin=18, topMargin=18, bottomMargin=18)
    styles = getSampleStyleSheet()
    elems = [Paragraph(titel, styles["Title"]),
             Paragraph(datetime.now().strftime("%d.%m.%Y %H:%M"), styles["Normal"]),
             Spacer(0, 6)]

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.black),
        ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ("ALIGN", (2,1), (2,-1), "RIGHT"),  # Q-TTR
    ]))
    elems.append(table)
    doc.build(elems)

def print_file(path: Path) -> bool:
    """Versuch, das PDF direkt zu drucken. Rückgabe: True, wenn ein Druckversuch gestartet wurde."""
    try:
        if sys.platform.startswith("win"):
            # Standarddrucker nutzen (silent). Fallback: öffnen.
            os.startfile(str(path), "print")  # type: ignore[attr-defined]
            return True
        else:
            # macOS/Linux: CUPS
            # Erst lp versuchen, sonst lpr. Wenn beides fehlt: False.
            for cmd in (["lp", str(path)], ["lpr", str(path)]):
                try:
                    subprocess.run(cmd, check=True)
                    return True
                except Exception:
                    continue
    except Exception:
        logger.exception("Druckversuch fehlgeschlagen")
    return False

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        for i in range(8): frm.columnconfigure(i, weight=1)

        cfg = load_config()
        self.groups: List[Dict[str,str]] = load_groups()
        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))
        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))
        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))
        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))
        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))
        self.var_group_label = tk.StringVar(value=default_label)
        self.var_group_id    = tk.StringVar(value=default_id)
        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))
        self.var_format  = tk.StringVar(value=cfg.get("format","json"))
        self.var_autofetch = tk.BooleanVar(value=cfg.get("autofetch", False))
        self.var_debug = tk.BooleanVar(value=False)
        self.groups_path = get_groups_path_from_config(cfg)

        # --- Zeile: Base-URL
        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=7, sticky="ew", padx=6, pady=3)

        # --- Zeile: Saison / Runde
        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)
        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,
                                      values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        # --- Zeile: Gruppe + ID + Sprache
        r += 1
        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")
        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,
                                      values=self._group_labels(), state="readonly")
        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)

        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")
        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")
        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)

        # --- Zeile: Datenformat
        r += 1
        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,
                                       values=["json","csv","markdown","xlsx"], state="readonly")
        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)

        # --- Buttons / Schalter
        r += 1
        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=8, sticky="ew", pady=(6,3))
        for i in range(12): btn_frame.columnconfigure(i, weight=1)

        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",           command=self.on_fetch);        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")
        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",       command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")
        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",            command=self.on_clear);        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")
        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",       command=self.on_settings);     self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")
        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",         command=self.on_groups);       self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")
        self.chk_autof    = ttk.Checkbutton(btn_frame, text="Auto-Abruf beim Gruppenwechsel", variable=self.var_autofetch)
        self.chk_autof.grid(row=0, column=5, padx=4, sticky="w")
        self.btn_browser  = ttk.Button(btn_frame, text="Im Browser öffnen", command=self.on_open_browser); self.btn_browser.grid(row=0, column=6, padx=4, sticky="ew")
        self.lbl_gpath    = ttk.Label(btn_frame, text=f"Gruppen-Datei: {self.groups_path}"); self.lbl_gpath.grid(row=0, column=7, padx=6, sticky="w")
        self.btn_pickpath = ttk.Button(btn_frame, text="Speicherort Gruppen …", command=self.on_pick_groups_path); self.btn_pickpath.grid(row=0, column=8, padx=4, sticky="ew")
        self.btn_print    = ttk.Button(btn_frame, text="Drucken …",         command=self.on_print, state="disabled"); self.btn_print.grid(row=0, column=9, padx=4, sticky="ew")
        self.btn_cancel   = ttk.Button(btn_frame, text="Abbrechen",         command=self.on_cancel, state="disabled"); self.btn_cancel.grid(row=0, column=10, padx=4, sticky="ew")
        self.chk_debug    = ttk.Checkbutton(btn_frame, text="Debug-Log",    variable=self.var_debug)
        self.chk_debug.grid(row=0, column=11, padx=4, sticky="w")

        # --- Filterzeile
        r += 1
        filter_bar = ttk.Frame(frm); filter_bar.grid(row=r, column=0, columnspan=8, sticky="ew", pady=(0,6))
        for i in range(10): filter_bar.columnconfigure(i, weight=(1 if i in (1,3,5) else 0))
        ttk.Label(filter_bar, text="Filter:").grid(row=0, column=0, sticky="e")
        self.var_filter = tk.StringVar()
        ttk.Entry(filter_bar, textvariable=self.var_filter).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(filter_bar, text="Q-TTR ≥").grid(row=0, column=2, sticky="e")
        self.var_qmin = tk.StringVar(); ttk.Entry(filter_bar, textvariable=self.var_qmin, width=7).grid(row=0, column=3, sticky="w")
        ttk.Label(filter_bar, text="≤").grid(row=0, column=4, sticky="e")
        self.var_qmax = tk.StringVar(); ttk.Entry(filter_bar, textvariable=self.var_qmax, width=7).grid(row=0, column=5, sticky="w")
        ttk.Button(filter_bar, text="Anwenden", command=self.apply_filter).grid(row=0, column=6, padx=6)
        ttk.Button(filter_bar, text="Filter löschen", command=self.clear_filter).grid(row=0, column=7, padx=6)

        # --- Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=7, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau (Spaltenkopf klicken zum Sortieren)").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=14)
        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:
            self.tree.heading(col, text=text); self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=7, sticky="nsew", padx=6, pady=3)

        frm.rowconfigure(r-1, weight=0)  # status
        frm.rowconfigure(r,   weight=1)  # table

        self.rows: List[Dict] = []
        self.filtered_rows: List[Dict] = []
        self._cancel_flag = False

        self._make_treeview_sortable(self.tree)
        self._sync_group_id_to_label()

        # Shortcuts
        self.root.bind("<Control-s>", lambda e: self.on_export())
        self.root.bind("<Control-f>", lambda e: [self.var_filter.set(""), self.apply_filter()])

    # -------------------- Helpers --------------------

    def _group_labels(self) -> List[str]: return [g.get("label","") for g in self.groups]
    def _group_map(self) -> Dict[str,str]: return {g.get("label",""): g.get("id","") for g in self.groups}
    def _sync_group_id_to_label(self):
        gid = self._group_map().get(self.var_group_label.get().strip(), "")
        self.var_group_id.set(gid)

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")
        if self.var_debug.get():
            logger.info(msg)

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))
        self.btn_print.config(state=("normal" if (not busy and self.filtered_rows) else "disabled"))
        self.btn_cancel.config(state=("normal" if busy else "disabled"))
        self._cancel_flag = False if busy else self._cancel_flag

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.rows = []; self.filtered_rows = []
        self.btn_export.config(state="disabled")
        self.btn_print.config(state="disabled")

    def _make_treeview_sortable(self, tree: ttk.Treeview):
        for col in tree["columns"]:
            tree.heading(col, text=tree.heading(col, "text"),
                         command=lambda c=col: self._sort_by(tree, c, False))

    def _sort_by(self, tree: ttk.Treeview, col: str, descending: bool):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        def _num(v):
            try: return float(str(v).replace(",", "."))
            except Exception: return None
        if any(_num(v) is not None for v,_ in data):
            data.sort(key=lambda t: (_num(t[0]) is None, _num(t[0]) or 0.0))
        else:
            data.sort(key=lambda t: str(t[0]).lower())
        if descending: data.reverse()
        for idx, item in enumerate(data): tree.move(item[1], "", idx)
        tree.heading(col, command=lambda: self._sort_by(tree, col, not descending))

    def _render_rows(self, rows: List[Dict]):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),
                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))
        # Buttons aktualisieren
        self.filtered_rows = rows
        self.btn_print.config(state=("normal" if rows else "disabled"))
        self.btn_export.config(state=("normal" if self.rows else "disabled"))

    # -------------------- Filter --------------------

    def clear_filter(self):
        self.var_filter.set(""); self.var_qmin.set(""); self.var_qmax.set("")
        self.apply_filter()

    def apply_filter(self):
        term = self.var_filter.get().strip().lower()
        def to_int(s):
            try: return int(s.strip()) if s.strip() else None
            except Exception: return None
        qmin = to_int(self.var_qmin.get()); qmax = to_int(self.var_qmax.get())
        out = []
        for r in self.rows:
            name = str(r.get("name","")).lower()
            team = str(r.get("team","")).lower()
            qttr = r.get("qttr", None)
            if term and (term not in name and term not in team):
                continue
            if qmin is not None and (not isinstance(qttr, int) or qttr < qmin):
                continue
            if qmax is not None and (not isinstance(qttr, int) or qttr > qmax):
                continue
            out.append(r)
        self._render_rows(out)

    # -------------------- Actions --------------------

    def on_group_selected(self, _evt=None):
        self._sync_group_id_to_label()
        if self.var_autofetch.get() and str(self.btn_fetch["state"]) != "disabled":
            self.root.after(80, self.on_fetch)

    def on_open_browser(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()
        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return
        url = build_url(base, saison, runde, gid)
        webbrowser.open(url)
        self.log(f"Im Browser geöffnet: {url}")

    def on_fetch(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return

        url = build_url(base, saison, runde, gid)
        if self.var_debug.get(): logger.info("URL: %s", url)
        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def on_cancel(self):
        self._cancel_flag = True
        self.log("Abruf wird abgebrochen …")

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            if self._cancel_flag:
                self.root.after(0, lambda: self._abort("Abgebrochen."))
                return
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if self._cancel_flag:
                self.root.after(0, lambda: self._abort("Abgebrochen."))
                return
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))
                return
            avgs = self._team_avgs(rows)
            def finish():
                self._update_rows(rows, avgs)
            self.root.after(0, finish)
        except Exception as e:
            if self.var_debug.get():
                logger.exception("Fetch-Thread Fehler")
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs: Dict[str, Optional[float]] = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled"); self.btn_print.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        self.apply_filter()  # rendert gefilterte Ansicht
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False)

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return
        fmt = self.var_format.get(); sprache = self.var_sprache.get()
        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "xlsx": ".xlsx"}
        if fmt not in ext_map:
            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return
        path = filedialog.asksaveasfilename(
            title="Speichern unter",
            defaultextension=ext_map[fmt],
            filetypes=[("Excel","*.xlsx"), ("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")]
        )
        if not path: return
        try:
            # Exportiert alle geladenen Zeilen (nicht nur sichtbare).
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    def on_print(self):
        if not self.filtered_rows:
            messagebox.showinfo("Nichts zu drucken", "Keine sichtbaren (gefilterten) Zeilen."); return
        sprache = self.var_sprache.get()
        title = f"Q-TTR – {self.var_saison.get()} / {self.var_runde.get()} – {self.var_group_label.get()}"
        out_dir = CONFIG_DIR / "printouts"; out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = out_dir / f"qttr_{ts}.pdf"
        try:
            pdf_from_rows(self.filtered_rows, pdf_path, titel=title, sprache=sprache)
        except Exception as e:
            if self.var_debug.get(): logger.exception("PDF-Erzeugung fehlgeschlagen")
            messagebox.showerror("Fehler", f"PDF konnte nicht erzeugt werden:\n{e}")
            return
        # Druck versuchen
        attempted = print_file(pdf_path)
        if attempted:
            self.log(f"Druckauftrag gestartet: {pdf_path}")
        else:
            # Fallback: PDF öffnen, Nutzer druckt manuell
            webbrowser.open(str(pdf_path))
            self.log(f"PDF geöffnet (zum manuellen Drucken): {pdf_path}")

    def on_pick_groups_path(self):
        initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)
        initial_file = self.groups_path.name if self.groups_path else "gruppen.json"
        chosen = filedialog.asksaveasfilename(
            title="Speicherort für gruppen.json wählen",
            initialdir=initial_dir, initialfile=initial_file,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]
        )
        if not chosen: return
        new_path = _normalize_path(chosen)
        try:
            if Path(new_path).exists():
                data = json.loads(Path(new_path).read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.groups = data
            else:
                save_groups(self.groups, new_path)
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")
            return
        self.groups_path = new_path
        cfg = load_config(); cfg["groups_path"] = str(new_path); save_config(cfg)
        self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")
        self._refresh_group_dropdown()

    def on_settings(self):
        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):
            cfg = load_config()
            cfg.update({
                "base": self.var_base.get(),
                "saison": self.var_saison.get(),
                "runde": self.var_runde.get(),
                "group_label": self.var_group_label.get(),
                "group": self.var_group_id.get(),
                "sprache": self.var_sprache.get(),
                "format": self.var_format.get(),
                "autofetch": self.var_autofetch.get(),
                "groups_path": str(self.groups_path),
            })
            try:
                save_config(cfg)
                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")

    def on_groups(self):
        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()
        dlg.geometry("620x420")
        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)
        cols = ("label","id")
        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)
        tree.heading("label", text="Bezeichnung"); tree.heading("id", text="Group-ID")
        tree.column("label", stretch=True, width=360); tree.column("id", stretch=False, width=140)
        tree.pack(fill="both", expand=True, pady=(0,8))

        path_frame = ttk.Frame(container); path_frame.pack(fill="x", pady=(0,8))
        lbl = ttk.Label(path_frame, text=f"Datei: {self.groups_path}"); lbl.pack(side="left", padx=(0,6))
        def pick_path():
            initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)
            initial_file = self.groups_path.name if self.groups_path else "gruppen.json"
            chosen = filedialog.asksaveasfilename(
                title="Speicherort für gruppen.json wählen",
                initialdir=initial_dir, initialfile=initial_file,
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]
            )
            if not chosen: return
            new_path = _normalize_path(chosen)
            try:
                if Path(new_path).exists():
                    data = json.loads(Path(new_path).read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        self.groups = data
                else:
                    save_groups(self.groups, new_path)
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")
                return
            self.groups_path = new_path
            cfg = load_config(); cfg["groups_path"] = str(new_path); save_config(cfg)
            lbl.config(text=f"Datei: {self.groups_path}")
            self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")
            refresh_tree(); self._refresh_group_dropdown()
        ttk.Button(path_frame, text="Speicherort wählen …", command=pick_path).pack(side="left")

        form = ttk.Frame(container); form.pack(fill="x", pady=4)
        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")
        var_label = tk.StringVar(); ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")
        var_id = tk.StringVar(); ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)
        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))

        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))
        def refresh_tree():
            for i in tree.get_children(): tree.delete(i)
            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))
        def select_from_tree(_evt=None):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values"); var_label.set(vals[0]); var_id.set(vals[1])
        def add_or_update():
            label = var_label.get().strip(); gid = var_id.get().strip()
            if not label or not gid:
                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return
            if not gid.isdigit():
                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"): return
            for g in self.groups:
                if g.get("label","") == label:
                    g["id"] = gid; break
            else:
                self.groups.append({"label": label, "id": gid})
            save_groups(self.groups, self.groups_path)
            refresh_tree(); self._refresh_group_dropdown()
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            label = tree.item(sel[0], "values")[0]
            self.groups = [g for g in self.groups if g.get("label","") != label]
            save_groups(self.groups, self.groups_path)
            refresh_tree(); self._refresh_group_dropdown()
        def close_dialog():
            if self.var_group_label.get() not in self._group_labels():
                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")
            self._sync_group_id_to_label()
            try:
                self._save_current_config()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Konfiguration nicht speichern:\n{e}")
        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)
        ttk.Button(btns, text="Schließen", command=close_dialog).pack(side="right", padx=4)

        tree.bind("<<TreeviewSelect>>", select_from_tree)
        refresh_tree()

    def _refresh_group_dropdown(self):
        self.cmb_group.config(values=self._group_labels())
        if self.var_group_label.get() not in self._group_labels() and self._group_labels():
            self.var_group_label.set(self._group_labels()[0])
        self._sync_group_id_to_label()

    def _save_current_config(self):
        config = load_config()
        config.update({
            "base": self.var_base.get(),
            "saison": self.var_saison.get(),
            "runde": self.var_runde.get(),
            "group_label": self.var_group_label.get(),
            "group": self.var_group_id.get(),
            "sprache": self.var_sprache.get(),
            "format": self.var_format.get(),
            "autofetch": bool(self.var_autofetch.get()),
            "groups_path": str(self.groups_path),
        })
        save_config(config)

def main():
    root = tk.Tk()
    try:
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass
    root.geometry("1220x720")
    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

---

### Hinweise zur Nutzung
- **Filter**: Text passt auf Name & Team; Q-TTR Min/Max schränkt zusätzlich ein. Die **Druck- und PDF-Ausgabe** nimmt **sichtbare (gefilterte)** Zeilen.  
- **Drucken**: Unter Windows wird der Standarddrucker direkt angesteuert; auf macOS/Linux wird `lp`/`lpr` versucht. Greift das nicht, öffnet sich das erzeugte PDF im Standard-Viewer.  
- **Logs**: Liegen unter `…/ttrscraper/ttrscraper.log`. Aktiviere **Debug-Log** bei Bedarf.  

Wenn du magst, kann ich dir alternativ einen „**Druckvorschau**“-Dialog (Seitenränder, Seitentitel, Quer/Hochformat) oder einen **Markdown-Report** mit Logo/Styles bauen.

### 37. Benutzer

ja und den filter entfernen

### 38. Assistent

Alles klar — hier ist **v1.8**:  
- **Filter komplett entfernt** (UI + Logik).  
- Neuer **Druckvorschau-Dialog** mit Optionen: Titel, Ausrichtung (Hoch/Quer), Schriftgröße, Seitenränder, „PDF öffnen“ und „direkt drucken“.  
- Rest (Cancel-Button, Logging, frei wählbarer `gruppen.json`-Pfad, XLSX-Export mit „Stats“) bleibt.

> Zusatzpaket (wie zuvor + ReportLab fürs PDF):
> ```bash
> pip install requests beautifulsoup4 requests-cache openpyxl platformdirs reportlab
> ```

---

## `ttr_gui.py` (v1.8)
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
click-TT Q-TTR Scraper (Weg 1, groupPools) – GUI v1.8

Neu:
- Filter vollständig entfernt (UI + Code)
- Druckvorschau-Dialog mit Optionen (Titel, Ausrichtung, Schriftgröße, Ränder, PDF öffnen / direkt drucken)

Bestehendes:
- Frei wählbarer Speicherort für gruppen.json (Pfad in config.json: groups_path)
- Robustes HTTP (Retries + Cache)
- Sortierbare Tabelle
- XLSX-Export mit Blatt "Stats" (Team-Aggregate + Top-10)
- Gruppen-Pulldown + Konfig-Dialog (Label->ID)
- Rotierendes Log + Debug-Schalter
- "Im Browser öffnen" + optionaler Auto-Abruf beim Gruppenwechsel
- Abbrechen-Button für laufende Abrufe
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote
from pathlib import Path
import webbrowser
import os
import subprocess
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache
from bs4 import BeautifulSoup
from openpyxl import Workbook
from platformdirs import PlatformDirs

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Logging (rotierendes Log) ------------------------------------------------
import logging
from logging.handlers import RotatingFileHandler

APP_NAME, APP_AUTHOR = "ttrscraper", "ttc"
_dirs = PlatformDirs(APP_NAME, APP_AUTHOR)
CONFIG_DIR  = Path(_dirs.user_config_path); CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_GROUPS_PATH = CONFIG_DIR / "gruppen.json"
LOG_PATH = CONFIG_DIR / "ttrscraper.log"

logger = logging.getLogger("ttr")
logger.setLevel(logging.INFO)
_handler = RotatingFileHandler(LOG_PATH, maxBytes=512_000, backupCount=3, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
if not logger.handlers:
    logger.addHandler(_handler)

# -------------------------------
# Config / Gruppen
# -------------------------------

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("config.json kann nicht gelesen werden")
    return {}

def _normalize_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).absolute()

def get_groups_path_from_config(cfg: Optional[dict] = None) -> Path:
    if cfg is None:
        cfg = load_config()
    p = cfg.get("groups_path")
    if p:
        try:
            return _normalize_path(p)
        except Exception:
            return DEFAULT_GROUPS_PATH
    return DEFAULT_GROUPS_PATH

def save_groups(groups: List[Dict[str, str]], path: Optional[Path] = None):
    if path is None:
        path = get_groups_path_from_config()
    cleaned, seen = [], set()
    for g in groups:
        label = (g.get("label") or "").strip()
        gid   = (g.get("id") or "").strip()
        if not label or not gid:
            continue
        key = (label.lower(), gid)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"label": label, "id": gid})
    cleaned.sort(key=lambda x: x["label"].lower())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")

def load_groups(default: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    cfg = load_config()
    groups_path = get_groups_path_from_config(cfg)
    if groups_path.exists():
        try:
            data = json.loads(groups_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            logger.exception("gruppen.json kann nicht gelesen werden")
    # Migration / Default
    if isinstance(cfg.get("groups"), list) and cfg["groups"]:
        save_groups(cfg["groups"], groups_path)
        return cfg["groups"]
    if default is None:
        default = [{"label": "Kreisliga C2", "id": "494514"}]
    save_groups(default, groups_path)
    return default

# -------------------------------
# HTTP: Session mit Retry + Cache
# -------------------------------

def make_session() -> requests.Session:
    s = requests_cache.CachedSession(
        cache_name=str(CONFIG_DIR / "http_cache"),
        expire_after=1800, allowable_methods=("GET",), stale_if_error=True
    )
    retry = Retry(total=3, backoff_factor=0.8,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET"]))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter); s.mount("http://", adapter)
    s.headers.update({
        "User-Agent": "ttr-gui/1.8 (+https://example.org/bot-info)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5"
    })
    return s

SESSION = make_session()

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
            f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}")

def fetch_html(url: str, timeout: int = 30) -> str:
    resp = SESSION.get(url, timeout=timeout); resp.raise_for_status()
    return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    for h in ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
              "session abgelaufen", "access denied", "forbidden"]:
        if h in text: return h
    if not soup.find("table"): return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    results: List[Dict] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team: continue
        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))
        if not table: continue
        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
        except StopIteration:
            continue
        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)
        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr: continue
            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None
            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""
            extra = {}
            if len(cols) >= 4: extra["anmerkung"] = cols[3]
            if len(cols) >= 5: extra["status"] = cols[4]
            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}
            if item["name"] or item["qttr"] is not None: results.append(item)
    return results

# -------------------------------
# Export (JSON/CSV/MD/XLSX)
# -------------------------------

def _row_to_list(r: Dict) -> List:
    return [r.get("team",""), r.get("rang",""), r.get("qttr",""),
            r.get("name",""), r.get("anmerkung",""), r.get("status","")]

def _compute_team_stats(rows: List[Dict]) -> List[Dict]:
    stats = []
    teams = sorted({r["team"] for r in rows})
    for t in teams:
        vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
        if not vals:
            stats.append({"Team": t, "Anzahl": 0, "Ø Q-TTR": None, "Min": None, "Max": None})
        else:
            stats.append({"Team": t, "Anzahl": len(vals), "Ø Q-TTR": round(mean(vals), 1),
                          "Min": min(vals), "Max": max(vals)})
    return stats

def _top_n(rows: List[Dict], n: int = 10) -> List[Dict]:
    valids = [r for r in rows if isinstance(r.get("qttr"), int)]
    valids.sort(key=lambda r: r["qttr"], reverse=True)
    out = []
    for i, r in enumerate(valids[:n], 1):
        out.append({"#": i, "Name": r.get("name",""), "Team": r.get("team",""), "Q-TTR": r.get("qttr")})
    return out

def export_xlsx(rows: List[Dict], path: str, sprache: str):
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]
    wb = Workbook()
    ws = wb.active; ws.title = "Q-TTR"
    ws.append(headers)
    for r in rows: ws.append(_row_to_list(r))
    for col in ws.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(10, maxlen + 2), 40)
    ws2 = wb.create_sheet("Stats")
    ws2.append(["Team","Anzahl","Ø Q-TTR","Min","Max"])
    for s in _compute_team_stats(rows):
        ws2.append([s["Team"], s["Anzahl"], s["Ø Q-TTR"], s["Min"], s["Max"]])
    ws2.append([]); ws2.append(["Top-10 (Liga)"]); ws2.append(["#","Name","Team","Q-TTR"])
    for t in _top_n(rows, 10):
        ws2.append([t["#"], t["Name"], t["Team"], t["Q-TTR"]])
    for col in ws2.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws2.column_dimensions[col[0].column_letter].width = min(max(8, maxlen + 2), 40)
    wb.save(path)

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]
    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(headers)
            for r in rows: w.writerow(_row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows: f.write("| " + " | ".join("" if v is None else str(v) for v in _row_to_list(r)) + " |\n")
    elif datenformat == "xlsx":
        export_xlsx(rows, path, sprache)
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# Drucken (PDF erzeugen + OS-Print)
# -------------------------------

def mm_to_pt(mm: float) -> float:
    return mm * 72.0 / 25.4

def pdf_from_rows(rows: List[Dict], out_path: Path, titel: str = "Q-TTR Ergebnisse",
                  sprache: str = "de", orientation: str = "landscape",
                  fontsize: int = 8, margins_pt: Dict[str, float] = None):
    from reportlab.lib.pagesizes import A4, landscape, portrait
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    if margins_pt is None:
        margins_pt = {"left": 18, "right": 18, "top": 18, "bottom": 18}

    pagesize = landscape(A4) if orientation == "landscape" else portrait(A4)
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    data = [headers] + [_row_to_list(r) for r in rows]

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=pagesize,
        leftMargin=margins_pt["left"], rightMargin=margins_pt["right"],
        topMargin=margins_pt["top"], bottomMargin=margins_pt["bottom"]
    )
    styles = getSampleStyleSheet()
    elems = [Paragraph(titel, styles["Title"]),
             Paragraph(datetime.now().strftime("%d.%m.%Y %H:%M"), styles["Normal"]),
             Spacer(0, 6)]

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.black),
        ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), fontsize),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ("ALIGN", (2,1), (2,-1), "RIGHT"),  # Q-TTR
    ]))
    elems.append(table)
    doc.build(elems)

def print_file(path: Path) -> bool:
    """Versuch, das PDF direkt zu drucken. Rückgabe: True, wenn ein Druckversuch gestartet wurde."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path), "print")  # type: ignore[attr-defined]
            return True
        else:
            for cmd in (["lp", str(path)], ["lpr", str(path)]):
                try:
                    subprocess.run(cmd, check=True)
                    return True
                except Exception:
                    continue
    except Exception:
        logger.exception("Druckversuch fehlgeschlagen")
    return False

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        for i in range(8): frm.columnconfigure(i, weight=1)

        cfg = load_config()
        self.groups: List[Dict[str,str]] = load_groups()
        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))
        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))
        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))
        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))
        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))
        self.var_group_label = tk.StringVar(value=default_label)
        self.var_group_id    = tk.StringVar(value=default_id)
        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))
        self.var_format  = tk.StringVar(value=cfg.get("format","json"))
        self.var_autofetch = tk.BooleanVar(value=cfg.get("autofetch", False))
        self.var_debug = tk.BooleanVar(value=False)
        self.groups_path = get_groups_path_from_config(cfg)

        # --- Zeile: Base-URL
        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=7, sticky="ew", padx=6, pady=3)

        # --- Zeile: Saison / Runde
        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)
        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,
                                      values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        # --- Zeile: Gruppe + ID + Sprache
        r += 1
        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")
        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,
                                      values=self._group_labels(), state="readonly")
        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)

        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")
        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")
        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)

        # --- Zeile: Datenformat
        r += 1
        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,
                                       values=["json","csv","markdown","xlsx"], state="readonly")
        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)

        # --- Buttons / Schalter
        r += 1
        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=8, sticky="ew", pady=(6,3))
        for i in range(12): btn_frame.columnconfigure(i, weight=1)

        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",           command=self.on_fetch);        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")
        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",       command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")
        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",            command=self.on_clear);        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")
        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",       command=self.on_settings);     self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")
        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",         command=self.on_groups);       self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")
        self.chk_autof    = ttk.Checkbutton(btn_frame, text="Auto-Abruf beim Gruppenwechsel", variable=self.var_autofetch)
        self.chk_autof.grid(row=0, column=5, padx=4, sticky="w")
        self.btn_browser  = ttk.Button(btn_frame, text="Im Browser öffnen", command=self.on_open_browser); self.btn_browser.grid(row=0, column=6, padx=4, sticky="ew")
        self.lbl_gpath    = ttk.Label(btn_frame, text=f"Gruppen-Datei: {self.groups_path}"); self.lbl_gpath.grid(row=0, column=7, padx=6, sticky="w")
        self.btn_pickpath = ttk.Button(btn_frame, text="Speicherort Gruppen …", command=self.on_pick_groups_path); self.btn_pickpath.grid(row=0, column=8, padx=4, sticky="ew")
        self.btn_print    = ttk.Button(btn_frame, text="Drucken …",         command=self.on_print, state="disabled"); self.btn_print.grid(row=0, column=9, padx=4, sticky="ew")
        self.btn_cancel   = ttk.Button(btn_frame, text="Abbrechen",         command=self.on_cancel, state="disabled"); self.btn_cancel.grid(row=0, column=10, padx=4, sticky="ew")
        self.chk_debug    = ttk.Checkbutton(btn_frame, text="Debug-Log",    variable=self.var_debug)
        self.chk_debug.grid(row=0, column=11, padx=4, sticky="w")

        # --- Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=7, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau (Spaltenkopf klicken zum Sortieren)").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=16)
        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:
            self.tree.heading(col, text=text); self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=7, sticky="nsew", padx=6, pady=3)

        frm.rowconfigure(r-1, weight=0)  # status
        frm.rowconfigure(r,   weight=1)  # table

        self.rows: List[Dict] = []
        self._cancel_flag = False

        self._make_treeview_sortable(self.tree)
        self._sync_group_id_to_label()

        # Shortcut nur noch für Speichern
        self.root.bind("<Control-s>", lambda e: self.on_export())

    # -------------------- Helpers --------------------

    def _group_labels(self) -> List[str]: return [g.get("label","") for g in self.groups]
    def _group_map(self) -> Dict[str,str]: return {g.get("label",""): g.get("id","") for g in self.groups}
    def _sync_group_id_to_label(self):
        gid = self._group_map().get(self.var_group_label.get().strip(), "")
        self.var_group_id.set(gid)

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")
        if self.var_debug.get():
            logger.info(msg)

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))
        self.btn_print.config(state=("normal" if (not busy and self.rows) else "disabled"))
        self.btn_cancel.config(state=("normal" if busy else "disabled"))
        self._cancel_flag = False if busy else self._cancel_flag

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.rows = []
        self.btn_export.config(state="disabled")
        self.btn_print.config(state="disabled")

    def _make_treeview_sortable(self, tree: ttk.Treeview):
        for col in tree["columns"]:
            tree.heading(col, text=tree.heading(col, "text"),
                         command=lambda c=col: self._sort_by(tree, c, False))

    def _sort_by(self, tree: ttk.Treeview, col: str, descending: bool):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        def _num(v):
            try: return float(str(v).replace(",", "."))
            except Exception: return None
        if any(_num(v) is not None for v,_ in data):
            data.sort(key=lambda t: (_num(t[0]) is None, _num(t[0]) or 0.0))
        else:
            data.sort(key=lambda t: str(t[0]).lower())
        if descending: data.reverse()
        for idx, item in enumerate(data): tree.move(item[1], "", idx)
        tree.heading(col, command=lambda: self._sort_by(tree, col, not descending))

    def _render_rows(self, rows: List[Dict]):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),
                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))
        self.btn_print.config(state=("normal" if rows else "disabled"))
        self.btn_export.config(state=("normal" if rows else "disabled"))

    # -------------------- Actions --------------------

    def on_group_selected(self, _evt=None):
        self._sync_group_id_to_label()
        if self.var_autofetch.get() and str(self.btn_fetch["state"]) != "disabled":
            self.root.after(80, self.on_fetch)

    def on_open_browser(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()
        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return
        url = build_url(base, saison, runde, gid)
        webbrowser.open(url)
        self.log(f"Im Browser geöffnet: {url}")

    def on_fetch(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return

        url = build_url(base, saison, runde, gid)
        if self.var_debug.get(): logger.info("URL: %s", url)
        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def on_cancel(self):
        self._cancel_flag = True
        self.log("Abruf wird abgebrochen …")

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            if self._cancel_flag:
                self.root.after(0, lambda: self._abort("Abgebrochen."))
                return
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if self._cancel_flag:
                self.root.after(0, lambda: self._abort("Abgebrochen."))
                return
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))
                return
            avgs = self._team_avgs(rows)
            def finish():
                self._update_rows(rows, avgs)
            self.root.after(0, finish)
        except Exception as e:
            if self.var_debug.get():
                logger.exception("Fetch-Thread Fehler")
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs: Dict[str, Optional[float]] = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled"); self.btn_print.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        self._render_rows(rows)
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False)

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return
        fmt = self.var_format.get(); sprache = self.var_sprache.get()
        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "xlsx": ".xlsx"}
        if fmt not in ext_map:
            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return
        path = filedialog.asksaveasfilename(
            title="Speichern unter",
            defaultextension=ext_map[fmt],
            filetypes=[("Excel","*.xlsx"), ("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")]
        )
        if not path: return
        try:
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    # -------------------- Druckvorschau --------------------

    def on_print(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu drucken", "Keine Daten geladen."); return

        dlg = tk.Toplevel(self.root); dlg.title("Druckvorschau / Optionen"); dlg.grab_set()
        dlg.geometry("520x260")
        box = ttk.Frame(dlg, padding=10); box.pack(fill="both", expand=True)

        # Felder
        var_title = tk.StringVar(value=f"Q-TTR – {self.var_saison.get()} / {self.var_runde.get()} – {self.var_group_label.get()}")
        var_orient = tk.StringVar(value="landscape")  # 'landscape' | 'portrait'
        var_font   = tk.IntVar(value=8)
        var_open   = tk.BooleanVar(value=True)
        # Ränder (mm)
        var_m_left   = tk.DoubleVar(value=12.0)
        var_m_right  = tk.DoubleVar(value=12.0)
        var_m_top    = tk.DoubleVar(value=12.0)
        var_m_bottom = tk.DoubleVar(value=12.0)

        # Layout
        r = 0
        ttk.Label(box, text="Titel").grid(row=r, column=0, sticky="w")
        ttk.Entry(box, textvariable=var_title).grid(row=r, column=1, columnspan=3, sticky="ew", padx=6, pady=4)

        r += 1
        ttk.Label(box, text="Ausrichtung").grid(row=r, column=0, sticky="w")
        ttk.Radiobutton(box, text="Querformat", variable=var_orient, value="landscape").grid(row=r, column=1, sticky="w")
        ttk.Radiobutton(box, text="Hochformat", variable=var_orient, value="portrait").grid(row=r, column=2, sticky="w")
        ttk.Label(box, text="Schriftgröße").grid(row=r, column=3, sticky="e")
        ttk.Spinbox(box, from_=6, to=12, textvariable=var_font, width=5).grid(row=r, column=4, sticky="w", padx=6)

        r += 1
        ttk.Label(box, text="Ränder (mm)").grid(row=r, column=0, sticky="w")
        ttk.Label(box, text="Links").grid(row=r, column=1, sticky="e")
        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_left, width=6).grid(row=r, column=2, sticky="w")
        ttk.Label(box, text="Rechts").grid(row=r, column=3, sticky="e")
        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_right, width=6).grid(row=r, column=4, sticky="w")

        r += 1
        ttk.Label(box, text="").grid(row=r, column=0, sticky="w")
        ttk.Label(box, text="Oben").grid(row=r, column=1, sticky="e")
        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_top, width=6).grid(row=r, column=2, sticky="w")
        ttk.Label(box, text="Unten").grid(row=r, column=3, sticky="e")
        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_bottom, width=6).grid(row=r, column=4, sticky="w")

        r += 1
        ttk.Checkbutton(box, text="PDF nach Erzeugung öffnen", variable=var_open).grid(row=r, column=0, columnspan=2, sticky="w", pady=(6,0))

        for c in range(5): box.columnconfigure(c, weight=(1 if c in (1,2,4) else 0))

        # Buttons
        btns = ttk.Frame(box); btns.grid(row=r+1, column=0, columnspan=5, sticky="ew", pady=(12,0))
        for i in range(3): btns.columnconfigure(i, weight=1)

        def make_pdf_and(option_print: bool):
            try:
                margins = {
                    "left":   mm_to_pt(var_m_left.get()),
                    "right":  mm_to_pt(var_m_right.get()),
                    "top":    mm_to_pt(var_m_top.get()),
                    "bottom": mm_to_pt(var_m_bottom.get()),
                }
            except Exception:
                messagebox.showerror("Fehler", "Ungültige Randangaben."); return

            out_dir = CONFIG_DIR / "printouts"; out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = out_dir / f"qttr_{ts}.pdf"

            try:
                pdf_from_rows(
                    self.rows, pdf_path,
                    titel=var_title.get().strip() or "Q-TTR",
                    sprache=self.var_sprache.get(),
                    orientation=var_orient.get(),
                    fontsize=int(var_font.get()),
                    margins_pt=margins
                )
            except Exception as e:
                if self.var_debug.get(): logger.exception("PDF-Erzeugung fehlgeschlagen")
                messagebox.showerror("Fehler", f"PDF konnte nicht erzeugt werden:\n{e}")
                return

            if option_print:
                attempted = print_file(pdf_path)
                if attempted:
                    self.log(f"Druckauftrag gestartet: {pdf_path}")
                    dlg.destroy()
                else:
                    webbrowser.open(str(pdf_path))
                    self.log(f"PDF geöffnet (zum manuellen Drucken): {pdf_path}")
                    dlg.destroy()
            else:
                # Nur speichern/öffnen
                if var_open.get():
                    webbrowser.open(str(pdf_path))
                self.log(f"PDF erzeugt: {pdf_path}")
                dlg.destroy()

        ttk.Button(btns, text="Als PDF erzeugen", command=lambda: make_pdf_and(False)).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(btns, text="Direkt drucken",   command=lambda: make_pdf_and(True)).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(btns, text="Abbrechen",        command=dlg.destroy).grid(row=0, column=2, padx=6, sticky="ew")

    # -------------------- Gruppen/Settings --------------------

    def on_pick_groups_path(self):
        initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)
        initial_file = self.groups_path.name if self.groups_path else "gruppen.json"
        chosen = filedialog.asksaveasfilename(
            title="Speicherort für gruppen.json wählen",
            initialdir=initial_dir, initialfile=initial_file,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]
        )
        if not chosen: return
        new_path = _normalize_path(chosen)
        try:
            if Path(new_path).exists():
                data = json.loads(Path(new_path).read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.groups = data
            else:
                save_groups(self.groups, new_path)
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")
            return
        self.groups_path = new_path
        cfg = load_config(); cfg["groups_path"] = str(new_path); save_config(cfg)
        self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")
        self._refresh_group_dropdown()

    def on_settings(self):
        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):
            cfg = load_config()
            cfg.update({
                "base": self.var_base.get(),
                "saison": self.var_saison.get(),
                "runde": self.var_runde.get(),
                "group_label": self.var_group_label.get(),
                "group": self.var_group_id.get(),
                "sprache": self.var_sprache.get(),
                "format": self.var_format.get(),
                "autofetch": self.var_autofetch.get(),
                "groups_path": str(self.groups_path),
            })
            try:
                save_config(cfg)
                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")

    def on_groups(self):
        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()
        dlg.geometry("620x420")
        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)
        cols = ("label","id")
        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)
        tree.heading("label", text="Bezeichnung"); tree.heading("id", text="Group-ID")
        tree.column("label", stretch=True, width=360); tree.column("id", stretch=False, width=140)
        tree.pack(fill="both", expand=True, pady=(0,8))

        path_frame = ttk.Frame(container); path_frame.pack(fill="x", pady=(0,8))
        lbl = ttk.Label(path_frame, text=f"Datei: {self.groups_path}"); lbl.pack(side="left", padx=(0,6))
        def pick_path():
            initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)
            initial_file = self.groups_path.name if self.groups_path else "gruppen.json"
            chosen = filedialog.asksaveasfilename(
                title="Speicherort für gruppen.json wählen",
                initialdir=initial_dir, initialfile=initial_file,
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]
            )
            if not chosen: return
            new_path = _normalize_path(chosen)
            try:
                if Path(new_path).exists():
                    data = json.loads(Path(new_path).read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        self.groups = data
                else:
                    save_groups(self.groups, new_path)
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")
                return
            self.groups_path = new_path
            cfg = load_config(); cfg["groups_path"] = str(new_path); save_config(cfg)
            lbl.config(text=f"Datei: {self.groups_path}")
            self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")
            refresh_tree(); self._refresh_group_dropdown()
        ttk.Button(path_frame, text="Speicherort wählen …", command=pick_path).pack(side="left")

        form = ttk.Frame(container); form.pack(fill="x", pady=4)
        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")
        var_label = tk.StringVar(); ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")
        var_id = tk.StringVar(); ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)
        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))

        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))
        def refresh_tree():
            for i in tree.get_children(): tree.delete(i)
            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))
        def select_from_tree(_evt=None):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values"); var_label.set(vals[0]); var_id.set(vals[1])
        def add_or_update():
            label = var_label.get().strip(); gid = var_id.get().strip()
            if not label or not gid:
                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return
            if not gid.isdigit():
                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"): return
            for g in self.groups:
                if g.get("label","") == label:
                    g["id"] = gid; break
            else:
                self.groups.append({"label": label, "id": gid})
            save_groups(self.groups, self.groups_path)
            refresh_tree(); self._refresh_group_dropdown()
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            label = tree.item(sel[0], "values")[0]
            self.groups = [g for g in self.groups if g.get("label","") != label]
            save_groups(self.groups, self.groups_path)
            refresh_tree(); self._refresh_group_dropdown()
        def close_dialog():
            if self.var_group_label.get() not in self._group_labels():
                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")
            self._sync_group_id_to_label()
            try:
                self._save_current_config()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Konfiguration nicht speichern:\n{e}")
        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)
        ttk.Button(btns, text="Schließen", command=close_dialog).pack(side="right", padx=4)

        tree.bind("<<TreeviewSelect>>", select_from_tree)
        refresh_tree()

    def _refresh_group_dropdown(self):
        self.cmb_group.config(values=self._group_labels())
        if self.var_group_label.get() not in self._group_labels() and self._group_labels():
            self.var_group_label.set(self._group_labels()[0])
        self._sync_group_id_to_label()

    def _save_current_config(self):
        config = load_config()
        config.update({
            "base": self.var_base.get(),
            "saison": self.var_saison.get(),
            "runde": self.var_runde.get(),
            "group_label": self.var_group_label.get(),
            "group": self.var_group_id.get(),
            "sprache": self.var_sprache.get(),
            "format": self.var_format.get(),
            "autofetch": bool(self.var_autofetch.get()),
            "groups_path": str(self.groups_path),
        })
        save_config(config)

def main():
    root = tk.Tk()
    try:
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass
    root.geometry("1200x700")
    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

---

Wenn du magst, ergänze ich in der Druckvorschau noch **Seitennummern** und **Logo/Club-Header** (ReportLab-Canvas-Callback) oder einen **CSV-→PDF-Batchdruck** für mehrere Gruppen aus deiner `gruppen.json`.

### 39. Benutzer

neuer code als grundlage: #!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

click-TT Q-TTR Scraper (Weg 1, groupPools) – GUI v1.8



Neu:

- Filter vollständig entfernt (UI + Code)

- Druckvorschau-Dialog mit Optionen (Titel, Ausrichtung, Schriftgröße, Ränder, PDF öffnen / direkt drucken)



Bestehendes:

- Frei wählbarer Speicherort für gruppen.json (Pfad in config.json: groups_path)

- Robustes HTTP (Retries + Cache)

- Sortierbare Tabelle

- XLSX-Export mit Blatt "Stats" (Team-Aggregate + Top-10)

- Gruppen-Pulldown + Konfig-Dialog (Label->ID)

- Rotierendes Log + Debug-Schalter

- "Im Browser öffnen" + optionaler Auto-Abruf beim Gruppenwechsel

- Abbrechen-Button für laufende Abrufe

"""



import csv

import json

import re

import sys

import threading

from statistics import mean

from typing import Dict, List, Optional

from urllib.parse import quote

from pathlib import Path

import webbrowser

import os

import subprocess

from datetime import datetime



import requests

from requests.adapters import HTTPAdapter

from urllib3.util.retry import Retry

import requests_cache

from bs4 import BeautifulSoup

from openpyxl import Workbook

from platformdirs import PlatformDirs



import tkinter as tk

from tkinter import ttk, messagebox, filedialog



# --- Logging (rotierendes Log) ------------------------------------------------

import logging

from logging.handlers import RotatingFileHandler



APP_NAME, APP_AUTHOR = "ttrscraper", "ttc"

_dirs = PlatformDirs(APP_NAME, APP_AUTHOR)

CONFIG_DIR  = Path(_dirs.user_config_path); CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_GROUPS_PATH = CONFIG_DIR / "gruppen.json"

LOG_PATH = CONFIG_DIR / "ttrscraper.log"



logger = logging.getLogger("ttr")

logger.setLevel(logging.INFO)

_handler = RotatingFileHandler(LOG_PATH, maxBytes=512_000, backupCount=3, encoding="utf-8")

_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))

if not logger.handlers:

    logger.addHandler(_handler)



# -------------------------------

# Config / Gruppen

# -------------------------------



def save_config(config: dict):

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")



def load_config() -> dict:

    if CONFIG_PATH.exists():

        try:

            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

        except Exception:

            logger.exception("config.json kann nicht gelesen werden")

    return {}



def _normalize_path(p: str) -> Path:

    return Path(os.path.expanduser(p)).absolute()



def get_groups_path_from_config(cfg: Optional[dict] = None) -> Path:

    if cfg is None:

        cfg = load_config()

    p = cfg.get("groups_path")

    if p:

        try:

            return _normalize_path(p)

        except Exception:

            return DEFAULT_GROUPS_PATH

    return DEFAULT_GROUPS_PATH



def save_groups(groups: List[Dict[str, str]], path: Optional[Path] = None):

    if path is None:

        path = get_groups_path_from_config()

    cleaned, seen = [], set()

    for g in groups:

        label = (g.get("label") or "").strip()

        gid   = (g.get("id") or "").strip()

        if not label or not gid:

            continue

        key = (label.lower(), gid)

        if key in seen:

            continue

        seen.add(key)

        cleaned.append({"label": label, "id": gid})

    cleaned.sort(key=lambda x: x["label"].lower())

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")



def load_groups(default: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:

    cfg = load_config()

    groups_path = get_groups_path_from_config(cfg)

    if groups_path.exists():

        try:

            data = json.loads(groups_path.read_text(encoding="utf-8"))

            if isinstance(data, list):

                return data

        except Exception:

            logger.exception("gruppen.json kann nicht gelesen werden")

    # Migration / Default

    if isinstance(cfg.get("groups"), list) and cfg["groups"]:

        save_groups(cfg["groups"], groups_path)

        return cfg["groups"]

    if default is None:

        default = [{"label": "Kreisliga C2", "id": "494514"}]

    save_groups(default, groups_path)

    return default



# -------------------------------

# HTTP: Session mit Retry + Cache

# -------------------------------



def make_session() -> requests.Session:

    s = requests_cache.CachedSession(

        cache_name=str(CONFIG_DIR / "http_cache"),

        expire_after=1800, allowable_methods=("GET",), stale_if_error=True

    )

    retry = Retry(total=3, backoff_factor=0.8,

                  status_forcelist=(429, 500, 502, 503, 504),

                  allowed_methods=frozenset(["GET"]))

    adapter = HTTPAdapter(max_retries=retry)

    s.mount("https://", adapter); s.mount("http://", adapter)

    s.headers.update({

        "User-Agent": "ttr-gui/1.8 (+https://example.org/bot-info)",

        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5"

    })

    return s



SESSION = make_session()



# -------------------------------

# Scraping-Logik (Weg 1)

# -------------------------------



def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:

    base = base_url.rstrip("/")

    return (f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"

            f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}")



def fetch_html(url: str, timeout: int = 30) -> str:

    resp = SESSION.get(url, timeout=timeout); resp.raise_for_status()

    return resp.text



def looks_like_login_or_error(html: str) -> Optional[str]:

    soup = BeautifulSoup(html, "lxml")

    text = soup.get_text(" ", strip=True).lower()

    for h in ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",

              "session abgelaufen", "access denied", "forbidden"]:

        if h in text: return h

    if not soup.find("table"): return "keine tabellen gefunden"

    return None



def parse_group_pools(html: str) -> List[Dict]:

    soup = BeautifulSoup(html, "lxml")

    results: List[Dict] = []

    for heading in soup.find_all(["h2", "h3", "h4"]):

        team = heading.get_text(strip=True)

        if not team: continue

        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))

        if not table: continue

        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]

        try:

            idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)

        except StopIteration:

            continue

        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)

        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)

        for row in table.select("tbody tr"):

            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]

            if not cols or len(cols) <= idx_qttr: continue

            qttr_raw = cols[idx_qttr]

            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)

            qttr_val = int(qttr_num) if qttr_num.isdigit() else None

            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""

            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""

            extra = {}

            if len(cols) >= 4: extra["anmerkung"] = cols[3]

            if len(cols) >= 5: extra["status"] = cols[4]

            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}

            if item["name"] or item["qttr"] is not None: results.append(item)

    return results



# -------------------------------

# Export (JSON/CSV/MD/XLSX)

# -------------------------------



def _row_to_list(r: Dict) -> List:

    return [r.get("team",""), r.get("rang",""), r.get("qttr",""),

            r.get("name",""), r.get("anmerkung",""), r.get("status","")]



def _compute_team_stats(rows: List[Dict]) -> List[Dict]:

    stats = []

    teams = sorted({r["team"] for r in rows})

    for t in teams:

        vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]

        if not vals:

            stats.append({"Team": t, "Anzahl": 0, "Ø Q-TTR": None, "Min": None, "Max": None})

        else:

            stats.append({"Team": t, "Anzahl": len(vals), "Ø Q-TTR": round(mean(vals), 1),

                          "Min": min(vals), "Max": max(vals)})

    return stats



def _top_n(rows: List[Dict], n: int = 10) -> List[Dict]:

    valids = [r for r in rows if isinstance(r.get("qttr"), int)]

    valids.sort(key=lambda r: r["qttr"], reverse=True)

    out = []

    for i, r in enumerate(valids[:n], 1):

        out.append({"#": i, "Name": r.get("name",""), "Team": r.get("team",""), "Q-TTR": r.get("qttr")})

    return out



def export_xlsx(rows: List[Dict], path: str, sprache: str):

    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \

              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    wb = Workbook()

    ws = wb.active; ws.title = "Q-TTR"

    ws.append(headers)

    for r in rows: ws.append(_row_to_list(r))

    for col in ws.columns:

        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)

        ws.column_dimensions[col[0].column_letter].width = min(max(10, maxlen + 2), 40)

    ws2 = wb.create_sheet("Stats")

    ws2.append(["Team","Anzahl","Ø Q-TTR","Min","Max"])

    for s in _compute_team_stats(rows):

        ws2.append([s["Team"], s["Anzahl"], s["Ø Q-TTR"], s["Min"], s["Max"]])

    ws2.append([]); ws2.append(["Top-10 (Liga)"]); ws2.append(["#","Name","Team","Q-TTR"])

    for t in _top_n(rows, 10):

        ws2.append([t["#"], t["Name"], t["Team"], t["Q-TTR"]])

    for col in ws2.columns:

        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)

        ws2.column_dimensions[col[0].column_letter].width = min(max(8, maxlen + 2), 40)

    wb.save(path)



def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:

    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \

              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    if datenformat == "json":

        with open(path, "w", encoding="utf-8") as f:

            json.dump(rows, f, ensure_ascii=False, indent=2)

    elif datenformat == "csv":

        with open(path, "w", encoding="utf-8-sig", newline="") as f:

            w = csv.writer(f); w.writerow(headers)

            for r in rows: w.writerow(_row_to_list(r))

    elif datenformat == "markdown":

        with open(path, "w", encoding="utf-8") as f:

            f.write("| " + " | ".join(headers) + " |\n")

            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")

            for r in rows: f.write("| " + " | ".join("" if v is None else str(v) for v in _row_to_list(r)) + " |\n")

    elif datenformat == "xlsx":

        export_xlsx(rows, path, sprache)

    else:

        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")



# -------------------------------

# Drucken (PDF erzeugen + OS-Print)

# -------------------------------



def mm_to_pt(mm: float) -> float:

    return mm * 72.0 / 25.4



def pdf_from_rows(rows: List[Dict], out_path: Path, titel: str = "Q-TTR Ergebnisse",

                  sprache: str = "de", orientation: str = "landscape",

                  fontsize: int = 8, margins_pt: Dict[str, float] = None):

    from reportlab.lib.pagesizes import A4, landscape, portrait

    from reportlab.lib import colors

    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    from reportlab.lib.styles import getSampleStyleSheet



    if margins_pt is None:

        margins_pt = {"left": 18, "right": 18, "top": 18, "bottom": 18}



    pagesize = landscape(A4) if orientation == "landscape" else portrait(A4)

    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \

              else ["Team","Slot","Q-TTR","Name","Note","Status"]



    data = [headers] + [_row_to_list(r) for r in rows]



    doc = SimpleDocTemplate(

        str(out_path),

        pagesize=pagesize,

        leftMargin=margins_pt["left"], rightMargin=margins_pt["right"],

        topMargin=margins_pt["top"], bottomMargin=margins_pt["bottom"]

    )

    styles = getSampleStyleSheet()

    elems = [Paragraph(titel, styles["Title"]),

             Paragraph(datetime.now().strftime("%d.%m.%Y %H:%M"), styles["Normal"]),

             Spacer(0, 6)]



    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),

        ("TEXTCOLOR",  (0,0), (-1,0), colors.black),

        ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),

        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),

        ("FONTSIZE",   (0,0), (-1,-1), fontsize),

        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),

        ("ALIGN", (2,1), (2,-1), "RIGHT"),  # Q-TTR

    ]))

    elems.append(table)

    doc.build(elems)



def print_file(path: Path) -> bool:

    """Versuch, das PDF direkt zu drucken. Rückgabe: True, wenn ein Druckversuch gestartet wurde."""

    try:

        if sys.platform.startswith("win"):

            os.startfile(str(path), "print")  # type: ignore[attr-defined]

            return True

        else:

            for cmd in (["lp", str(path)], ["lpr", str(path)]):

                try:

                    subprocess.run(cmd, check=True)

                    return True

                except Exception:

                    continue

    except Exception:

        logger.exception("Druckversuch fehlgeschlagen")

    return False



# -------------------------------

# GUI

# -------------------------------



class TTRScraperGUI:

    def __init__(self, root: tk.Tk):

        self.root = root

        root.title("click-TT Q-TTR Scraper (Weg 1)")



        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")

        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)

        for i in range(8): frm.columnconfigure(i, weight=1)



        cfg = load_config()

        self.groups: List[Dict[str,str]] = load_groups()

        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))

        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))

        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))

        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))

        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))

        self.var_group_label = tk.StringVar(value=default_label)

        self.var_group_id    = tk.StringVar(value=default_id)

        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))

        self.var_format  = tk.StringVar(value=cfg.get("format","json"))

        self.var_autofetch = tk.BooleanVar(value=cfg.get("autofetch", False))

        self.var_debug = tk.BooleanVar(value=False)

        self.groups_path = get_groups_path_from_config(cfg)



        # --- Zeile: Base-URL

        r = 0

        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")

        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=7, sticky="ew", padx=6, pady=3)



        # --- Zeile: Saison / Runde

        r += 1

        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")

        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)

        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")

        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,

                                      values=["vorrunde", "rueckrunde"], state="readonly")

        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)



        # --- Zeile: Gruppe + ID + Sprache

        r += 1

        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")

        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,

                                      values=self._group_labels(), state="readonly")

        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)

        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)



        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")

        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")

        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)



        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")

        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")

        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)



        # --- Zeile: Datenformat

        r += 1

        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")

        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,

                                       values=["json","csv","markdown","xlsx"], state="readonly")

        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)



        # --- Buttons / Schalter

        r += 1

        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=8, sticky="ew", pady=(6,3))

        for i in range(13): btn_frame.columnconfigure(i, weight=1)



        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",           command=self.on_fetch);        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")

        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",       command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")

        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",            command=self.on_clear);        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")

        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",       command=self.on_settings);     self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")

        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",         command=self.on_groups);       self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")

        self.chk_autof    = ttk.Checkbutton(btn_frame, text="Auto-Abruf beim Gruppenwechsel", variable=self.var_autofetch)

        self.chk_autof.grid(row=0, column=5, padx=4, sticky="w")

        self.btn_browser  = ttk.Button(btn_frame, text="Im Browser öffnen", command=self.on_open_browser); self.btn_browser.grid(row=0, column=6, padx=4, sticky="ew")

        self.lbl_gpath    = ttk.Label(btn_frame, text=f"Gruppen-Datei: {self.groups_path}"); self.lbl_gpath.grid(row=0, column=7, padx=6, sticky="w")

        self.btn_pickpath = ttk.Button(btn_frame, text="Speicherort Gruppen …", command=self.on_pick_groups_path); self.btn_pickpath.grid(row=0, column=8, padx=4, sticky="ew")

        self.btn_print    = ttk.Button(btn_frame, text="Drucken",         command=self.on_print, state="normal"); self.btn_print.grid(row=0, column=9, padx=4, sticky="ew")

        self.btn_cancel   = ttk.Button(btn_frame, text="Abbrechen",         command=self.on_cancel, state="disabled"); self.btn_cancel.grid(row=0, column=10, padx=4, sticky="ew")

        self.chk_debug    = ttk.Checkbutton(btn_frame, text="Debug-Log",    variable=self.var_debug)

        self.chk_debug.grid(row=0, column=11, padx=4, sticky="w")

        self.btn_exit     = ttk.Button(btn_frame, text="Exit", command=self.root.quit)

        self.btn_exit.grid(row=0, column=12, padx=4, sticky="ew")



        # --- Status + Vorschau

        r += 1

        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")

        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=7, sticky="nsew", padx=6, pady=3)



        r += 1

        ttk.Label(frm, text="Vorschau (Spaltenkopf klicken zum Sortieren)").grid(row=r, column=0, sticky="w")

        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=16)

        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:

            self.tree.heading(col, text=text); self.tree.column(col, stretch=True, width=120)

        self.tree.grid(row=r, column=1, columnspan=7, sticky="nsew", padx=6, pady=3)



        frm.rowconfigure(r-1, weight=0)  # status

        frm.rowconfigure(r,   weight=1)  # table



        self.rows: List[Dict] = []

        self._cancel_flag = False



        self._make_treeview_sortable(self.tree)

        self._sync_group_id_to_label()



        # Shortcut nur noch für Speichern

        self.root.bind("<Control-s>", lambda e: self.on_export())



    # -------------------- Helpers --------------------



    def _group_labels(self) -> List[str]: return [g.get("label","") for g in self.groups]

    def _group_map(self) -> Dict[str,str]: return {g.get("label",""): g.get("id","") for g in self.groups}

    def _sync_group_id_to_label(self):

        gid = self._group_map().get(self.var_group_label.get().strip(), "")

        self.var_group_id.set(gid)



    def log(self, msg: str):

        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")

        if self.var_debug.get():

            logger.info(msg)



    def set_busy(self, busy: bool):

        state = "disabled" if busy else "normal"

        self.btn_fetch.config(state=state)

        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))

        self.btn_print.config(state=("normal" if (not busy and self.rows) else "disabled"))

        self.btn_cancel.config(state=("normal" if busy else "disabled"))

        self._cancel_flag = False if busy else self._cancel_flag



    def on_clear(self):

        self.txt_status.delete("1.0", "end")

        for i in self.tree.get_children(): self.tree.delete(i)

        self.rows = []

        self.btn_export.config(state="disabled")

        self.btn_print.config(state="disabled")



    def _make_treeview_sortable(self, tree: ttk.Treeview):

        for col in tree["columns"]:

            tree.heading(col, text=tree.heading(col, "text"),

                         command=lambda c=col: self._sort_by(tree, c, False))



    def _sort_by(self, tree: ttk.Treeview, col: str, descending: bool):

        data = [(tree.set(k, col), k) for k in tree.get_children("")]

        def _num(v):

            try: return float(str(v).replace(",", "."))

            except Exception: return None

        if any(_num(v) is not None for v,_ in data):

            data.sort(key=lambda t: (_num(t[0]) is None, _num(t[0]) or 0.0))

        else:

            data.sort(key=lambda t: str(t[0]).lower())

        if descending: data.reverse()

        for idx, item in enumerate(data): tree.move(item[1], "", idx)

        tree.heading(col, command=lambda: self._sort_by(tree, col, not descending))



    def _render_rows(self, rows: List[Dict]):

        for i in self.tree.get_children(): self.tree.delete(i)

        for r in rows:

            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),

                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))

        self.btn_print.config(state=("normal" if rows else "disabled"))

        self.btn_export.config(state=("normal" if rows else "disabled"))



    # -------------------- Actions --------------------



    def on_group_selected(self, _evt=None):

        self._sync_group_id_to_label()

        if self.var_autofetch.get() and str(self.btn_fetch["state"]) != "disabled":

            self.root.after(80, self.on_fetch)



    def on_open_browser(self):

        base   = self.var_base.get().strip()

        saison = self.var_saison.get().strip()

        runde  = self.var_runde.get().strip()

        label  = self.var_group_label.get().strip()

        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:

            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")

            return

        url = build_url(base, saison, runde, gid)

        webbrowser.open(url)

        self.log(f"Im Browser geöffnet: {url}")



    def on_fetch(self):

        base   = self.var_base.get().strip()

        saison = self.var_saison.get().strip()

        runde  = self.var_runde.get().strip()

        label  = self.var_group_label.get().strip()

        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()



        if not base or not saison or not runde or not gid:

            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")

            return



        url = build_url(base, saison, runde, gid)

        if self.var_debug.get(): logger.info("URL: %s", url)

        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)

        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()



    def on_cancel(self):

        self._cancel_flag = True

        self.log("Abruf wird abgebrochen …")



    def _fetch_thread(self, url: str):

        try:

            html = fetch_html(url)

            if self._cancel_flag:

                self.root.after(0, lambda: self._abort("Abgebrochen."))

                return

            issue = looks_like_login_or_error(html)

            if issue:

                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))

                return

            rows = parse_group_pools(html)

            if self._cancel_flag:

                self.root.after(0, lambda: self._abort("Abgebrochen."))

                return

            if not rows:

                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))

                return

            avgs = self._team_avgs(rows)

            def finish():

                self._update_rows(rows, avgs)

            self.root.after(0, finish)

        except Exception as e:

            if self.var_debug.get():

                logger.exception("Fetch-Thread Fehler")

            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))



    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:

        avgs: Dict[str, Optional[float]] = {}

        teams = sorted({r["team"] for r in rows})

        for t in teams:

            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]

            avgs[t] = (mean(vals) if vals else None)

        return avgs



    def _abort(self, msg: str):

        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled"); self.btn_print.config(state="disabled")



    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):

        self.rows = rows

        self._render_rows(rows)

        self.log(f"{len(rows)} Zeilen geladen.")

        self.log("Team-Mittel (Q-TTR):")

        for t, v in avgs.items():

            self.log(f"  • {t}: {'' if v is None else round(v,1)}")

        self.set_busy(False)



    def on_export(self):

        if not self.rows:

            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return

        fmt = self.var_format.get(); sprache = self.var_sprache.get()

        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "xlsx": ".xlsx"}

        if fmt not in ext_map:

            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return

        path = filedialog.asksaveasfilename(

            title="Speichern unter",

            defaultextension=ext_map[fmt],

            filetypes=[("Excel","*.xlsx"), ("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")]

        )

        if not path: return

        try:

            export_rows(self.rows, fmt, sprache, path)

            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")

        except Exception as e:

            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")



    # -------------------- Druckvorschau --------------------



    def on_print(self):

        if not self.rows:

            messagebox.showinfo("Nichts zu drucken", "Keine Daten geladen."); return



        dlg = tk.Toplevel(self.root); dlg.title("Druckvorschau / Optionen"); dlg.grab_set()

        dlg.geometry("520x260")

        box = ttk.Frame(dlg, padding=10); box.pack(fill="both", expand=True)



        # Felder

        var_title = tk.StringVar(value=f"Q-TTR – {self.var_saison.get()} / {self.var_runde.get()} – {self.var_group_label.get()}")

        var_orient = tk.StringVar(value="landscape")  # 'landscape' | 'portrait'

        var_font   = tk.IntVar(value=8)

        var_open   = tk.BooleanVar(value=True)

        # Ränder (mm)

        var_m_left   = tk.DoubleVar(value=12.0)

        var_m_right  = tk.DoubleVar(value=12.0)

        var_m_top    = tk.DoubleVar(value=12.0)

        var_m_bottom = tk.DoubleVar(value=12.0)



        # Layout

        r = 0

        ttk.Label(box, text="Titel").grid(row=r, column=0, sticky="w")

        ttk.Entry(box, textvariable=var_title).grid(row=r, column=1, columnspan=3, sticky="ew", padx=6, pady=4)



        r += 1

        ttk.Label(box, text="Ausrichtung").grid(row=r, column=0, sticky="w")

        ttk.Radiobutton(box, text="Querformat", variable=var_orient, value="landscape").grid(row=r, column=1, sticky="w")

        ttk.Radiobutton(box, text="Hochformat", variable=var_orient, value="portrait").grid(row=r, column=2, sticky="w")

        ttk.Label(box, text="Schriftgröße").grid(row=r, column=3, sticky="e")

        ttk.Spinbox(box, from_=6, to=12, textvariable=var_font, width=5).grid(row=r, column=4, sticky="w", padx=6)



        r += 1

        ttk.Label(box, text="Ränder (mm)").grid(row=r, column=0, sticky="w")

        ttk.Label(box, text="Links").grid(row=r, column=1, sticky="e")

        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_left, width=6).grid(row=r, column=2, sticky="w")

        ttk.Label(box, text="Rechts").grid(row=r, column=3, sticky="e")

        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_right, width=6).grid(row=r, column=4, sticky="w")



        r += 1

        ttk.Label(box, text="").grid(row=r, column=0, sticky="w")

        ttk.Label(box, text="Oben").grid(row=r, column=1, sticky="e")

        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_top, width=6).grid(row=r, column=2, sticky="w")

        ttk.Label(box, text="Unten").grid(row=r, column=3, sticky="e")

        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_bottom, width=6).grid(row=r, column=4, sticky="w")



        r += 1

        ttk.Checkbutton(box, text="PDF nach Erzeugung öffnen", variable=var_open).grid(row=r, column=0, columnspan=2, sticky="w", pady=(6,0))



        for c in range(5): box.columnconfigure(c, weight=(1 if c in (1,2,4) else 0))



        # Buttons

        btns = ttk.Frame(box); btns.grid(row=r+1, column=0, columnspan=5, sticky="ew", pady=(12,0))

        for i in range(3): btns.columnconfigure(i, weight=1)



        def make_pdf_and(option_print: bool):

            try:

                margins = {

                    "left":   mm_to_pt(var_m_left.get()),

                    "right":  mm_to_pt(var_m_right.get()),

                    "top":    mm_to_pt(var_m_top.get()),

                    "bottom": mm_to_pt(var_m_bottom.get()),

                }

            except Exception:

                messagebox.showerror("Fehler", "Ungültige Randangaben."); return



            out_dir = CONFIG_DIR / "printouts"; out_dir.mkdir(parents=True, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            pdf_path = out_dir / f"qttr_{ts}.pdf"



            try:

                pdf_from_rows(

                    self.rows, pdf_path,

                    titel=var_title.get().strip() or "Q-TTR",

                    sprache=self.var_sprache.get(),

                    orientation=var_orient.get(),

                    fontsize=int(var_font.get()),

                    margins_pt=margins

                )

            except Exception as e:

                if self.var_debug.get(): logger.exception("PDF-Erzeugung fehlgeschlagen")

                messagebox.showerror("Fehler", f"PDF konnte nicht erzeugt werden:\n{e}")

                return



            if option_print:

                attempted = print_file(pdf_path)

                if attempted:

                    self.log(f"Druckauftrag gestartet: {pdf_path}")

                    dlg.destroy()

                else:

                    webbrowser.open(str(pdf_path))

                    self.log(f"PDF geöffnet (zum manuellen Drucken): {pdf_path}")

                    dlg.destroy()

            else:

                # Nur speichern/öffnen

                if var_open.get():

                    webbrowser.open(str(pdf_path))

                self.log(f"PDF erzeugt: {pdf_path}")

                dlg.destroy()



        ttk.Button(btns, text="Als PDF erzeugen", command=lambda: make_pdf_and(False)).grid(row=0, column=0, padx=6, sticky="ew")

        ttk.Button(btns, text="Direkt drucken",   command=lambda: make_pdf_and(True)).grid(row=0, column=1, padx=6, sticky="ew")

        ttk.Button(btns, text="Abbrechen",        command=dlg.destroy).grid(row=0, column=2, padx=6, sticky="ew")



    # -------------------- Gruppen/Settings --------------------



    def on_pick_groups_path(self):

        initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)

        initial_file = self.groups_path.name if self.groups_path else "gruppen.json"

        chosen = filedialog.asksaveasfilename(

            title="Speicherort für gruppen.json wählen",

            initialdir=initial_dir, initialfile=initial_file,

            defaultextension=".json",

            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]

        )

        if not chosen: return

        new_path = _normalize_path(chosen)

        try:

            if Path(new_path).exists():

                data = json.loads(Path(new_path).read_text(encoding="utf-8"))

                if isinstance(data, list):

                    self.groups = data

            else:

                save_groups(self.groups, new_path)

        except Exception as e:

            messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")

            return

        self.groups_path = new_path

        cfg = load_config(); cfg["groups_path"] = str(new_path); save_config(cfg)

        self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")

        self._refresh_group_dropdown()



    def on_settings(self):

        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):

            cfg = load_config()

            cfg.update({

                "base": self.var_base.get(),

                "saison": self.var_saison.get(),

                "runde": self.var_runde.get(),

                "group_label": self.var_group_label.get(),

                "group": self.var_group_id.get(),

                "sprache": self.var_sprache.get(),

                "format": self.var_format.get(),

                "autofetch": self.var_autofetch.get(),

                "groups_path": str(self.groups_path),

            })

            try:

                save_config(cfg)

                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")

            except Exception as e:

                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")



    def on_groups(self):

        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()

        dlg.geometry("620x420")

        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)

        cols = ("label","id")

        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)

        tree.heading("label", text="Bezeichnung"); tree.heading("id", text="Group-ID")

        tree.column("label", stretch=True, width=360); tree.column("id", stretch=False, width=140)

        tree.pack(fill="both", expand=True, pady=(0,8))



        path_frame = ttk.Frame(container); path_frame.pack(fill="x", pady=(0,8))

        lbl = ttk.Label(path_frame, text=f"Datei: {self.groups_path}"); lbl.pack(side="left", padx=(0,6))

        def pick_path():

            initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)

            initial_file = self.groups_path.name if self.groups_path else "gruppen.json"

            chosen = filedialog.asksaveasfilename(

                title="Speicherort für gruppen.json wählen",

                initialdir=initial_dir, initialfile=initial_file,

                defaultextension=".json",

                filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]

            )

            if not chosen: return

            new_path = _normalize_path(chosen)

            try:

                if Path(new_path).exists():

                    data = json.loads(Path(new_path).read_text(encoding="utf-8"))

                    if isinstance(data, list):

                        self.groups = data

                else:

                    save_groups(self.groups, new_path)

            except Exception as e:

                messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")

                return

            self.groups_path = new_path

            cfg = load_config(); cfg["groups_path"] = str(new_path); save_config(cfg)

            lbl.config(text=f"Datei: {self.groups_path}")

            self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")

            refresh_tree(); self._refresh_group_dropdown()

        ttk.Button(path_frame, text="Speicherort wählen …", command=pick_path).pack(side="left")



        form = ttk.Frame(container); form.pack(fill="x", pady=4)

        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")

        var_label = tk.StringVar(); ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")

        var_id = tk.StringVar(); ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)

        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))



        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))

        def refresh_tree():

            for i in tree.get_children(): tree.delete(i)

            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))

        def select_from_tree(_evt=None):

            sel = tree.selection()

            if not sel: return

            vals = tree.item(sel[0], "values"); var_label.set(vals[0]); var_id.set(vals[1])

        def add_or_update():

            label = var_label.get().strip(); gid = var_id.get().strip()

            if not label or not gid:

                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return

            if not gid.isdigit():

                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"): return

            for g in self.groups:

                if g.get("label","") == label:

                    g["id"] = gid; break

            else:

                self.groups.append({"label": label, "id": gid})

            save_groups(self.groups, self.groups_path)

            refresh_tree(); self._refresh_group_dropdown()

        def delete_selected():

            sel = tree.selection()

            if not sel: return

            label = tree.item(sel[0], "values")[0]

            self.groups = [g for g in self.groups if g.get("label","") != label]

            save_groups(self.groups, self.groups_path)

            refresh_tree(); self._refresh_group_dropdown()

        def close_dialog():

            if self.var_group_label.get() not in self._group_labels():

                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")

            self._sync_group_id_to_label()

            try:

                self._save_current_config()

                dlg.destroy()

            except Exception as e:

                messagebox.showerror("Fehler", f"Konnte Konfiguration nicht speichern:\n{e}")

        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)

        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)

        ttk.Button(btns, text="Schließen", command=close_dialog).pack(side="right", padx=4)



        tree.bind("<<TreeviewSelect>>", select_from_tree)

        refresh_tree()



    def _refresh_group_dropdown(self):

        self.cmb_group.config(values=self._group_labels())

        if self.var_group_label.get() not in self._group_labels() and self._group_labels():

            self.var_group_label.set(self._group_labels()[0])

        self._sync_group_id_to_label()



    def _save_current_config(self):

        config = load_config()

        config.update({

            "base": self.var_base.get(),

            "saison": self.var_saison.get(),

            "runde": self.var_runde.get(),

            "group_label": self.var_group_label.get(),

            "group": self.var_group_id.get(),

            "sprache": self.var_sprache.get(),

            "format": self.var_format.get(),

            "autofetch": bool(self.var_autofetch.get()),

            "groups_path": str(self.groups_path),

        })

        save_config(config)



def main():

    root = tk.Tk()

    try:

        if sys.platform.startswith("win"):

            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore

    except Exception:

        pass

    # Fenster immer maximiert öffnen

    root.state('zoomed')  # Maximiert unter Windows

    # root.attributes('-zoomed', True)  # Für Linux/Unix (optional)

    app = TTRScraperGUI(root)

    root.mainloop()



if __name__ == "__main__":

    main()

### 40. Assistent

Nice! Saubere v1.8-Basis. Ich schiebe dir einen kleinen Qualitäts-Patch rüber: robustere Parser-Fallbacks, korrekter Initialzustand des Druck-Buttons, sauberes Beenden, Cross-Platform Maximierung, schnellere Spaltenerkennung für „Q-TTR“, Kontextmenü „Zeile kopieren“, und Shortcuts. Dazu ein kurzer Commit-Text.

# Patch (gezielte Änderungen)

## 1) BeautifulSoup robust machen (lxml-Fallback)
**Neu einfügen (ganz oben bei den Helpers, nach `SESSION = make_session()`):**
```python
def _mk_soup(html: str):
    # Robuster Parser: bevorzugt lxml, fällt auf html.parser zurück
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")
```

**Ersetze in `looks_like_login_or_error` und `parse_group_pools`:**
```python
- soup = BeautifulSoup(html, "lxml")
+ soup = _mk_soup(html)
```

## 2) Q-TTR-Spalte toleranter erkennen
**Hilfsfunktion direkt über `parse_group_pools` einfügen:**
```python
def _is_qttr_header(h: str) -> bool:
    h = re.sub(r"\W+", "", (h or "").lower())
    return h in {"qttr", "qttrwert", "qttrpunkte", "qttrwertet", "qttrwerten"} or "qttr" in h
```

**Im `parse_group_pools` ersetzen:**
```python
- idx_qttr = next(i for i, h in enumerate(headers) if "q-ttr" in h or "qttr" in h)
+ idx_qttr = next(i for i, h in enumerate(headers) if _is_qttr_header(h))
```

## 3) Druck-Button initial deaktivieren
**Im Konstruktor (Button-Zeile) ändern:**
```python
- self.btn_print    = ttk.Button(btn_frame, text="Drucken",         command=self.on_print, state="normal"); self.btn_print.grid(row=0, column=9, padx=4, sticky="ew")
+ self.btn_print    = ttk.Button(btn_frame, text="Drucken",         command=self.on_print, state="disabled"); self.btn_print.grid(row=0, column=9, padx=4, sticky="ew")
```

## 4) Exit sauber schließen
**Im Konstruktor die Exit-Action ändern:**
```python
- self.btn_exit     = ttk.Button(btn_frame, text="Exit", command=self.root.quit)
+ self.btn_exit     = ttk.Button(btn_frame, text="Exit", command=self.root.destroy)
```

## 5) Fenster plattformfreundlich maximieren
**`main()` anpassen:**
```python
def main():
    root = tk.Tk()
    try:
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass

    # Cross-Platform "maximiert"
    try:
        if sys.platform.startswith("win"):
            root.state('zoomed')
        elif sys.platform == "darwin":
            root.attributes('-zoomed', True)  # funktioniert je nach Tk-Version
        else:
            root.attributes('-zoomed', True)
    except Exception:
        root.geometry("1200x700")

    app = TTRScraperGUI(root)
    root.mainloop()
```
*(Deine bisherige Windows-Zeile ist ok; das obige macht’s nur universeller.)*

## 6) Kontextmenü: Zeile kopieren
**Im Konstruktor nach `self._make_treeview_sortable(self.tree)` einfügen:**
```python
self._make_tree_context_menu()
```

**Unter „Helpers“ ergänzen:**
```python
def _make_tree_context_menu(self):
    menu = tk.Menu(self.root, tearoff=0)
    menu.add_command(label="Zeile kopieren", command=self._copy_selected_row)
    def _popup(e):
        iid = self.tree.identify_row(e.y)
        if iid:
            self.tree.selection_set(iid)
            menu.tk_popup(e.x_root, e.y_root)
    self.tree.bind("<Button-3>", _popup)

def _copy_selected_row(self):
    sel = self.tree.selection()
    if not sel:
        return
    vals = self.tree.item(sel[0], "values")
    try:
        self.root.clipboard_clear()
        self.root.clipboard_append("\t".join(str(v) for v in vals))
        self.log("Zeile in die Zwischenablage kopiert.")
    except Exception:
        pass
```

## 7) Nützliche Shortcuts
**Im Konstruktor (wo du `<Control-s>` bindest) ergänzen:**
```python
self.root.bind("<Control-p>", lambda e: self.on_print())
self.root.bind("<Escape>",    lambda e: self.on_cancel() if str(self.btn_cancel['state']) == 'normal' else None)
```

# Commit-Text (Deutsch)
```text
chore(gui): Parser-Fallback, Q-TTR-Erkennung, UX-Feinschliff und sauberes Beenden

- Parser robuster: bevorzugt lxml, fällt auf html.parser zurück (keine Abhängigkeitshärte)
- Q-TTR-Spalte toleranter erkannt (normalisierte Header; „qttr“-Varianten)
- Druck-Button initial deaktiviert; wird erst nach Datenabruf aktiv
- Exit schließt Fenster zuverlässig via root.destroy
- Fenster-Maximierung plattformfreundlich (Windows zoomed, sonst -zoomed Fallback)
- Kontextmenü im Grid: „Zeile kopieren“ in Zwischenablage (TSV)
- Shortcuts: Ctrl+P (Drucken), Esc (Abruf abbrechen, wenn aktiv)

Hinweis:
- Optional `pip install lxml` für schnelle BeautifulSoup-Parsing-Performance.
```

# Optional: Abhängigkeiten
Falls du lxml wirklich nutzen willst (schneller Parser), pack’s in dein Setup:
```bash
pip install lxml
```

Wenn du noch Seitennummern und Vereinslogo im PDF willst, setze ich dir im `pdf_from_rows` einen `onFirstPage/onLaterPages`-Canvas-Callback auf.

### 41. Benutzer

alles außer optional Abhängigkeiten implementieren. zum schluss einen completten commit-text in deutsch erstellen

### 42. Assistent

Alles klar — hier ist deine überarbeitete **v1.8+** mit allen gewünschten Verbesserungen umgesetzt (ohne zusätzliche optionale Abhängigkeiten). Direkt darunter findest du einen vollständigen Commit-Text auf Deutsch.

---

## `ttr_gui.py`
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
click-TT Q-TTR Scraper (Weg 1, groupPools) – GUI v1.8+

Neu (dieser Patch):
- Robuster HTML-Parser mit Fallback (_mk_soup): nutzt lxml, fällt sonst auf html.parser zurück
- Tolerantere Erkennung der Q-TTR-Spalte (_is_qttr_header)
- Druck-Button initial deaktiviert; wird erst nach Datenabruf aktiv
- Exit beendet sauber mit root.destroy
- Cross-Platform-Maximierung (Windows: zoomed; macOS/Linux: -zoomed Fallback; sonst feste Größe)
- Kontextmenü für Tabelle: „Zeile kopieren“ (TSV in Zwischenablage)
- Shortcuts: Ctrl+P (Drucken), Esc (Abruf abbrechen, wenn aktiv)

Bestehendes:
- Frei wählbarer Speicherort für gruppen.json (Pfad in config.json: groups_path)
- Robustes HTTP (Retries + Cache)
- Sortierbare Tabelle
- XLSX-Export mit Blatt "Stats" (Team-Aggregate + Top-10)
- Gruppen-Pulldown + Konfig-Dialog (Label->ID)
- Rotierendes Log + Debug-Schalter
- "Im Browser öffnen" + optionaler Auto-Abruf beim Gruppenwechsel
- Abbrechen-Button für laufende Abrufe
- Druckvorschau/Optionen (PDF/Print)
"""

import csv
import json
import re
import sys
import threading
from statistics import mean
from typing import Dict, List, Optional
from urllib.parse import quote
from pathlib import Path
import webbrowser
import os
import subprocess
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests_cache
from bs4 import BeautifulSoup
from openpyxl import Workbook
from platformdirs import PlatformDirs

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Logging (rotierendes Log) ------------------------------------------------
import logging
from logging.handlers import RotatingFileHandler

APP_NAME, APP_AUTHOR = "ttrscraper", "ttc"
_dirs = PlatformDirs(APP_NAME, APP_AUTHOR)
CONFIG_DIR  = Path(_dirs.user_config_path); CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_GROUPS_PATH = CONFIG_DIR / "gruppen.json"
LOG_PATH = CONFIG_DIR / "ttrscraper.log"

logger = logging.getLogger("ttr")
logger.setLevel(logging.INFO)
_handler = RotatingFileHandler(LOG_PATH, maxBytes=512_000, backupCount=3, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
if not logger.handlers:
    logger.addHandler(_handler)

# -------------------------------
# Config / Gruppen
# -------------------------------

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("config.json kann nicht gelesen werden")
    return {}

def _normalize_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).absolute()

def get_groups_path_from_config(cfg: Optional[dict] = None) -> Path:
    if cfg is None:
        cfg = load_config()
    p = cfg.get("groups_path")
    if p:
        try:
            return _normalize_path(p)
        except Exception:
            return DEFAULT_GROUPS_PATH
    return DEFAULT_GROUPS_PATH

def save_groups(groups: List[Dict[str, str]], path: Optional[Path] = None):
    if path is None:
        path = get_groups_path_from_config()
    cleaned, seen = [], set()
    for g in groups:
        label = (g.get("label") or "").strip()
        gid   = (g.get("id") or "").strip()
        if not label or not gid:
            continue
        key = (label.lower(), gid)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"label": label, "id": gid})
    cleaned.sort(key=lambda x: x["label"].lower())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")

def load_groups(default: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    cfg = load_config()
    groups_path = get_groups_path_from_config(cfg)
    if groups_path.exists():
        try:
            data = json.loads(groups_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            logger.exception("gruppen.json kann nicht gelesen werden")
    # Migration / Default
    if isinstance(cfg.get("groups"), list) and cfg["groups"]:
        save_groups(cfg["groups"], groups_path)
        return cfg["groups"]
    if default is None:
        default = [{"label": "Kreisliga C2", "id": "494514"}]
    save_groups(default, groups_path)
    return default

# -------------------------------
# HTTP: Session mit Retry + Cache
# -------------------------------

def make_session() -> requests.Session:
    s = requests_cache.CachedSession(
        cache_name=str(CONFIG_DIR / "http_cache"),
        expire_after=1800, allowable_methods=("GET",), stale_if_error=True
    )
    retry = Retry(total=3, backoff_factor=0.8,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET"]))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter); s.mount("http://", adapter)
    s.headers.update({
        "User-Agent": "ttr-gui/1.8 (+https://example.org/bot-info)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5"
    })
    return s

SESSION = make_session()

# -------------------------------
# Soup/Parser-Helper
# -------------------------------

def _mk_soup(html: str):
    """Robuster Parser: versucht lxml, fällt auf html.parser zurück."""
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")

def _is_qttr_header(h: str) -> bool:
    """Tolerante Erkennung verschiedener QTTR-Header-Schreibweisen."""
    h_norm = re.sub(r"\W+", "", (h or "").lower())
    return ("qttr" in h_norm) or h_norm in {"qttr", "qttrwert", "qttrpunkte"}

# -------------------------------
# Scraping-Logik (Weg 1)
# -------------------------------

def build_url(base_url: str, saison: str, runde: str, group_id: str) -> str:
    base = base_url.rstrip("/")
    return (f"{base}/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPools"
            f"?championship={quote(saison)}&displayTyp={runde}&group={group_id}")

def fetch_html(url: str, timeout: int = 30) -> str:
    resp = SESSION.get(url, timeout=timeout); resp.raise_for_status()
    return resp.text

def looks_like_login_or_error(html: str) -> Optional[str]:
    soup = _mk_soup(html)
    text = soup.get_text(" ", strip=True).lower()
    for h in ["anmeldung", "login", "zugriff verweigert", "nicht berechtigt",
              "session abgelaufen", "access denied", "forbidden"]:
        if h in text: return h
    if not soup.find("table"): return "keine tabellen gefunden"
    return None

def parse_group_pools(html: str) -> List[Dict]:
    soup = _mk_soup(html)
    results: List[Dict] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        team = heading.get_text(strip=True)
        if not team:
            continue
        table = heading.find_next(lambda tag: tag.name == "table" and tag.find("thead"))
        if not table:
            continue
        headers = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        try:
            idx_qttr = next(i for i, h in enumerate(headers) if _is_qttr_header(h))
        except StopIteration:
            continue
        idx_rang = next((i for i, h in enumerate(headers) if h.startswith("rang") or h.startswith("pos")), None)
        idx_name = next((i for i, h in enumerate(headers) if "name" in h), None)
        for row in table.select("tbody tr"):
            cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cols or len(cols) <= idx_qttr:
                continue
            qttr_raw = cols[idx_qttr]
            qttr_num = re.sub(r"[^\d\-]", "", qttr_raw)
            qttr_val = int(qttr_num) if qttr_num.isdigit() else None
            rang_val = cols[idx_rang] if (idx_rang is not None and idx_rang < len(cols)) else ""
            name_val = cols[idx_name] if (idx_name is not None and idx_name < len(cols)) else ""
            extra = {}
            if len(cols) >= 4: extra["anmerkung"] = cols[3]
            if len(cols) >= 5: extra["status"] = cols[4]
            item = {"team": team, "rang": rang_val, "qttr": qttr_val, "name": name_val, **extra}
            if item["name"] or item["qttr"] is not None:
                results.append(item)
    return results

# -------------------------------
# Export (JSON/CSV/MD/XLSX)
# -------------------------------

def _row_to_list(r: Dict) -> List:
    return [r.get("team",""), r.get("rang",""), r.get("qttr",""),
            r.get("name",""), r.get("anmerkung",""), r.get("status","")]

def _compute_team_stats(rows: List[Dict]) -> List[Dict]:
    stats = []
    teams = sorted({r["team"] for r in rows})
    for t in teams:
        vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
        if not vals:
            stats.append({"Team": t, "Anzahl": 0, "Ø Q-TTR": None, "Min": None, "Max": None})
        else:
            stats.append({"Team": t, "Anzahl": len(vals), "Ø Q-TTR": round(mean(vals), 1),
                          "Min": min(vals), "Max": max(vals)})
    return stats

def _top_n(rows: List[Dict], n: int = 10) -> List[Dict]:
    valids = [r for r in rows if isinstance(r.get("qttr"), int)]
    valids.sort(key=lambda r: r["qttr"], reverse=True)
    out = []
    for i, r in enumerate(valids[:n], 1):
        out.append({"#": i, "Name": r.get("name",""), "Team": r.get("team",""), "Q-TTR": r.get("qttr")})
    return out

def export_xlsx(rows: List[Dict], path: str, sprache: str):
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]
    wb = Workbook()
    ws = wb.active; ws.title = "Q-TTR"
    ws.append(headers)
    for r in rows: ws.append(_row_to_list(r))
    for col in ws.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(10, maxlen + 2), 40)
    ws2 = wb.create_sheet("Stats")
    ws2.append(["Team","Anzahl","Ø Q-TTR","Min","Max"])
    for s in _compute_team_stats(rows):
        ws2.append([s["Team"], s["Anzahl"], s["Ø Q-TTR"], s["Min"], s["Max"]])
    ws2.append([]); ws2.append(["Top-10 (Liga)"]); ws2.append(["#","Name","Team","Q-TTR"])
    for t in _top_n(rows, 10):
        ws2.append([t["#"], t["Name"], t["Team"], t["Q-TTR"]])
    for col in ws2.columns:
        maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws2.column_dimensions[col[0].column_letter].width = min(max(8, maxlen + 2), 40)
    wb.save(path)

def export_rows(rows: List[Dict], datenformat: str, sprache: str, path: str) -> None:
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]
    if datenformat == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif datenformat == "csv":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(headers)
            for r in rows: w.writerow(_row_to_list(r))
    elif datenformat == "markdown":
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for r in rows: f.write("| " + " | ".join("" if v is None else str(v) for v in _row_to_list(r)) + " |\n")
    elif datenformat == "xlsx":
        export_xlsx(rows, path, sprache)
    else:
        raise ValueError(f"Unbekanntes Datenformat: {datenformat}")

# -------------------------------
# Drucken (PDF erzeugen + OS-Print)
# -------------------------------

def mm_to_pt(mm: float) -> float:
    return mm * 72.0 / 25.4

def pdf_from_rows(rows: List[Dict], out_path: Path, titel: str = "Q-TTR Ergebnisse",
                  sprache: str = "de", orientation: str = "landscape",
                  fontsize: int = 8, margins_pt: Dict[str, float] = None):
    from reportlab.lib.pagesizes import A4, landscape, portrait
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    if margins_pt is None:
        margins_pt = {"left": 18, "right": 18, "top": 18, "bottom": 18}

    pagesize = landscape(A4) if orientation == "landscape" else portrait(A4)
    headers = ["Team","Rang","Q-TTR","Name","Anmerkung","Status"] if sprache.lower().startswith("de") \
              else ["Team","Slot","Q-TTR","Name","Note","Status"]

    data = [headers] + [_row_to_list(r) for r in rows]

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=pagesize,
        leftMargin=margins_pt["left"], rightMargin=margins_pt["right"],
        topMargin=margins_pt["top"], bottomMargin=margins_pt["bottom"]
    )
    styles = getSampleStyleSheet()
    elems = [Paragraph(titel, styles["Title"]),
             Paragraph(datetime.now().strftime("%d.%m.%Y %H:%M"), styles["Normal"]),
             Spacer(0, 6)]

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.black),
        ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), fontsize),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ("ALIGN", (2,1), (2,-1), "RIGHT"),  # Q-TTR
    ]))
    elems.append(table)
    doc.build(elems)

def print_file(path: Path) -> bool:
    """Versuch, das PDF direkt zu drucken. Rückgabe: True, wenn ein Druckversuch gestartet wurde."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path), "print")  # type: ignore[attr-defined]
            return True
        else:
            for cmd in (["lp", str(path)], ["lpr", str(path)]):
                try:
                    subprocess.run(cmd, check=True)
                    return True
                except Exception:
                    continue
    except Exception:
        logger.exception("Druckversuch fehlgeschlagen")
    return False

# -------------------------------
# GUI
# -------------------------------

class TTRScraperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("click-TT Q-TTR Scraper (Weg 1)")

        frm = ttk.Frame(root, padding=12); frm.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        for i in range(8): frm.columnconfigure(i, weight=1)

        cfg = load_config()
        self.groups: List[Dict[str,str]] = load_groups()
        self.var_base    = tk.StringVar(value=cfg.get("base",   "https://ttbw.click-tt.de"))
        self.var_saison  = tk.StringVar(value=cfg.get("saison", "TTBW 2025/26"))
        self.var_runde   = tk.StringVar(value=cfg.get("runde",  "vorrunde"))
        default_label = cfg.get("group_label", (self.groups[0]["label"] if self.groups else ""))
        default_id    = cfg.get("group",       (self.groups[0]["id"]    if self.groups else ""))
        self.var_group_label = tk.StringVar(value=default_label)
        self.var_group_id    = tk.StringVar(value=default_id)
        self.var_sprache = tk.StringVar(value=cfg.get("sprache","de"))
        self.var_format  = tk.StringVar(value=cfg.get("format","json"))
        self.var_autofetch = tk.BooleanVar(value=cfg.get("autofetch", False))
        self.var_debug = tk.BooleanVar(value=False)
        self.groups_path = get_groups_path_from_config(cfg)

        # --- Zeile: Base-URL
        r = 0
        ttk.Label(frm, text="Base-URL (Verband)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_base).grid(row=r, column=1, columnspan=7, sticky="ew", padx=6, pady=3)

        # --- Zeile: Saison / Runde
        r += 1
        ttk.Label(frm, text="Saison (genau wie in URL)").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_saison).grid(row=r, column=1, columnspan=2, sticky="ew", padx=6, pady=3)
        ttk.Label(frm, text="Runde").grid(row=r, column=3, sticky="e")
        self.cmb_runde = ttk.Combobox(frm, textvariable=self.var_runde,
                                      values=["vorrunde", "rueckrunde"], state="readonly")
        self.cmb_runde.grid(row=r, column=4, sticky="ew", padx=6)

        # --- Zeile: Gruppe + ID + Sprache
        r += 1
        ttk.Label(frm, text="Gruppe").grid(row=r, column=0, sticky="w")
        self.cmb_group = ttk.Combobox(frm, textvariable=self.var_group_label,
                                      values=self._group_labels(), state="readonly")
        self.cmb_group.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
        self.cmb_group.bind("<<ComboboxSelected>>", self.on_group_selected)

        ttk.Label(frm, text="Group-ID").grid(row=r, column=2, sticky="e")
        self.ent_group_id = ttk.Entry(frm, textvariable=self.var_group_id, state="readonly")
        self.ent_group_id.grid(row=r, column=3, sticky="ew", padx=6)

        ttk.Label(frm, text="Sprache").grid(row=r, column=4, sticky="e")
        self.cmb_sprache = ttk.Combobox(frm, textvariable=self.var_sprache, values=["de","en"], state="readonly")
        self.cmb_sprache.grid(row=r, column=5, sticky="ew", padx=6)

        # --- Zeile: Datenformat
        r += 1
        ttk.Label(frm, text="Datenformat").grid(row=r, column=0, sticky="w")
        self.cmb_format = ttk.Combobox(frm, textvariable=self.var_format,
                                       values=["json","csv","markdown","xlsx"], state="readonly")
        self.cmb_format.grid(row=r, column=1, sticky="ew", padx=6)

        # --- Buttons / Schalter
        r += 1
        btn_frame = ttk.Frame(frm); btn_frame.grid(row=r, column=0, columnspan=8, sticky="ew", pady=(6,3))
        for i in range(13): btn_frame.columnconfigure(i, weight=1)

        self.btn_fetch    = ttk.Button(btn_frame, text="Abrufen",           command=self.on_fetch);        self.btn_fetch.grid(row=0, column=0, padx=4, sticky="ew")
        self.btn_export   = ttk.Button(btn_frame, text="Speichern …",       command=self.on_export, state="disabled"); self.btn_export.grid(row=0, column=1, padx=4, sticky="ew")
        self.btn_clear    = ttk.Button(btn_frame, text="Leeren",            command=self.on_clear);        self.btn_clear.grid(row=0, column=2, padx=4, sticky="ew")
        self.btn_settings = ttk.Button(btn_frame, text="Einstellung",       command=self.on_settings);     self.btn_settings.grid(row=0, column=3, padx=4, sticky="ew")
        self.btn_groups   = ttk.Button(btn_frame, text="Gruppen …",         command=self.on_groups);       self.btn_groups.grid(row=0, column=4, padx=4, sticky="ew")
        self.chk_autof    = ttk.Checkbutton(btn_frame, text="Auto-Abruf beim Gruppenwechsel", variable=self.var_autofetch)
        self.chk_autof.grid(row=0, column=5, padx=4, sticky="w")
        self.btn_browser  = ttk.Button(btn_frame, text="Im Browser öffnen", command=self.on_open_browser); self.btn_browser.grid(row=0, column=6, padx=4, sticky="ew")
        self.lbl_gpath    = ttk.Label(btn_frame, text=f"Gruppen-Datei: {self.groups_path}"); self.lbl_gpath.grid(row=0, column=7, padx=6, sticky="w")
        self.btn_pickpath = ttk.Button(btn_frame, text="Speicherort Gruppen …", command=self.on_pick_groups_path); self.btn_pickpath.grid(row=0, column=8, padx=4, sticky="ew")
        self.btn_print    = ttk.Button(btn_frame, text="Drucken",           command=self.on_print, state="disabled"); self.btn_print.grid(row=0, column=9,  padx=4, sticky="ew")
        self.btn_cancel   = ttk.Button(btn_frame, text="Abbrechen",         command=self.on_cancel, state="disabled"); self.btn_cancel.grid(row=0, column=10, padx=4, sticky="ew")
        self.chk_debug    = ttk.Checkbutton(btn_frame, text="Debug-Log",    variable=self.var_debug)
        self.chk_debug.grid(row=0, column=11, padx=4, sticky="w")
        self.btn_exit     = ttk.Button(btn_frame, text="Exit", command=self.root.destroy)
        self.btn_exit.grid(row=0, column=12, padx=4, sticky="ew")

        # --- Status + Vorschau
        r += 1
        ttk.Label(frm, text="Status").grid(row=r, column=0, sticky="w")
        self.txt_status = tk.Text(frm, height=5, wrap="word"); self.txt_status.grid(row=r, column=1, columnspan=7, sticky="nsew", padx=6, pady=3)

        r += 1
        ttk.Label(frm, text="Vorschau (Spaltenkopf klicken zum Sortieren)").grid(row=r, column=0, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("team","rang","qttr","name","anmerkung","status"), show="headings", height=16)
        for col, text in [("team","Team"),("rang","Rang"),("qttr","Q-TTR"),("name","Name"),("anmerkung","Anmerkung"),("status","Status")]:
            self.tree.heading(col, text=text); self.tree.column(col, stretch=True, width=120)
        self.tree.grid(row=r, column=1, columnspan=7, sticky="nsew", padx=6, pady=3)

        frm.rowconfigure(r-1, weight=0)  # status
        frm.rowconfigure(r,   weight=1)  # table

        self.rows: List[Dict] = []
        self._cancel_flag = False

        self._make_treeview_sortable(self.tree)
        self._make_tree_context_menu()
        self._sync_group_id_to_label()

        # Shortcuts
        self.root.bind("<Control-s>", lambda e: self.on_export())
        self.root.bind("<Control-p>", lambda e: self.on_print())
        self.root.bind("<Escape>",    lambda e: self.on_cancel() if str(self.btn_cancel['state']) == 'normal' else None)

    # -------------------- Helpers --------------------

    def _group_labels(self) -> List[str]: return [g.get("label","") for g in self.groups]
    def _group_map(self) -> Dict[str,str]: return {g.get("label",""): g.get("id","") for g in self.groups}
    def _sync_group_id_to_label(self):
        gid = self._group_map().get(self.var_group_label.get().strip(), "")
        self.var_group_id.set(gid)

    def log(self, msg: str):
        self.txt_status.insert("end", msg + "\n"); self.txt_status.see("end")
        if self.var_debug.get():
            logger.info(msg)

    def set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        self.btn_export.config(state=("normal" if (not busy and self.rows) else "disabled"))
        self.btn_print.config(state=("normal" if (not busy and self.rows) else "disabled"))
        self.btn_cancel.config(state=("normal" if busy else "disabled"))
        self._cancel_flag = False if busy else self._cancel_flag

    def on_clear(self):
        self.txt_status.delete("1.0", "end")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.rows = []
        self.btn_export.config(state="disabled")
        self.btn_print.config(state="disabled")

    def _make_treeview_sortable(self, tree: ttk.Treeview):
        for col in tree["columns"]:
            tree.heading(col, text=tree.heading(col, "text"),
                         command=lambda c=col: self._sort_by(tree, c, False))

    def _sort_by(self, tree: ttk.Treeview, col: str, descending: bool):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        def _num(v):
            try: return float(str(v).replace(",", "."))
            except Exception: return None
        if any(_num(v) is not None for v,_ in data):
            data.sort(key=lambda t: (_num(t[0]) is None, _num(t[0]) or 0.0))
        else:
            data.sort(key=lambda t: str(t[0]).lower())
        if descending: data.reverse()
        for idx, item in enumerate(data): tree.move(item[1], "", idx)
        tree.heading(col, command=lambda: self._sort_by(tree, col, not descending))

    def _render_rows(self, rows: List[Dict]):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r.get("team",""), r.get("rang",""), r.get("qttr",""),
                                                r.get("name",""), r.get("anmerkung",""), r.get("status","")))
        self.btn_print.config(state=("normal" if rows else "disabled"))
        self.btn_export.config(state=("normal" if rows else "disabled"))

    def _make_tree_context_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Zeile kopieren", command=self._copy_selected_row)
        def _popup(e):
            iid = self.tree.identify_row(e.y)
            if iid:
                self.tree.selection_set(iid)
                menu.tk_popup(e.x_root, e.y_root)
        self.tree.bind("<Button-3>", _popup)

    def _copy_selected_row(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append("\t".join(str(v) for v in vals))
            self.log("Zeile in die Zwischenablage kopiert.")
        except Exception:
            pass

    # -------------------- Actions --------------------

    def on_group_selected(self, _evt=None):
        self._sync_group_id_to_label()
        if self.var_autofetch.get() and str(self.btn_fetch["state"]) != "disabled":
            self.root.after(80, self.on_fetch)

    def on_open_browser(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()
        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return
        url = build_url(base, saison, runde, gid)
        webbrowser.open(url)
        self.log(f"Im Browser geöffnet: {url}")

    def on_fetch(self):
        base   = self.var_base.get().strip()
        saison = self.var_saison.get().strip()
        runde  = self.var_runde.get().strip()
        label  = self.var_group_label.get().strip()
        gid    = self._group_map().get(label, "").strip() or self.var_group_id.get().strip()

        if not base or not saison or not runde or not gid:
            messagebox.showwarning("Eingabe fehlt", "Bitte Base-URL, Saison, Runde und Gruppe/ID angeben.")
            return

        url = build_url(base, saison, runde, gid)
        if self.var_debug.get(): logger.info("URL: %s", url)
        self.on_clear(); self.log(f"Abruf: {url}"); self.set_busy(True)
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def on_cancel(self):
        self._cancel_flag = True
        self.log("Abruf wird abgebrochen …")

    def _fetch_thread(self, url: str):
        try:
            html = fetch_html(url)
            if self._cancel_flag:
                self.root.after(0, lambda: self._abort("Abgebrochen."))
                return
            issue = looks_like_login_or_error(html)
            if issue:
                self.root.after(0, lambda: self._abort(f"Seite wirkt gesperrt/unerwartet: {issue}."))
                return
            rows = parse_group_pools(html)
            if self._cancel_flag:
                self.root.after(0, lambda: self._abort("Abgebrochen."))
                return
            if not rows:
                self.root.after(0, lambda: self._abort("Keine Q-TTR-Daten gefunden (prüfe Saison/Runde/Gruppe)."))
                return
            avgs = self._team_avgs(rows)
            def finish():
                self._update_rows(rows, avgs)
            self.root.after(0, finish)
        except Exception as e:
            if self.var_debug.get():
                logger.exception("Fetch-Thread Fehler")
            self.root.after(0, lambda: self._abort(f"Fehler: {e}"))

    def _team_avgs(self, rows: List[Dict]) -> Dict[str, Optional[float]]:
        avgs: Dict[str, Optional[float]] = {}
        teams = sorted({r["team"] for r in rows})
        for t in teams:
            vals = [r["qttr"] for r in rows if r["team"] == t and isinstance(r["qttr"], int)]
            avgs[t] = (mean(vals) if vals else None)
        return avgs

    def _abort(self, msg: str):
        self.log(msg); self.set_busy(False); self.btn_export.config(state="disabled"); self.btn_print.config(state="disabled")

    def _update_rows(self, rows: List[Dict], avgs: Dict[str, Optional[float]]):
        self.rows = rows
        self._render_rows(rows)
        self.log(f"{len(rows)} Zeilen geladen.")
        self.log("Team-Mittel (Q-TTR):")
        for t, v in avgs.items():
            self.log(f"  • {t}: {'' if v is None else round(v,1)}")
        self.set_busy(False)

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu speichern", "Keine Daten geladen."); return
        fmt = self.var_format.get(); sprache = self.var_sprache.get()
        ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "xlsx": ".xlsx"}
        if fmt not in ext_map:
            messagebox.showerror("Fehler", f"Unbekanntes Format: {fmt}"); return
        path = filedialog.asksaveasfilename(
            title="Speichern unter",
            defaultextension=ext_map[fmt],
            filetypes=[("Excel","*.xlsx"), ("JSON","*.json"),("CSV","*.csv"),("Markdown","*.md"),("Alle Dateien","*.*")]
        )
        if not path: return
        try:
            export_rows(self.rows, fmt, sprache, path)
            messagebox.showinfo("Gespeichert", f"Erfolg: {path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    # -------------------- Druckvorschau --------------------

    def on_print(self):
        if not self.rows:
            messagebox.showinfo("Nichts zu drucken", "Keine Daten geladen."); return

        dlg = tk.Toplevel(self.root); dlg.title("Druckvorschau / Optionen"); dlg.grab_set()
        dlg.geometry("520x260")
        box = ttk.Frame(dlg, padding=10); box.pack(fill="both", expand=True)

        # Felder
        var_title = tk.StringVar(value=f"Q-TTR – {self.var_saison.get()} / {self.var_runde.get()} – {self.var_group_label.get()}")
        var_orient = tk.StringVar(value="landscape")  # 'landscape' | 'portrait'
        var_font   = tk.IntVar(value=8)
        var_open   = tk.BooleanVar(value=True)
        # Ränder (mm)
        var_m_left   = tk.DoubleVar(value=12.0)
        var_m_right  = tk.DoubleVar(value=12.0)
        var_m_top    = tk.DoubleVar(value=12.0)
        var_m_bottom = tk.DoubleVar(value=12.0)

        # Layout
        r = 0
        ttk.Label(box, text="Titel").grid(row=r, column=0, sticky="w")
        ttk.Entry(box, textvariable=var_title).grid(row=r, column=1, columnspan=3, sticky="ew", padx=6, pady=4)

        r += 1
        ttk.Label(box, text="Ausrichtung").grid(row=r, column=0, sticky="w")
        ttk.Radiobutton(box, text="Querformat", variable=var_orient, value="landscape").grid(row=r, column=1, sticky="w")
        ttk.Radiobutton(box, text="Hochformat", variable=var_orient, value="portrait").grid(row=r, column=2, sticky="w")
        ttk.Label(box, text="Schriftgröße").grid(row=r, column=3, sticky="e")
        ttk.Spinbox(box, from_=6, to=12, textvariable=var_font, width=5).grid(row=r, column=4, sticky="w", padx=6)

        r += 1
        ttk.Label(box, text="Ränder (mm)").grid(row=r, column=0, sticky="w")
        ttk.Label(box, text="Links").grid(row=r, column=1, sticky="e")
        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_left, width=6).grid(row=r, column=2, sticky="w")
        ttk.Label(box, text="Rechts").grid(row=r, column=3, sticky="e")
        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_right, width=6).grid(row=r, column=4, sticky="w")

        r += 1
        ttk.Label(box, text="").grid(row=r, column=0, sticky="w")
        ttk.Label(box, text="Oben").grid(row=r, column=1, sticky="e")
        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_top, width=6).grid(row=r, column=2, sticky="w")
        ttk.Label(box, text="Unten").grid(row=r, column=3, sticky="e")
        ttk.Spinbox(box, from_=5, to=30, increment=1, textvariable=var_m_bottom, width=6).grid(row=r, column=4, sticky="w")

        r += 1
        ttk.Checkbutton(box, text="PDF nach Erzeugung öffnen", variable=var_open).grid(row=r, column=0, columnspan=2, sticky="w", pady=(6,0))

        for c in range(5): box.columnconfigure(c, weight=(1 if c in (1,2,4) else 0))

        # Buttons
        btns = ttk.Frame(box); btns.grid(row=r+1, column=0, columnspan=5, sticky="ew", pady=(12,0))
        for i in range(3): btns.columnconfigure(i, weight=1)

        def make_pdf_and(option_print: bool):
            try:
                margins = {
                    "left":   mm_to_pt(var_m_left.get()),
                    "right":  mm_to_pt(var_m_right.get()),
                    "top":    mm_to_pt(var_m_top.get()),
                    "bottom": mm_to_pt(var_m_bottom.get()),
                }
            except Exception:
                messagebox.showerror("Fehler", "Ungültige Randangaben."); return

            out_dir = CONFIG_DIR / "printouts"; out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = out_dir / f"qttr_{ts}.pdf"

            try:
                pdf_from_rows(
                    self.rows, pdf_path,
                    titel=var_title.get().strip() or "Q-TTR",
                    sprache=self.var_sprache.get(),
                    orientation=var_orient.get(),
                    fontsize=int(var_font.get()),
                    margins_pt=margins
                )
            except Exception as e:
                if self.var_debug.get(): logger.exception("PDF-Erzeugung fehlgeschlagen")
                messagebox.showerror("Fehler", f"PDF konnte nicht erzeugt werden:\n{e}")
                return

            if option_print:
                attempted = print_file(pdf_path)
                if attempted:
                    self.log(f"Druckauftrag gestartet: {pdf_path}")
                    dlg.destroy()
                else:
                    webbrowser.open(str(pdf_path))
                    self.log(f"PDF geöffnet (zum manuellen Drucken): {pdf_path}")
                    dlg.destroy()
            else:
                if var_open.get():
                    webbrowser.open(str(pdf_path))
                self.log(f"PDF erzeugt: {pdf_path}")
                dlg.destroy()

        ttk.Button(btns, text="Als PDF erzeugen", command=lambda: make_pdf_and(False)).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(btns, text="Direkt drucken",   command=lambda: make_pdf_and(True)).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(btns, text="Abbrechen",        command=dlg.destroy).grid(row=0, column=2, padx=6, sticky="ew")

    # -------------------- Gruppen/Settings --------------------

    def on_pick_groups_path(self):
        initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)
        initial_file = self.groups_path.name if self.groups_path else "gruppen.json"
        chosen = filedialog.asksaveasfilename(
            title="Speicherort für gruppen.json wählen",
            initialdir=initial_dir, initialfile=initial_file,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]
        )
        if not chosen: return
        new_path = _normalize_path(chosen)
        try:
            if Path(new_path).exists():
                data = json.loads(Path(new_path).read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.groups = data
            else:
                save_groups(self.groups, new_path)
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")
            return
        self.groups_path = new_path
        cfg = load_config(); cfg["groups_path"] = str(new_path); save_config(cfg)
        self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")
        self._refresh_group_dropdown()

    def on_settings(self):
        if messagebox.askyesno("Einstellung speichern", "Aktuelle Konfiguration als Standard speichern?"):
            cfg = load_config()
            cfg.update({
                "base": self.var_base.get(),
                "saison": self.var_saison.get(),
                "runde": self.var_runde.get(),
                "group_label": self.var_group_label.get(),
                "group": self.var_group_id.get(),
                "sprache": self.var_sprache.get(),
                "format": self.var_format.get(),
                "autofetch": self.var_autofetch.get(),
                "groups_path": str(self.groups_path),
            })
            try:
                save_config(cfg)
                messagebox.showinfo("Gespeichert", "Konfiguration gespeichert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Konfiguration konnte nicht gespeichert werden:\n{e}")

    def on_groups(self):
        dlg = tk.Toplevel(self.root); dlg.title("Gruppen verwalten"); dlg.grab_set()
        dlg.geometry("620x420")
        container = ttk.Frame(dlg, padding=10); container.pack(fill="both", expand=True)
        cols = ("label","id")
        tree = ttk.Treeview(container, columns=cols, show="headings", height=10)
        tree.heading("label", text="Bezeichnung"); tree.heading("id", text="Group-ID")
        tree.column("label", stretch=True, width=360); tree.column("id", stretch=False, width=140)
        tree.pack(fill="both", expand=True, pady=(0,8))

        path_frame = ttk.Frame(container); path_frame.pack(fill="x", pady=(0,8))
        lbl = ttk.Label(path_frame, text=f"Datei: {self.groups_path}"); lbl.pack(side="left", padx=(0,6))
        def pick_path():
            initial_dir = str(self.groups_path.parent if self.groups_path else CONFIG_DIR)
            initial_file = self.groups_path.name if self.groups_path else "gruppen.json"
            chosen = filedialog.asksaveasfilename(
                title="Speicherort für gruppen.json wählen",
                initialdir=initial_dir, initialfile=initial_file,
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]
            )
            if not chosen: return
            new_path = _normalize_path(chosen)
            try:
                if Path(new_path).exists():
                    data = json.loads(Path(new_path).read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        self.groups = data
                else:
                    save_groups(self.groups, new_path)
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Datei nicht verwenden:\n{e}")
                return
            self.groups_path = new_path
            cfg = load_config(); cfg["groups_path"] = str(new_path); save_config(cfg)
            lbl.config(text=f"Datei: {self.groups_path}")
            self.lbl_gpath.config(text=f"Gruppen-Datei: {self.groups_path}")
            refresh_tree(); self._refresh_group_dropdown()
        ttk.Button(path_frame, text="Speicherort wählen …", command=pick_path).pack(side="left")

        form = ttk.Frame(container); form.pack(fill="x", pady=4)
        ttk.Label(form, text="Bezeichnung").grid(row=0, column=0, sticky="w")
        var_label = tk.StringVar(); ent_label = ttk.Entry(form, textvariable=var_label); ent_label.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Label(form, text="Group-ID").grid(row=0, column=2, sticky="e")
        var_id = tk.StringVar(); ent_id = ttk.Entry(form, textvariable=var_id); ent_id.grid(row=0, column=3, sticky="ew", padx=6)
        for i in range(4): form.columnconfigure(i, weight=(1 if i in (1,3) else 0))

        btns = ttk.Frame(container); btns.pack(fill="x", pady=(4,0))
        def refresh_tree():
            for i in tree.get_children(): tree.delete(i)
            for g in self.groups: tree.insert("", "end", values=(g.get("label",""), g.get("id","")))
        def select_from_tree(_evt=None):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values"); var_label.set(vals[0]); var_id.set(vals[1])
        def add_or_update():
            label = var_label.get().strip(); gid = var_id.get().strip()
            if not label or not gid:
                messagebox.showwarning("Fehlende Eingaben", "Bitte Bezeichnung und Group-ID angeben."); return
            if not gid.isdigit():
                if not messagebox.askyesno("Achtung", "Group-ID ist nicht rein numerisch. Trotzdem übernehmen?"): return
            for g in self.groups:
                if g.get("label","") == label:
                    g["id"] = gid; break
            else:
                self.groups.append({"label": label, "id": gid})
            save_groups(self.groups, self.groups_path)
            refresh_tree(); self._refresh_group_dropdown()
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            label = tree.item(sel[0], "values")[0]
            self.groups = [g for g in self.groups if g.get("label","") != label]
            save_groups(self.groups, self.groups_path)
            refresh_tree(); self._refresh_group_dropdown()
        def close_dialog():
            if self.var_group_label.get() not in self._group_labels():
                self.var_group_label.set(self._group_labels()[0] if self._group_labels() else "")
            self._sync_group_id_to_label()
            try:
                self._save_current_config()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Konfiguration nicht speichern:\n{e}")
        ttk.Button(btns, text="Hinzufügen / Aktualisieren", command=add_or_update).pack(side="left", padx=4)
        ttk.Button(btns, text="Löschen", command=delete_selected).pack(side="left", padx=4)
        ttk.Button(btns, text="Schließen", command=close_dialog).pack(side="right", padx=4)

        tree.bind("<<TreeviewSelect>>", select_from_tree)
        refresh_tree()

    def _refresh_group_dropdown(self):
        self.cmb_group.config(values=self._group_labels())
        if self.var_group_label.get() not in self._group_labels() and self._group_labels():
            self.var_group_label.set(self._group_labels()[0])
        self._sync_group_id_to_label()

    def _save_current_config(self):
        config = load_config()
        config.update({
            "base": self.var_base.get(),
            "saison": self.var_saison.get(),
            "runde": self.var_runde.get(),
            "group_label": self.var_group_label.get(),
            "group": self.var_group_id.get(),
            "sprache": self.var_sprache.get(),
            "format": self.var_format.get(),
            "autofetch": bool(self.var_autofetch.get()),
            "groups_path": str(self.groups_path),
        })
        save_config(config)

def main():
    root = tk.Tk()
    try:
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass

    # Cross-Platform Maximierung mit Fallback
    try:
        if sys.platform.startswith("win"):
            root.state('zoomed')
        elif sys.platform == "darwin":
            root.attributes('-zoomed', True)
        else:
            root.attributes('-zoomed', True)
    except Exception:
        root.geometry("1200x700")

    app = TTRScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

---

## Commit-Text (Deutsch, vollständig)
```
feat(gui): robustere Parser, bessere QTTR-Erkennung, UX-Verbesserungen und sauberes Beenden

- Parser: neue Helper-Funktion _mk_soup nutzt bevorzugt lxml und fällt bei Bedarf auf html.parser zurück
- QTTR-Erkennung: _is_qttr_header normalisiert Header und erkennt diverse Varianten (z. B. „Q TTR“, „QTTR-Werte“)
- Druck-Button: initial deaktiviert; wird erst nach erfolgreichem Datenabruf aktiv
- Exit: beendet Anwendung sauber via root.destroy
- Fenster: Cross-Platform-Maximierung (Windows „zoomed“, macOS/Linux „-zoomed“) mit Geometry-Fallback
- Tabelle: Kontextmenü „Zeile kopieren“ (TSV in Zwischenablage)
- Shortcuts: Strg+P (Drucken), Esc (Abruf abbrechen, falls aktiv)

Refactor:
- looks_like_login_or_error / parse_group_pools auf _mk_soup umgestellt

Hinweis:
- Keine optionalen Zusatzabhängigkeiten nötig; bs4 bleibt ausreichend.
```

### 43. Benutzer

info box implementieren mit folgendem inhalt: Autor Markus Dickscheit Name: TTRScraper, Version 1.0,  Text: Ist ausschließlich für den privaten gebrauch erstellt. Verwenden auf eigene Gefahr. Open Source

### 44. Assistent

Klar – ich baue dir eine **Info-Box** ein (Button + Shortcut). Minimalinvasiv, ohne neue Abhängigkeiten.

## Änderungen (präziser Patch)

### 1) Metadaten oben definieren (z. B. direkt unter den LOG-/CONFIG-Konstanten)
```python
# --- App-Metadaten für die Info-Box -----------------------------------------
INFO_NAME = "TTRScraper"
INFO_VERSION = "1.0"
INFO_AUTHOR = "Markus Dickscheit"
INFO_TEXT = "Ist ausschließlich für den privaten gebrauch erstellt. Verwenden auf eigene Gefahr. Open Source"
```

### 2) Info-Button in die Buttonleiste einfügen
Im Konstruktor (`__init__`) im Block „Buttons / Schalter“:

- erhöhe die Spaltenanzahl von 13 auf **14**:
```python
- for i in range(13): btn_frame.columnconfigure(i, weight=1)
+ for i in range(14): btn_frame.columnconfigure(i, weight=1)
```

- **neuen Button** hinzufügen und `Exit` eins nach rechts schieben:
```python
# ... bereits vorhandene Buttons ...
self.chk_debug    = ttk.Checkbutton(btn_frame, text="Debug-Log",    variable=self.var_debug)
self.chk_debug.grid(row=0, column=11, padx=4, sticky="w")

# NEU: Info-Button
self.btn_info     = ttk.Button(btn_frame, text="Info", command=self.on_info)
self.btn_info.grid(row=0, column=12, padx=4, sticky="ew")

# Exit jetzt in Spalte 13
- self.btn_exit     = ttk.Button(btn_frame, text="Exit", command=self.root.destroy)
- self.btn_exit.grid(row=0, column=12, padx=4, sticky="ew")
+ self.btn_exit     = ttk.Button(btn_frame, text="Exit", command=self.root.destroy)
+ self.btn_exit.grid(row=0, column=13, padx=4, sticky="ew")
```

### 3) Info-Handler implementieren
Füge diese Methode in die Klasse `TTRScraperGUI` ein (z. B. unter „Actions“ oder „Druckvorschau“ – egal, Hauptsache innerhalb der Klasse):
```python
def on_info(self):
    title = f"Info — {INFO_NAME}"
    msg = (
        f"Name: {INFO_NAME}\n"
        f"Version: {INFO_VERSION}\n"
        f"Autor: {INFO_AUTHOR}\n\n"
        f"{INFO_TEXT}"
    )
    messagebox.showinfo(title, msg, parent=self.root)
```

### 4) Shortcut für die Info-Box (F1)
Im Konstruktor, wo du schon die Shortcuts bindest:
```python
self.root.bind("<Control-s>", lambda e: self.on_export())
self.root.bind("<Control-p>", lambda e: self.on_print())
self.root.bind("<Escape>",    lambda e: self.on_cancel() if str(self.btn_cancel['state']) == 'normal' else None)
# NEU:
self.root.bind("<F1>",        lambda e: self.on_info())
```

Das war’s – der neue **„Info“**-Button öffnet deine Info-Box, und **F1** tut’s auch.

---

## Vollständiger Commit-Text (Deutsch)
```
feat(gui): Info-Box hinzugefügt (Autor/Name/Version/Disclaimer)

- Neuer Button „Info“ in der Buttonleiste + F1-Shortcut
- Anzeige per MessageBox mit:
  • Autor: Markus Dickscheit
  • Name: TTRScraper
  • Version: 1.0
  • Text: „Ist ausschließlich für den privaten gebrauch erstellt. Verwenden auf eigene Gefahr. Open Source“
- Buttonleiste um eine Spalte erweitert (Exit nach rechts verschoben)
- Metadaten zentral als Konstanten hinterlegt (INFO_NAME/INFO_VERSION/INFO_AUTHOR/INFO_TEXT)

Hinweis: Keine zusätzlichen Abhängigkeiten erforderlich.
```

### 45. Benutzer

bitte implementieren

### 46. Assistent

Eingebaut! Unten bekommst du einen **minimalen Patch**, den du direkt in deine aktuelle `v1.8+`-Basis einfügst. Er fügt die Info-Box samt **„Info“-Button** und **F1-Shortcut** hinzu – ohne neue Abhängigkeiten.

---

# Änderungen (copy & paste)

## 1) Metadaten hinzufügen
Setz das direkt unter deine LOG-/CONFIG-Konstanten (z. B. nach `LOG_PATH = ...`):

```python
# --- App-Metadaten für die Info-Box -----------------------------------------
INFO_NAME = "TTRScraper"
INFO_VERSION = "1.0"
INFO_AUTHOR = "Markus Dickscheit"
INFO_TEXT = "Ist ausschließlich für den privaten gebrauch erstellt. Verwenden auf eigene Gefahr. Open Source"
```

---

## 2) Buttonleiste: eine Spalte mehr
Im Konstruktor `__init__` in der Klasse `TTRScraperGUI`, im Block „Buttons / Schalter“:

```python
- for i in range(13): btn_frame.columnconfigure(i, weight=1)
+ for i in range(14): btn_frame.columnconfigure(i, weight=1)
```

---

## 3) Neuen „Info“-Button einfügen und Exit verschieben
Im selben Button-Block, **nach** `self.chk_debug.grid(...)` einfügen und **Exit** um eine Spalte nach rechts verschieben:

```python
# NEU: Info-Button
self.btn_info     = ttk.Button(btn_frame, text="Info", command=self.on_info)
self.btn_info.grid(row=0, column=12, padx=4, sticky="ew")

# Exit jetzt in Spalte 13
- self.btn_exit     = ttk.Button(btn_frame, text="Exit", command=self.root.destroy)
- self.btn_exit.grid(row=0, column=12, padx=4, sticky="ew")
+ self.btn_exit     = ttk.Button(btn_frame, text="Exit", command=self.root.destroy)
+ self.btn_exit.grid(row=0, column=13, padx=4, sticky="ew")
```

---

## 4) Info-Handler implementieren
Innerhalb der Klasse `TTRScraperGUI` (z. B. unter den Actions) diese Methode hinzufügen:

```python
def on_info(self):
    title = f"Info — {INFO_NAME}"
    msg = (
        f"Name: {INFO_NAME}\n"
        f"Version: {INFO_VERSION}\n"
        f"Autor: {INFO_AUTHOR}\n\n"
        f"{INFO_TEXT}"
    )
    messagebox.showinfo(title, msg, parent=self.root)
```

---

## 5) F1-Shortcut binden
Im Konstruktor, bei deinen bestehenden Shortcuts:

```python
self.root.bind("<Control-s>", lambda e: self.on_export())
self.root.bind("<Control-p>", lambda e: self.on_print())
self.root.bind("<Escape>",    lambda e: self.on_cancel() if str(self.btn_cancel['state']) == 'normal' else None)
# NEU:
self.root.bind("<F1>",        lambda e: self.on_info())
```

---

Fertig. Beim Klick auf **„Info“** (oder F1) erscheint die Box mit:
- Autor: Markus Dickscheit  
- Name: TTRScraper  
- Version: 1.0  
- Text: „Ist ausschließlich für den privaten gebrauch erstellt. Verwenden auf eigene Gefahr. Open Source“

Wenn du lieber ein modales „About“-Fenster mit Logo/Link haben willst, kann ich dir das auch als eigenes `Toplevel` bauen.

### 47. Benutzer

alle anpassungen wurden in den code übernommen

### 48. Assistent

Perfekt — klingt so, als wäre dein Tool jetzt rund. Hier noch ein knapper Abschluss mit Setup, Schnelltest und Mini-Checkliste, damit alles glatt läuft.

# Setup (einmalig)
```bash
pip install requests beautifulsoup4 requests-cache openpyxl platformdirs reportlab
```

# Schnelltest (Smoke Test)
1. Starten: `python ttr_gui.py`
2. Base-URL: `https://ttbw.click-tt.de`
3. Saison: `TTBW 2025/26`, Runde: `vorrunde`
4. Gruppe per Dropdown wählen (z. B. „Kreisliga C2“ → ID 494514).
5. **Abrufen** → in der Vorschau sollten Q-TTR-Zeilen erscheinen.
6. **Speichern …** (CSV/XLSX/JSON/MD) ausprobieren.
7. **Drucken …** → PDF erzeugen und öffnen bzw. direkt drucken.
8. **Info** (oder **F1**) → Box mit Autor/Name/Version/Disclaimer.
9. Shortcuts: **Ctrl+S** (Speichern), **Ctrl+P** (Drucken), **Esc** (Abruf abbrechen).

# Mini-Checkliste & Tipps
- **Druck (Linux/macOS):** Stelle sicher, dass `lp` oder `lpr` im PATH ist (CUPS).
- **Parser-Fallback:** Bei ungewöhnlichem HTML nutzt der Code automatisch `html.parser`.
- **QTTR-Header:** Falls ein Verband exotische Spaltentitel nutzt, passe `_is_qttr_header` an.
- **Gruppenverwaltung:** `Gruppen …` öffnen → Bezeichnung/ID pflegen; Speicherort der `gruppen.json` ist frei wählbar und in `config.json` hinterlegt.
- **Logs:** Rotierendes Log unter `…/ttrscraper.log` hilft beim Debugging.

# Commit-Text (Deutsch, vollständig)
```
feat(app): Info-Box + finale UX-/Robustheitsverbesserungen

- Info-Box hinzugefügt (Button „Info“ + F1-Shortcut)
  • Name: TTRScraper
  • Version: 1.0
  • Autor: Markus Dickscheit
  • Text: „Ist ausschließlich für den privaten gebrauch erstellt. Verwenden auf eigene Gefahr. Open Source“
- Buttonleiste erweitert; Exit nach rechts verschoben
- Parser robuster (_mk_soup): bevorzugt lxml, Fallback auf html.parser
- QTTR-Spalte toleranter erkannt (_is_qttr_header)
- Druck-Button initial deaktiviert; wird nach Datenabruf aktiv
- Exit beendet sauber via root.destroy
- Cross-Platform-Maximierung (Windows: 'zoomed', macOS/Linux: '-zoomed' Fallback)
- Tabelle: Kontextmenü „Zeile kopieren“ (TSV in Zwischenablage)
- Shortcuts: Ctrl+S (Speichern), Ctrl+P (Drucken), Esc (Abruf abbrechen), F1 (Info)
- Druckdialog: PDF erzeugen/öffnen oder direkt drucken; Ränder/Ausrichtung/Schriftgröße konfigurierbar

Dependencies (bereits genutzt): requests, beautifulsoup4, requests-cache, openpyxl, platformdirs, reportlab
```

Wenn du als Nächstes eine portable Desktop-App für Teamkollegen möchtest, kann ich dir ein PyInstaller-Recipe (inkl. Fonts für ReportLab) vorbereiten.

### 49. Benutzer

ja

### 50. Assistent

yes captain. hier ist ein knackiges, pragmatisches **PyInstaller-Recipe** für dein Projekt – ohne Extra-Abhängigkeiten, mit zwei Wegen: schneller CLI-Build und reproduzierbarer `.spec`-Build. Dazu Troubleshooting, Icons, und ein Commit-Text auf Deutsch.

---

# 1) Schnellstart (CLI)

> Gut, wenn du einfach nur fix ein lauffähiges Binary willst.

## Windows (exe, ohne Konsole)
```powershell
py -m pip install --upgrade pyinstaller
$cert = python -c "import certifi,sys;print(certifi.where())"
pyinstaller ttr_gui.py `
  --name TTRScraper `
  --noconfirm `
  --windowed `
  --add-data "$cert;certifi"
# optionales Icon: --icon path\zu\icon.ico
```

## macOS (App, ohne Konsole)
```bash
python3 -m pip install --upgrade pyinstaller
CERT=$(python3 -c 'import certifi;print(certifi.where())')
pyinstaller ttr_gui.py \
  --name TTRScraper \
  --noconfirm \
  --windowed \
  --add-data "$CERT:certifi"
# optionales Icon: --icon path/to/icon.icns
```

## Linux (AppImage/Dist-Ordner, ohne Konsole)
```bash
python3 -m pip install --upgrade pyinstaller
CERT=$(python3 -c 'import certifi;print(certifi.where())')
pyinstaller ttr_gui.py \
  --name TTRScraper \
  --noconfirm \
  --windowed \
  --add-data "$CERT:certifi"
# optionales Icon: --icon path/to/icon.png
```

Ergebnis liegt in `dist/TTRScraper/` (Windows: `TTRScraper.exe`, macOS: `TTRScraper.app`).

**Warum `--add-data certifi`?**  
`requests` braucht ein CA-Bundle für HTTPS. PyInstaller packt `certifi` oft automatisch ein; das explizite Hinzufügen verhindert „SSL: CERTIFICATE_VERIFY_FAILED“ auf manchen Systemen.

---

# 2) Reproduzierbar mit `.spec`

> Ideal für CI/CD oder wenn du Build-Optionen zentral versionieren willst.

Lege eine Datei `ttrscraper.spec` im Projektroot an:

```python
# ttrscraper.spec — PyInstaller 6+
# Build:  pyinstaller ttrscraper.spec

import certifi
from PyInstaller.utils.hooks import collect_submodules

app_name = "TTRScraper"

block_cipher = None

datas = [
    (certifi.where(), "certifi/cacert.pem"),
]

# ReportLab & requests_cache werden meist automatisch gehookt.
# Falls deine Umgebung zickt, erzwinge Hidden-Imports:
hiddenimports = []
hiddenimports += collect_submodules("reportlab")
hiddenimports += collect_submodules("requests_cache")

a = Analysis(
    ['ttr_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=app_name,
    console=False,   # GUI: keine Konsole anzeigen
    disable_windowed_traceback=False,
    argv_emulation=False,     # auf macOS meist False okay
    target_arch=None,
    codesign_identity=None,   # macOS: hier ggf. Signatur setzen
    entitlements_file=None,   # macOS: Sandbox/Entitlements optional
    icon=None,                # setze z.B. "assets/app.icns" oder ".ico"
)

# Auf macOS ein .app-Container erstellen:
app = BUNDLE(
    exe,
    name=f"{app_name}.app",
    icon=None,
    bundle_identifier="de.ttc.ttrscraper",
    info_plist={
        "CFBundleName": app_name,
        "CFBundleDisplayName": app_name,
        "CFBundleVersion": "1.0",
        "CFBundleShortVersionString": "1.0",
        "NSHighResolutionCapable": True,
        # Für Druck/Dateizugriffe sind in der Regel keine Extra-Entitlements nötig.
    },
)
```

Build:
```bash
pyinstaller ttrscraper.spec --noconfirm
```

---

# 3) Optional: Icon einbinden
- **Windows:** `.ico` (mehrere Größen 16/32/48/256 px).
- **macOS:** `.icns`.
- **Linux:** `.png` ist ok.

Im CLI-Build: `--icon pfad/zum/icon.ico`  
Im `.spec`: `icon="assets/app.icns"` (bei `EXE`/`BUNDLE` setzen).

---

# 4) Pfade & Daten
Dein Code nutzt `platformdirs` → Config/Cache landen sauber im Nutzerverzeichnis.  
Keine Codeänderung nötig; `gruppen.json` und `config.json` werden dort erzeugt/geladen.

---

# 5) Signieren & Notarization (nur macOS, grob)
Wenn du verteilst, willst du meist signieren:
```bash
codesign --deep --force --options runtime --sign "Developer ID Application: <Name> (<TeamID>)" dist/TTRScraper.app
xcrun notarytool submit dist/TTRScraper.app --keychain-profile "<profile>" --wait
```
Nicht zwingend fürs Testen, aber hilfreich gegen „App beschädigt“-Warnungen.

---

# 6) Troubleshooting (kurz & knackig)

- **SSL Fehler (CERTIFICATE_VERIFY_FAILED):**  
  Stelle sicher, dass `certifi` via `--add-data` enthalten ist (siehe oben).

- **Drucken funktioniert nicht (Linux/macOS):**  
  `lp`/`lpr` müssen im System vorhanden sein (CUPS). Test: `lp --version`.

- **„Failed to execute script“ beim Start:**  
  Lösche `build/` & `dist/` und baue neu; prüfe, ob dein `ttr_gui.py` wirklich Entry-Point ist.

- **Kein Fenster / App startet nicht:**  
  Prüfe, ob `--windowed` gesetzt ist (sonst kann eine Konsole „im Weg“ sein, v. a. auf macOS).

---

# 7) Mini-Buildscript (optional)

`build_win.ps1`:
```powershell
py -m pip install --upgrade pyinstaller
$cert = python -c "import certifi;print(certifi.where())"
pyinstaller ttr_gui.py --name TTRScraper --noconfirm --windowed --add-data "$cert;certifi" # --icon .\assets\app.ico
```

`build_nix.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install --upgrade pyinstaller
CERT=$(python3 -c 'import certifi;print(certifi.where())')
pyinstaller ttr_gui.py --name TTRScraper --noconfirm --windowed --add-data "$CERT:certifi" # --icon assets/app.icns
```

---

# Commit-Text (Deutsch, vollständig)
```
build(distribution): PyInstaller-Packaging für TTRScraper hinzugefügt

- CLI-Build-Rezepte für Windows/macOS/Linux (ohne Konsole, --windowed)
- Zertifikatsbundle von certifi explizit eingebunden (--add-data), um SSL-Fehler zu vermeiden
- Reproduzierbarer Build via ttrscraper.spec:
  • packt certifi/cacert.pem
  • optional Hidden-Imports für reportlab/requests_cache
  • macOS .app-Bundle mit Basis-InfoPlist
- Optionale Icons (.ico/.icns/.png) dokumentiert
- Kurze Troubleshooting-Sektion (SSL, Druck, Hooks)
- Beispiel-Buildskripte (PowerShell/Bash) für lokale Builds oder CI

Hinweis: Keine zusätzlichen Laufzeit-Abhängigkeiten; App nutzt weiterhin platformdirs für Config/Cache.
```

Wenn du magst, packe ich dir noch ein kleines `--splash` (eigenes Fenster) oder ein automatisches Verpacken in ein .dmg (macOS) dazu.

### 51. Benutzer

ja

### 52. Assistent

sehr gut — ich liefere dir beides:  
A) Splashscreen (Windows/Linux via PyInstaller-Option, macOS via integrierter Tk-Splash)  
B) macOS-DMG-Packaging (minimal mit `hdiutil`, optional „hübsch“ mit `create-dmg`)

Ich packe dir unten **präzise Patches** + **Build-Snippets** + **Commit-Text**. Wichtige Hinweise sind belegt: PyInstaller-Splash gibt’s als `--splash` (experimentell) und ist **mit Tkinter auf macOS nicht kompatibel**—daher der integrierte Tk-Splash speziell für macOS. citeturn0search10turn0search14turn0search4turn0search11  
Für DMGs nutzt du `hdiutil` aus macOS oder das bewährte `create-dmg`-Script. citeturn0search12turn0search8turn0search3turn0search7

---

# A) Splashscreen

## A1) PyInstaller-Splash (Windows/Linux)
**Einfacher Build mit Bilddatei (PNG):**
```bash
# Windows
pyinstaller ttr_gui.py --name TTRScraper --windowed --noconfirm --splash assets/splash.png

# Linux
pyinstaller ttr_gui.py --name TTRScraper --windowed --noconfirm --splash assets/splash.png
```
> `--splash` aktiviert den Bootloader-Splash, inkl. optionaler Fortschrittsmeldungen. Auf macOS ist das mit Tkinter nicht nutzbar; nimm dafür A2. citeturn0search10turn0search4

**.spec-Variante (automatisch, wenn du mit `--splash` generierst):** In der Spec erscheint ein `Splash(...)`-Target. Falls du manuell pflegst, füge es wie in der Doku beschrieben hinzu. citeturn0search0

## A2) Integrierter Tk-Splash (macOS-tauglich, läuft überall)
Füge diese **kleine Utility** in deine Datei (z. B. direkt über `class TTRScraperGUI:`):

```python
def _center_window(win, w, h):
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (sw - w) // 2, (sh - h) // 3
    win.geometry(f"{w}x{h}+{x}+{y}")

def show_splash(root, title="TTRScraper", text="lädt …"):
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    try:
        splash.attributes("-topmost", True)
    except Exception:
        pass
    frame = ttk.Frame(splash, padding=20)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=title, font=("TkDefaultFont", 16, "bold")).pack()
    ttk.Label(frame, text=text).pack(pady=(8, 0))
    _center_window(splash, 320, 140)
    root.withdraw()           # Hauptfenster verstecken bis bereit
    root.after(50, splash.lift)
    return splash
```

**`main()` anpassen** – Splash vor UI erstellen, danach de-iconify und maximieren:
```python
def main():
    root = tk.Tk()
    try:
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore
    except Exception:
        pass

    # NEU: Splash anzeigen (funktioniert auf allen Plattformen; macOS-Ersatz für PyInstaller-Splash)
    splash = show_splash(root, title="TTRScraper", text="lädt …")

    # GUI aufbauen
    app = TTRScraperGUI(root)

    # Splash weg, Hauptfenster zeigen
    try:
        splash.destroy()
    except Exception:
        pass
    root.deiconify()

    # Cross-Platform "maximiert" (nach dem Deiconify)
    try:
        if sys.platform.startswith("win"):
            root.state('zoomed')
        elif sys.platform == "darwin":
            root.attributes('-zoomed', True)
        else:
            root.attributes('-zoomed', True)
    except Exception:
        root.geometry("1200x700")

    root.mainloop()
```

> So bekommst du auf **macOS** einen sauberen Splash ohne PyInstaller-Threading-Probleme; unter Windows/Linux kannst du zusätzlich den PyInstaller-Splash nutzen, wenn du willst. citeturn0search4turn0search11

---

# B) macOS-DMG bauen

## B1) Minimal mit Bordmitteln (`hdiutil`)
Lege ein kleines Script `packaging/make_dmg.sh` an:
```bash
#!/usr/bin/env bash
set -euo pipefail
APP="dist/TTRScraper.app"           # Pfad zu deiner .app
VOLNAME="TTRScraper"
OUT="dist/TTRScraper-1.0.dmg"       # Version optional dynamisch setzen

# Staging: App + Applications-Link (Drag&Drop UX)
STAGE="dist/_dmg_stage"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

# DMG erzeugen (komprimiert, read-only)
hdiutil create -volname "$VOLNAME" -srcfolder "$STAGE" -ov -format UDZO "$OUT"

echo "DMG erstellt: $OUT"
```
> `hdiutil` ist das macOS-Tool für DMGs; `-srcfolder` nimmt deinen Stage-Ordner, `-format UDZO` erzeugt ein komprimiertes Image. citeturn0search12turn0search8

## B2) „Schönes“ DMG (Hintergrund, Layout) mit `create-dmg`
Wenn du eine **nice** Optik willst (Hintergrundbild, Icons an Positionen), nimm das OSS-Script `create-dmg`:
```bash
# Installation (einmalig)
brew install create-dmg

# Build
create-dmg \
  --volname "TTRScraper" \
  --window-pos 200 120 \
  --window-size 540 380 \
  --icon-size 96 \
  --text-size 12 \
  --background "assets/dmg-bg.png" \
  --icon "TTRScraper.app" 140 180 \
  --app-drop-link 400 180 \
  "dist/TTRScraper-1.0.dmg" \
  "dist/TTRScraper.app"
```
`create-dmg` kümmert sich um Layout/DS_Store und kann bei Bedarf sogar signieren; Notarization bleibt separat. citeturn0search3turn0search7turn0search13

---

# Bonus: CI-Hinweis
Für GitHub Actions gibt’s fertige Actions zum DMG-Bauen, falls du später automatisierst. citeturn0search9

---

# Vollständiger Commit-Text (Deutsch)
```
feat(packaging): Splashscreen & macOS-DMG-Distribution ergänzt

Splash:
- Windows/Linux: PyInstaller-Bootloader-Splash via `--splash assets/splash.png` (experimentell)
- macOS: integrierter Tk-Splash (Toplevel, overrideredirect), da PyInstaller-Splash mit Tkinter auf macOS nicht kompatibel ist
- `main()` angepasst: Splash vor UI, danach deiconify + Maximierung

DMG:
- Minimaler DMG-Build via `hdiutil` (Staging inkl. Applications-Symlink, UDZO)
- Option „hübsches“ DMG via `create-dmg` (Hintergrund, Layout, App-Drop-Link)
- Build-Scripts/Kommandos dokumentiert

Docs:
- Hinweise & Links zur PyInstaller-Splash-Option und macOS-Einschränkung für Tkinter
- Hinweise zur DMG-Erstellung mit `hdiutil` und `create-dmg`

Keine neuen Laufzeitabhängigkeiten; Splash (Tk) ist rein intern, PyInstaller-Option bleibt optional.
```

Wenn du magst, packe ich dir noch ein kleines `notarize.sh` (stapled DMG) und ein Codesigning-Snippet für macOS drauf, damit Downloads nicht von Gatekeeper geblockt werden.
