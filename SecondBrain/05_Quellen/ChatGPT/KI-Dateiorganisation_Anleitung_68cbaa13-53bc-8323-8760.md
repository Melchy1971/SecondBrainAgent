---
title: "KI-Dateiorganisation Anleitung"
type: chatgpt_conversation
source: chatgpt
source_id: "68cbaa13-53bc-8323-8760-8962fb42c338"
created: 2025-09-18
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


# KI-Dateiorganisation Anleitung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68cbaa13-53bc-8323-8760-8962fb42c338`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

{"asset_pointer": "file-service://file-XWHPucp5VTcdQyxEWMFqbn", "content_type": "image_asset_pointer", "fovea": null, "height": 305, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 57049, "width": 737}
Du bist ein erfahrener Programmierer mit exzellenten Fähigkeiten in der Entwicklung von KI-Anwendungen und beherrschst mehrere Programmiersprachen. Deine Aufgabe besteht darin, eine Wissensdatenbank aufzubauen, die Daten aus verschiedenen Quellen wie Outlook, PSD-Dateien sowie Ordnern auf einem Laptop oder PC integriert. Eine Azure-Unternehmenslizenz ist bereits vorhanden, und die Datenbank wird eine benutzerfreundliche GUI besitzen, um verschiedene Module zu steuern. Modul eins konzentriert sich darauf, mithilfe von KI bestimmte Dateitypen in Ordnern zu identifizieren und zu organisieren.

Agiere in der Rolle eines KI-Programmierers und Datenbank-Architekten. Du verfügst über fundiertes Wissen in Azure, Datenverarbeitung und der Verwendung von KI-Algorithmen zur Dateianalyse. Deine Methoden sind effizient, strukturiert und anwenderfreundlich.

Die Zielgruppe sind Software-Entwickler, IT-Administratoren und Unternehmensleiter, die Interesse an der Implementierung von KI-gestützten Lösungen zur Datenorganisation und -verarbeitung haben.

Deine Aufgabe ist es, eine detaillierte Schritt-für-Schritt-Anleitung zu erstellen, die erklärt, wie man ein Modul entwickelt, das automatisch Word-, PowerPoint- und Excel-Dateien auf einem Laptop oder PC in einem strukturierten Ordner speichert. Beschreibe die notwendigen Technologien, die Integration in Azure und die Vorgehensweise zur Umsetzung dieser Funktionalität.

Die Ausgabe sollte im Fließtextformat erfolgen und die wichtigsten Schritte sowie Codebeispiele zur Veranschaulichung enthalten.

### 2. Assistent

Hier ist eine praxisnahe, durchgehende Anleitung – geschrieben aus der Perspektive eines KI-Programmierers und Datenbank-Architekten – wie du ein robustes Modul baust, das Word-, PowerPoint- und Excel-Dateien auf einem Laptop/PC automatisch erkennt, klassifiziert und in eine saubere Ordnerstruktur verschiebt, dabei Metadaten extrahiert und alles sauber in Azure integriert. Das Ganze ist bewusst schlank gehalten, damit es in echten Umgebungen zügig läuft und sich später zu einer umfassenden Wissensdatenbank (Outlook, PSD, weitere Quellen) ausbauen lässt.

Zuerst klärst du die Ziellinie: Die lokale „Agent“-Komponente beobachtet definierte Quellordner (z. B. Desktop, Downloads, Projektverzeichnisse), erkennt Office-Dateien zuverlässig, liest Kernmetadaten (Titel, Autor, Erstellungs-/Änderungsdatum), ordnet sie anhand einfacher Regeln oder eines leichten Klassifikators einem Zielschema zu und verschiebt/kopiert sie in eine konsistente Struktur, etwa `ZIELROOT/<Jahr>/<Monat>/<Typ>/<Projekt>/<Datei>`. Parallel sendet der Agent die Metadaten an Azure (Blob Storage + Datenbank/Index), damit die zentrale GUI deines Wissenssystems alles modulübergreifend anzeigen und steuern kann.

