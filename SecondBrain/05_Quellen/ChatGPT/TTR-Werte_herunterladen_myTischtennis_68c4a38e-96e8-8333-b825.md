---
title: "TTR-Werte herunterladen myTischtennis"
type: chatgpt_conversation
source: chatgpt
source_id: "68c4a38e-96e8-8333-b825-6d46d46d8023"
created: 2025-09-13
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
  - tischtennis
  - verein
---


# TTR-Werte herunterladen myTischtennis

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68c4a38e-96e8-8333-b825-6d46d46d8023`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Wie kann ich in mytischtennis die ttr werte einer ganzen ligagruppe zb Kreisliga c2 anschauen und Downloaden

### 2. Assistent

In **myTischtennis.de** kannst du dir zwar die TTR-Werte aller Spieler einer Liga anschauen, aber ein direkter **Export/Download** als Datei (CSV, Excel usw.) ist dort offiziell nicht vorgesehen. Das System ist eher auf die Einzelanzeige ausgelegt. Es gibt aber ein paar Wege, wie du trotzdem an die Daten einer ganzen Gruppe wie „Kreisliga C2“ kommst:

---

### 1. Alle TTR-Werte online einsehen  
- Geh auf **myTischtennis.de → click-TT → Liga**.  
- Wähle deine **Staffel** (z. B. *Kreisliga C2 Herren*).  
- Klicke auf **Mannschaften** und von dort auf die **Einzelergebnisse / Ranglisten**.  
- In der Spielerliste wird jeweils auch der **aktuelle TTR-Wert** angezeigt.  

---

### 2. Daten in eine Tabelle holen (manuell)  
- Die Seite mit der Spielerliste öffnen.  
- Alles markieren und kopieren → in **Excel / Google Sheets** einfügen.  
- Mit "Text in Spalten" kannst du Namen, Verein, TTR usw. sauber trennen.  

---

### 3. Halbautomatisch mit Browser-Tools  
- Mit **Browser-Addons** wie *Table Capture* (Chrome/Firefox) lassen sich Tabellen auf Webseiten direkt als CSV/Excel speichern.  
- Das funktioniert auf den Mannschafts- und Spielerseiten von click-TT / myTischtennis recht gut.  

---

### 4. Automatisiert (nur für Technik-Fans)  
- Da die Daten in HTML-Tabellen liegen, könntest du mit **Python (BeautifulSoup + Pandas)** oder einem kleinen **Web-Scraper** alle Spieler samt TTR-Werten auslesen und in eine Excel-Datei exportieren.  
- Das ist aber technisch aufwendiger und sollte die Nutzungsbedingungen von myTischtennis beachten.  

---

Kurz gesagt:  
Direkt **Download-Button** gibt’s nicht, aber mit *Kopieren & Einfügen* oder einem Browser-Addon kannst du dir sehr einfach eine Tabelle aller TTR-Werte einer ganzen Liga ziehen.  

Soll ich dir ein kleines **Python-Skript schreiben**, das automatisch alle Spieler einer Kreisliga-Gruppe samt TTR in eine Excel-Datei exportiert?

### 3. Benutzer

Ja

### 4. Assistent

Perfekt – hier ist ein kleines, robustes **Python-Skript**, das dir aus einer **click-TT / myTischtennis**-Ligaseite (z. B. „Spieler-Rangliste“ deiner *Kreisliga C2*) die **Spieler samt TTR** herauszieht und als **Excel/CSV** speichert.

Es arbeitet tabellenbasiert (keine Browser-Automation), erkennt typische Spaltennamen („Spieler/Name“, „TTR/QTTR“, „Verein/Mannschaft“) automatisch und säubert die Werte.

---

### 🔧 Voraussetzungen
```bash
pip install pandas requests lxml openpyxl
```

---

### 🐍 Skript: `ttr_export.py`
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import sys
from typing import List, Optional

import pandas as pd
import requests


def fetch_tables(url: str, cookies: Optional[dict] = None, headers: Optional[dict] = None) -> List[pd.DataFrame]:
    """
    Lädt alle HTML-Tabellen einer Seite mit pandas.read_html.
    """
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; TTR-Exporter/1.0; +https://example.local)"
        }
    with requests.Session() as s:
        r = s.get(url, headers=headers, cookies=cookies, timeout=30)
        r.raise_for_status()
        # read_html kann direkt mit r.text arbeiten
        return pd.read_html(r.text, flavor="lxml")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vereinheitlicht Spaltennamen und extrahiert TTR-Zahlen.
    """
    original_cols = df.columns
    # Alles zu Strings und kleinschreiben
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    lower_map = {c: c.lower() for c in df.columns}

    # heuristische Kandidaten
    name_cols = [c for c in df.columns if re.search(r"(spieler|name)", lower_map[c])]
    club_cols = [c for c in df.columns if re.search(r"(verein|mannschaft|team|club)", lower_map[c])]
    ttr_cols  = [c for c in df.columns if re.search(r"\bq?-?ttr\b|\bttr-?wert\b", lower_map[c])]

    # Falls keine explizite TTR-Spalte: manchmal steht TTR in Klammern in einer kombinierten Spalte
    if not ttr_cols and name_cols:
        # versuche TTR aus Namen zu ziehen, z.B. "Muster, Max (1693)"
        def extract_ttr_from_text(x):
            if pd.isna(x):
                return None
            m = re.search(r"\((\d{3,4})\)", str(x))
            return int(m.group(1)) if m else None

        df["TTR"] = df[name_cols[0]].map(extract_ttr_from_text)
        if df["TTR"].notna().any():
            ttr_cols = ["TTR"]

    # Zielspalten bestimmen
    use_name = name_cols[0] if name_cols else (df.columns[0] if len(df.columns) else None)
    use_club = club_cols[0] if club_cols else None
    use_ttr  = ttr_cols[0] if ttr_cols else None

    # Wenn keine brauchbaren Spalten: unverändert zurück
    if use_name is None or use_ttr is None:
        return df

    out = pd.DataFrame()
    out["Spieler"] = df[use_name].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

    if use_club:
        out["Verein/Mannschaft"] = (
            df[use_club].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
        )

    # TTR säubern
    ttr_series = df[use_ttr]
    # häufig sind Kommas, Leerzeichen oder Einheiten drin
    ttr_series = (
        ttr_series.astype(str)
        .str.replace(r"[^\d]", "", regex=True)
        .replace({"": None})
    )
    out["TTR"] = pd.to_numeric(ttr_series, errors="coerce").astype("Int64")

    # Optional: weitere nützliche Spalten, falls vorhanden
    for extra in df.columns:
        el = extra.lower()
        if extra in (use_name, use_club, use_ttr):
            continue
        if re.search(r"(qttr|q-ttr|stichtag|geb\.?|jahrg\.?|rk|bilanz|position|rang|nr)", el):
            out[extra] = df[extra]

    # Duplikate entfernen, leere Namen/TTR raus
    out = out.dropna(subset=["Spieler"]).drop_duplicates()
    return out.reset_index(drop=True)


def choose_best_table(tables: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Wählt die Tabelle aus, die am ehesten die Spielerliste enthält:
    Scoring nach Vorkommen von Name/Spieler + TTR/QTTR.
    """
    best_score = -1
    best = None
    for t in tables:
        cols = [str(c).lower() for c in t.columns]
        score = 0
        if any(re.search(r"(spieler|name)", c) for c in cols):
            score += 2
        if any(re.search(r"\bq?-?ttr\b|\bttr-?wert\b", c) for c in cols):
            score += 3
        if any(re.search(r"(verein|mannschaft|team|club)", c) for c in cols):
            score += 1
        if len(t) >= 6:
            score += 1
        if score > best_score:
            best_score = score
            best = t
    return best


def main():
    ap = argparse.ArgumentParser(
        description="Exportiert Spieler und TTR einer click-TT/myTischtennis Ranglisten-Seite nach Excel/CSV."
    )
    ap.add_argument("url", help="URL der Liga/Spieler-Rangliste (z. B. Kreisliga C2 -> Spieler-Rangliste).")
    ap.add_argument("--xlsx", default="ttr_export.xlsx", help="Pfad zur Excel-Ausgabe (*.xlsx).")
    ap.add_argument("--csv", default=None, help="Optionaler Pfad für CSV-Export.")
    ap.add_argument("--sheet", default="TTR", help="Name des Excel-Arbeitsblatts.")
    ap.add_argument("--cookie", action="append", default=[],
                    help="Optionale Cookies KEY=VALUE (mehrfach nutzbar), falls Login erforderlich ist.")
    args = ap.parse_args()

    # Cookies ggf. aus --cookie sammeln
    cookies = {}
    for c in args.cookie:
        if "=" in c:
            k, v = c.split("=", 1)
            cookies[k.strip()] = v.strip()

    try:
        tables = fetch_tables(args.url, cookies=cookies)
    except Exception as e:
        print(f"Fehler beim Laden der Seite:\n{e}", file=sys.stderr)
        sys.exit(1)

    if not tables:
        print("Keine Tabellen gefunden. Prüfe, ob du auf der Spieler-Rangliste / TTR-Übersicht bist.", file=sys.stderr)
        sys.exit(2)

    best = choose_best_table(tables)
    if best is None:
        print("Konnte keine passende Spielertabelle erkennen.", file=sys.stderr)
        # zur Diagnose die Spalten aller Tabellen ausgeben
        for i, t in enumerate(tables):
            print(f"Tabelle {i}: Spalten = {list(map(str, t.columns))}", file=sys.stderr)
        sys.exit(3)

    cleaned = normalize_columns(best)

    # Prüfen, ob TTR-Spalte wirklich vorhanden/gefüllt ist
    if "TTR" not in cleaned.columns or cleaned["TTR"].isna().all():
        print("Hinweis: Keine TTR-Spalte gefunden oder alle Werte leer. "
              "Bist du sicher auf einer Seite mit TTR/QTTR-Anzeige?", file=sys.stderr)

    # speichern
    try:
        with pd.ExcelWriter(args.xlsx, engine="openpyxl") as xw:
            cleaned.to_excel(xw, sheet_name=args.sheet, index=False)
        print(f"Excel gespeichert: {args.xlsx} (Sheet: {args.sheet})")
    except Exception as e:
        print(f"Fehler beim Schreiben der Excel-Datei: {e}", file=sys.stderr)

    if args.csv:
        try:
            cleaned.to_csv(args.csv, index=False)
            print(f"CSV gespeichert: {args.csv}")
        except Exception as e:
            print(f"Fehler beim Schreiben der CSV-Datei: {e}", file=sys.stderr)

    # Kurze Vorschau auf der Konsole
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print("\nVorschau:")
        print(cleaned.head(20))


if __name__ == "__main__":
    main()
```

