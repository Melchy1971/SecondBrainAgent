---
title: "ttScraper überarbeiten code"
type: chatgpt_conversation
source: chatgpt
source_id: "68d3b878-92b4-832e-85ff-38445a06dbf5"
created: 2025-09-24
tags:
  - chatgpt
  - import
  - ki
  - obsidian
  - sap
  - tischtennis
  - verein
---


# ttScraper überarbeiten code

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68d3b878-92b4-832e-85ff-38445a06dbf5`
- Nachrichten: 3

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ttScrapper überarbeiten code: import csv

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



# --- App-Metadaten für die Info-Box -----------------------------------------

INFO_NAME = "TTRScraper"

INFO_VERSION = "1.0"

INFO_AUTHOR = "Markus Dickscheit"

INFO_TEXT = "Ist ausschließlich für den privaten Gebrauch erstellt. Verwendung auf eigene Gefahr. Open Source."



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

        for i in range(14): btn_frame.columnconfigure(i, weight=1)



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

        # NEU: Info-Button

        self.btn_info     = ttk.Button(btn_frame, text="Info", command=self.on_info)

        self.btn_info.grid(row=0, column=12, padx=4, sticky="ew")

        # Exit jetzt in Spalte 13

        self.btn_exit     = ttk.Button(btn_frame, text="Exit", command=self.root.destroy)

        self.btn_exit.grid(row=0, column=13, padx=4, sticky="ew")



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

        # NEU:

        self.root.bind("<F1>",        lambda e: self.on_info())



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



    def on_info(self):

        title = f"Info — {INFO_NAME}"

        msg = (

            f"Name: {INFO_NAME}\n"

            f"Version: {INFO_VERSION}\n"

            f"Autor: {INFO_AUTHOR}\n\n"

            f"{INFO_TEXT}"

        )

        messagebox.showinfo(title, msg, parent=self.root)



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

### 2. Assistent

nice — ich hab deinen `ttScraper` sauber überarbeitet und in eine klarere, robustere Version gegossen. Du findest den kompletten, lauffähigen Code im Canvas rechts („ttrscraper_refactored.py“).

Kurz, was sich konkret verbessert hat:

- **Parser robuster gemacht:** `parse_int_maybe()` extrahiert Q-TTR sicher (inkl. Minuszeichen), Header-Erkennung für „QTTR“ bleibt tolerant.
- **HTTP sauber gekapselt:** Lazy `requests_cache`-Session mit Retry & konfigurierbaren Defaults; kein globaler Session-Zombie mehr.
- **Konstanten & Defaults zentralisiert:** User-Agent, Sprache, Tabellenköpfe (DE/EN), Pfade, Cache-TTL.
- **Logging/Fehlerbilder:** Rotierendes Log unverändert, aber UI-Logging konsistenter; ReportLab-Fehler wird verständlich erklärt.
- **UI-Feinschliff:** Auto-Fetch mit kleinem **Debounce**, konsistente Enable/Disable-Zustände, Kontextmenü bleibt, Sortierung numerisch/lexikographisch smarter.
- **Export/Excel/Stats:** Unverändert im Feature-Set, aber Code gestrafft; Spaltenbreiten-Logik bleibt, Top-10 & Team-Mittel stabil.
- **Druck/PDF:** Gleiche Optionen, aber Exceptions klarer; Zielordner standardisiert (`printouts`).
- **Wiederverwendbare Helpers:** Gemeinsame Routine für das Auswählen/Speichern der `gruppen.json` (keine doppelte Logik mehr).

Was du als Nächstes easy ergänzen könntest (optional, nice-to-have):

- **Unit-Tests** für `parse_group_pools()` (ein paar HTML-Fixtures reichen).
- **CLI-Modus** (argparse) für Headless-Exports.
- **Team-Filter in der GUI** (Search-Entry über der Treeview) plus „Nur gültige Q-TTR anzeigen“-Toggle.

Wenn du magst, passe ich die Refactor-Version direkt an deinen Stil (z. B. Black/ruff-Konfig, Namespacing in Module, oder Packaging mit `pyproject.toml`).

### 3. Benutzer

ja