Technologisch genügt für den Agenten Python 3.10+ mit `watchdog` (Datei-Events), `pyyaml` (Konfiguration), `azure-identity` und `azure-storage-blob` (Cloud-Anbindung). Für Metadaten nutzt du den Office-Open-XML-Standard: DOCX/XLSX/PPTX sind ZIP-Container mit `docProps/core.xml`, die du ohne Office-Installation lesen kannst. Für die Azure-Seite richten Unternehmen mit vorhandener Azure-Lizenz Folgendes ein: ein Storage-Konto (Blob) für Dateien, Azure SQL oder Cosmos DB für Metadaten, optional Azure Cognitive Search zur Volltextsuche, Key Vault für Geheimnisse, Entra ID App-Registrierung (Service Principal) für den Agenten, sowie Application Insights für Telemetrie. Für fortgeschrittene Inhaltsklassifikation kannst du später Azure AI (z. B. Custom Text Classification oder Embeddings) hinzuschalten – starte aber mit regelbasierter Logik, damit das System von Tag 1 an Nutzen stiftet.

Die Umsetzung beginnt mit der Konfiguration. Definiere dein Zielschema, sensible Bereiche und Duplikatregeln (Hashing), sowie „Dry-Run“ und „Quarantäne“ für problematische Dateien. Eine einfache YAML-Konfiguration könnte so aussehen:

```yaml
# config.yaml
source_folders:
  - "C:/Users/ME/Desktop"
  - "C:/Users/ME/Downloads"
target_root: "D:/KnowledgeBase/office"
move_instead_of_copy: true
naming:
  pattern: "{year}/{month}/{type}/{project}/{safe_name}"
  project_rules:
    - match: ["angebot", "proposal", "p10"]
      project: "P10_Sales"
    - match: ["rechner", "calc", "kalkulation"]
      project: "Costing"
azure:
  blob_account_url: "https://<storageaccount>.blob.core.windows.net"
  container: "office-archive"
  use_managed_identity: false
  client_id: "<app-client-id>"
  tenant_id: "<tenant-id>"
  client_secret_env: "AZURE_CLIENT_SECRET"
runtime:
  dry_run: false
  quarantine: "D:/KnowledgeBase/quarantine"
```

Als nächstes implementierst du den Agenten. Der Kern läuft als Windows-Dienst (per Task Scheduler oder `nssm`) oder als Systemd-Service unter Linux. Der Code unten zeigt die komplette Pipeline: Erkennen, Metadaten auslesen, Zielpfad bauen, Kollisionen lösen, verschieben und optional nach Azure hochladen. Er ist so strukturiert, dass du ihn direkt in Produktion testen kannst.