---

### ▶️ Anwendung

1) Navigiere in myTischtennis → **click-TT** → **Liga/Staffel** → **Spieler-Rangliste** (oder ähnliche Übersicht, auf der TTR/QTTR sichtbar ist).  
2) Kopiere die **URL** dieser Seite.  
3) Starte das Skript:

```bash
python ttr_export.py "https://<deine-click-tt-url-zur-spieler-rangliste>"
```

- Excel: `ttr_export.xlsx`  
- Optional zusätzlich CSV:

```bash
python ttr_export.py "https://<url>" --csv ttr_export.csv
```

- Falls die Seite nur im eingeloggten Zustand TTR zeigt, kannst du (nur wenn erlaubt) dein **Session-Cookie** mitgeben, z. B.:

```bash
python ttr_export.py "https://<url>" --cookie "JSESSIONID=abc123" --cookie "mt_session=xyz987"
```

*(Cookie-Namen variieren. Cookies nie teilen. Nutzungsbedingungen beachten.)*

---

### 💡 Hinweise & Tipps
- **Seitenvarianz**: Je nach Verband heißen Spalten leicht anders („QTTR“, „Q-TTR“, „TTR-Wert“). Das Skript erkennt die üblichen Varianten automatisch.  
- **Fallback**: Wenn keine TTR-Spalte existiert, versucht das Skript TTR-Werte **in Klammern** neben dem Namen (z. B. „Muster, Max (1693)“) zu parsen.  
- **Transparenz**: Bei Problemen zeigt das Skript die erkannten Tabellenspalten an – damit kann man die richtige URL/Ansicht finden.

---

Wenn du mir **eine konkrete URL deiner Kreisliga-C2-Rangliste** gibst, passe ich dir das Skript bei Bedarf punktgenau an (z. B. zusätzliche Spalten, Filter nur auf Herren/Damen, mehrere Staffeln in einem Rutsch).
