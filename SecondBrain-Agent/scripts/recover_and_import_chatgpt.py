"""Rettet Konversationsdaten aus einer abgeschnittenen ChatGPT-Export-ZIP und importiert sie.

Hintergrund
-----------
Die Datei chatgpd23062026.zip (275 MB) ist beim Download/Transfer abgeschnitten
worden: Sie beginnt korrekt mit dem ZIP-Magic (PK\\x03\\x04), aber das zentrale
Verzeichnis am Dateiende fehlt (keine EOCD-Signatur PK\\x05\\x06, null Central-
Directory-Eintraege). Deshalb meldet das Betriebssystem "Zip archive", waehrend
Python/zipfile mit BadZipFile abbricht - zipfile liest das Verzeichnis am Ende.

Die Konversationsdaten selbst stehen am Anfang der Datei und sind unversehrt.
Dieses Skript scannt die lokalen Datei-Header (PK\\x03\\x04), dekomprimiert die
Eintraege conversations-*.json (und conversation_asset_file_names.json) per
Roh-Deflate, validiert sie als JSON und schreibt sie in eine intakte ZIP.
Anschliessend laeuft der regulaere, fuer das Splitformat gepatchte Importer.

Nutzung
-------
    python scripts\\recover_and_import_chatgpt.py
    python scripts\\recover_and_import_chatgpt.py "C:\\Pfad\\zur\\kaputten.zip"
    python scripts\\recover_and_import_chatgpt.py "...zip" --no-semantic
"""
from __future__ import annotations

import json
import struct
import sys
import zlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.chatgpt_importer.importer import import_chatgpt_zip

DEFAULT_BROKEN = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\ChatGPT\chatgpd23062026.zip")
EXPORTS_DIR = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\ChatGPT\exports")

# Welche Eintraege gerettet werden sollen (Praefix-Match auf den Dateinamen)
WANTED_PREFIXES = ("conversations-", "conversations.json", "conversation_asset_file_names.json")

LOCAL_HEADER_SIG = b"PK\x03\x04"


def _wanted(name: str) -> bool:
    base = name.rsplit("/", 1)[-1]
    return base.startswith("conversations-") or base in (
        "conversations.json",
        "conversation_asset_file_names.json",
    )


def salvage_entries(broken_zip: Path) -> dict[str, bytes]:
    """Liest verwertbare JSON-Eintraege aus einer abgeschnittenen ZIP.

    Geht ueber die lokalen Datei-Header (Dateianfang), statt ueber das fehlende
    zentrale Verzeichnis. Gibt {dateiname: rohbytes} fuer valide JSON zurueck.
    """
    data = broken_zip.read_bytes()

    # Offsets aller lokalen Header sammeln, plus Sentinel am Dateiende
    offsets: list[int] = []
    pos = 0
    while True:
        idx = data.find(LOCAL_HEADER_SIG, pos)
        if idx < 0:
            break
        offsets.append(idx)
        pos = idx + 4
    offsets.append(len(data))

    recovered: dict[str, bytes] = {}
    for i in range(len(offsets) - 1):
        j = offsets[i]
        try:
            method = struct.unpack("<H", data[j + 8:j + 10])[0]
            csize = struct.unpack("<I", data[j + 18:j + 22])[0]
            name_len = struct.unpack("<H", data[j + 26:j + 28])[0]
            extra_len = struct.unpack("<H", data[j + 28:j + 30])[0]
            name = data[j + 30:j + 30 + name_len].decode("utf-8", "replace")
        except Exception:
            continue

        if not _wanted(name):
            continue

        start = j + 30 + name_len + extra_len
        comp = data[start:start + csize] if csize > 0 else data[start:offsets[i + 1]]

        try:
            raw = zlib.decompress(comp, -15) if method == 8 else comp
        except Exception:
            # Defekter / abgeschnittener Eintrag - ueberspringen
            continue

        try:
            json.loads(raw.decode("utf-8"))
        except Exception:
            continue

        recovered[name.rsplit("/", 1)[-1]] = raw

    return recovered


def build_clean_zip(entries: dict[str, bytes], out_zip: Path) -> Path:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_zip, "w", ZIP_DEFLATED) as zf:
        for name in sorted(entries):
            zf.writestr(name, entries[name])
    # Gegencheck: laesst sich die neue ZIP fehlerfrei oeffnen?
    with ZipFile(out_zip, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"Reparierte ZIP defekt bei: {bad}")
    return out_zip


def main() -> int:
    args = [a for a in sys.argv[1:]]
    update_semantic = "--no-semantic" not in args
    args = [a for a in args if a != "--no-semantic"]
    broken = Path(args[0]) if args else DEFAULT_BROKEN

    if not broken.exists():
        print(f"FEHLER: ZIP nicht gefunden: {broken}")
        return 1

    print(f"Lese kaputte ZIP: {broken}  ({broken.stat().st_size} Bytes)")
    entries = salvage_entries(broken)

    conv_files = sorted(n for n in entries if n.startswith("conversations-") or n == "conversations.json")
    if not conv_files:
        print("FEHLER: Keine verwertbaren conversations-Dateien gefunden. "
              "Die Datei ist vermutlich vor dem Konversationsteil abgeschnitten - "
              "bitte Export neu herunterladen.")
        return 2

    total = 0
    for n in conv_files:
        total += len(json.loads(entries[n].decode("utf-8")))
    print(f"Gerettete Konversationsdateien: {conv_files}")
    print(f"Konversationen gesamt: {total}")

    out_zip = EXPORTS_DIR / (broken.stem + "_repariert.zip")
    build_clean_zip(entries, out_zip)
    print(f"Reparierte ZIP geschrieben: {out_zip}")

    report = import_chatgpt_zip(
        zip_path=out_zip,
        update_semantic_search=update_semantic,
        update_secondbrain_os=False,
    )
    print("---")
    print("Import abgeschlossen.")
    print("Importiert:", report["imported_count"])
    print("Fehler:", report["error_count"])
    print("Report:", report["report_md"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