```python
# requirements: watchdog pyyaml azure-identity azure-storage-blob
import hashlib, os, re, shutil, time, zipfile, xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import yaml

# --- Azure optional ---
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

OFFICE_TYPES = {
    ".docx": "word", ".doc": "word",
    ".xlsx": "excel", ".xls": "excel",
    ".pptx": "powerpoint", ".ppt": "powerpoint"
}

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def sha256(path: Path, block=1024*1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(block)
            if not data: break
            h.update(data)
    return h.hexdigest()

def read_office_coreprops(path: Path):
    meta = {"title": None, "author": None}
    try:
        # Office Open XML core properties
        with zipfile.ZipFile(path) as z:
            with z.open("docProps/core.xml") as core:
                tree = ET.parse(core)
                root = tree.getroot()
                ns = {
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                }
                title = root.find("dc:title", ns)
                creator = root.find("dc:creator", ns)
                meta["title"] = title.text if title is not None else None
                meta["author"] = creator.text if creator is not None else None
    except Exception:
        pass
    stat = path.stat()
    meta["created"] = datetime.fromtimestamp(stat.st_ctime)
    meta["modified"] = datetime.fromtimestamp(stat.st_mtime)
    return meta

def safe_name(name):
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name)

def infer_project(text_snippets, rules):
    text = " ".join([t.lower() for t in text_snippets if t])
    for rule in rules or []:
        if any(w.lower() in text for w in rule.get("match", [])):
            return rule.get("project")
    return "Unsorted"

def build_destination(p: Path, meta, cfg, ftype):
    year = meta["modified"].strftime("%Y")
    month = meta["modified"].strftime("%m")
    project = infer_project([meta.get("title"), p.name], cfg["naming"].get("project_rules"))
    base = cfg["naming"]["pattern"].format(
        year=year, month=month, type=ftype, project=project, safe_name=safe_name(p.name)
    )
    return Path(cfg["target_root"]) / base

def init_blob_client(cfg):
    if not cfg.get("azure"): return None
    az = cfg["azure"]
    if az.get("use_managed_identity", False):
        cred = DefaultAzureCredential()
    else:
        cred = ClientSecretCredential(tenant_id=az["tenant_id"], client_id=az["client_id"],
                                      client_secret=os.getenv(az["client_secret_env"]))
    return BlobServiceClient(account_url=az["blob_account_url"], credential=cred)

def upload_to_blob(blob_client, container, local_path: Path, dest_path: Path):
    try:
        container_client = blob_client.get_container_client(container)
        blob = container_client.get_blob_client(str(dest_path).replace("\\", "/"))
        with open(local_path, "rb") as data:
            blob.upload_blob(data, overwrite=True)
    except Exception as e:
        print(f"[BLOB] Upload fehlgeschlagen: {e}")

def move_or_copy(src: Path, dst: Path, move=True):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        # Kollisionsstrategie: Hash vergleichen, ggf. Suffix anhängen
        if sha256(src) == sha256(dst):
            return dst
        stem, ext = dst.stem, dst.suffix
        i = 1
        while True:
            cand = dst.with_name(f"{stem}__{i}{ext}")
            if not cand.exists():
                dst = cand; break
            i += 1
    if move:
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(str(src), str(dst))
    return dst

class OfficeHandler(FileSystemEventHandler):
    def __init__(self, cfg, blob_client=None):
        self.cfg = cfg
        self.blob = blob_client

    def process(self, path):
        p = Path(path)
        if not p.is_file(): return
        ext = p.suffix.lower()
        if ext not in OFFICE_TYPES: return
        # warten, bis Datei fertig geschrieben ist
        time.sleep(0.2)
        meta = read_office_coreprops(p)
        ftype = OFFICE_TYPES[ext]
        dst = build_destination(p, meta, self.cfg, ftype)
        print(f"[{ftype.upper()}] {p.name} -> {dst}")
        if self.cfg["runtime"]["dry_run"]:
            return
        try:
            final_path = move_or_copy(p, dst, move=self.cfg.get("move_instead_of_copy", True))
        except Exception as e:
            q = Path(self.cfg["runtime"]["quarantine"])/safe_name(p.name)
            Path(self.cfg["runtime"]["quarantine"]).mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(p), str(q))
            print(f"[WARN] Verschieben fehlgeschlagen, Datei in Quarantäne: {q} ({e})")
            return
        if self.blob:
            upload_to_blob(self.blob, self.cfg["azure"]["container"], final_path, dst.relative_to(self.cfg["target_root"]))

    def on_created(self, event): 
        if not event.is_directory: self.process(event.src_path)
    def on_moved(self, event): 
        if not event.is_directory: self.process(event.dest_path)

def main():
    cfg = load_config()
    blob_client = init_blob_client(cfg) if cfg.get("azure") else None
    handler = OfficeHandler(cfg, blob_client)
    obs = Observer()
    for src in cfg["source_folders"]:
        obs.schedule(handler, src, recursive=True)
        print(f"[WATCH] {src}")
    obs.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()

if __name__ == "__main__":
    main()
```

Damit ist die Baseline erledigt: Office-Dateien werden in Echtzeit sortiert und – falls gewünscht – zusätzlich nach Azure Blob gespiegelt. Der Code lässt sich problemlos als Windows-Dienst per Aufgabenplanung starten. Ein minimalistisches PowerShell-Skript für eine einmalige „Aufräumrunde“ (Batch-Verarbeitung) kann ergänzend nützlich sein:

```powershell
# Office-Dateien einmalig sortieren (rudimentär, ohne Metadaten)
param([string]$Source="C:\Users\ME\Downloads",[string]$Target="D:\KnowledgeBase\office")
Get-ChildItem -Path $Source -Recurse -Include *.doc,*.docx,*.xls,*.xlsx,*.ppt,*.pptx | ForEach-Object {
  $type = switch -Regex ($_.Extension.ToLower()) { "\.doc(x)?" {"word"} "\.xls(x)?" {"excel"} "\.ppt(x)?" {"powerpoint"} }
  $dt   = $_.LastWriteTime
  $dest = Join-Path $Target (Join-Path ($dt.ToString("yyyy")) (Join-Path ($dt.ToString("MM")) (Join-Path $type $_.Name)))
  New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
  Move-Item -Path $_.FullName -Destination $dest -Force
}
```

Für die Azure-Integration in die Gesamt-Wissensdatenbank gehst du behutsam, aber zielgerichtet vor. Zuerst legst du ein Storage-Konto und einen Container `office-archive` an. Dann hinterlegst du die Anmeldedaten (Client Secret oder Managed Identity) im Key Vault und verweist in der `config.yaml` nur auf Umgebungsvariablen/Managed Identity – Quellcode bleibt geheimnisfrei. Als Metadatenspeicher eignet sich Azure SQL (Tabellen `Files`, `HashIndex`, `Errors`), alternativ Cosmos DB, wenn du später viele nicht-relationale Quellen zusammenführst. Für schnelle Suche erstellst du einen Azure-Cognitive-Search-Index mit Feldern wie Pfad, Hash, Dateityp, Titel, Autor, Zeitstempel, Projekt. Ein kleines Azure Function-HTTP-Endpoint kann Metadaten entgegennehmen, validieren und in DB + Search schreiben; der Agent ruft es nach jedem erfolgreichen Move auf. In produktiven Umgebungen versiehst du den Call mit Entra-ID-geschütztem Tokenfluss (Client Credentials), Throttling sowie Retry mit Exponential Backoff.

Möchtest du den Klassifizierungsteil von „Regel-basiert“ zu „KI-gestützt“ heben, führst du eine kompakte Inhaltsanalyse ein: Office-Dateien sind ZIP-Container – du kannst den Klartext sehr günstig extrahieren (für DOCX `word/document.xml`, für PPTX die `ppt/slides/*.xml`, für XLSX z. B. `xl/sharedStrings.xml`). Aus den ersten paar tausend Zeichen baust du ein leichtes Feature-Set (TF-IDF) und trainierst im Azure Machine Learning Service einen linearen Klassifikator (LogReg/SVM) auf deine Projekte/Abteilungen. Das liefert robuste Labels wie „Sales/Proposal“, „Finance/Budget“, „Engineering/Specs“. Der Agent ersetzt dann die Funktion `infer_project(...)` durch einen Modellaufruf. Das ist ein nüchterner, skalierbarer Mittelweg – ohne die Latenz und Kosten großer Modelle.

Zur Qualitätssicherung gehört ein Dry-Run-Modus (nur loggen, nichts verschieben), die Quarantäne für gesperrte/beschädigte Dateien, Hash-basierte Duplikaterkennung und ein sauberes Log-Routing in Application Insights. Für Governance bindest du optional Purview/Microsoft Information Protection an, um später Sensitivitätslabels zuzuweisen – die Ordnerstruktur bleibt dabei unverändert, aber Richtlinien greifen.

Zum Deployment packst du den Agenten mit `pyinstaller` zu einem einzigen Executable, legst eine `config.yaml` daneben und registrierst einen geplanten Task „Beim Anmelden“ oder „Beim Systemstart“. Updates laufen, indem du die Binärdatei austauschst; die Konfiguration lässt sich aus Azure App Configuration ziehen, wenn du zentrale Steuerung bevorzugst.

Zum Abschluss ein winziges Snippet, wie der Agent Metadaten zusätzlich an eine Function postet (vereinfacht, mit Client-Credentials):

```python
import os, requests
from msal import ConfidentialClientApplication

def acquire_token(tenant, client_id, client_secret, scope):
    app = ConfidentialClientApplication(client_id, authority=f"https://login.microsoftonline.com/{tenant}",
                                        client_credential=client_secret)
    result = app.acquire_token_for_client(scopes=[scope])
    return result["access_token"]

def push_metadata(endpoint, token, payload):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(endpoint, json=payload, headers=headers, timeout=10)
    r.raise_for_status()

# usage after successful move:
payload = {
  "path": str(dst),
  "hash": sha256(dst),
  "type": ftype,
  "title": meta.get("title"),
  "author": meta.get("author"),
  "modified": meta["modified"].isoformat(),
  "project": project
}
token = acquire_token(tenant_id, client_id, os.getenv("AZURE_CLIENT_SECRET"), "api://your-app-id/.default")
push_metadata("https://<functionapp>.azurewebsites.net/api/ingest", token, payload)
```

Damit hast du ein produktionsreifes Modul 1: Es erkennt Office-Dateien lokal, organisiert sie zuverlässig, synchronisiert sie optional nach Azure und liefert die nötigen Metadaten für die übergeordnete GUI deiner Wissensdatenbank. Der Charme des Aufbaus liegt darin, dass du ohne Big-Bang starten kannst: erst Regeln, dann nach Bedarf ML; erst Blob/SQL, später Search, Outlook-Ingestion (über Microsoft Graph) und PSD-Analyse (XMP-Metadaten). Der nächste sinnvolle Schritt ist die GUI-Schicht mit einem kleinen Web-Dashboard, das die Logs live anzeigt, Regeln nachlädt und Dry-Run/Quarantäne per Schalter steuert.
