from pathlib import Path
import json
import re
from .utils import read_text_safe

def try_import_pypdf():
    try:
        from pypdf import PdfReader
        return PdfReader
    except Exception:
        return None

def extract_pdf_text(path: Path) -> str:
    PdfReader = try_import_pypdf()
    if PdfReader is None:
        return f"""PDF-Datei erkannt: {path.name}

Status:
PDF-Textextraktion benötigt das optionale Paket `pypdf`.

Installation:
pip install pypdf

Nach Installation erneut importieren.
"""

    try:
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(f"## Seite {i}\n\n{text.strip()}")
        joined = "\n\n".join(pages).strip()
        if not joined:
            return f"PDF-Datei erkannt: {path.name}\n\nKein Text extrahierbar. OCR-Fallback erforderlich."
        return joined
    except Exception as exc:
        return f"PDF-Importfehler bei {path.name}: {exc}"

def try_import_requests():
    try:
        import requests
        return requests
    except Exception:
        return None

def try_import_bs4():
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except Exception:
        return None

def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s)>\"]+", text)

def fetch_web_text(url: str) -> str:
    requests = try_import_requests()
    BeautifulSoup = try_import_bs4()

    if requests is None or BeautifulSoup is None:
        return f"""URL erkannt: {url}

Status:
Webseiten-Import benötigt optionale Pakete.

Installation:
pip install requests beautifulsoup4
"""

    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "SecondBrain-Agent/0.4"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else url
        text = soup.get_text("\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean = "\n".join(lines[:400])
        return f"# {title}\n\nQuelle: {url}\n\n{clean}"
    except Exception as exc:
        return f"Webseiten-Importfehler bei {url}: {exc}"

def parse_chat_json(raw: str, source_name: str) -> str:
    try:
        data = json.loads(raw)
    except Exception:
        return raw

    chunks = []

    if isinstance(data, list):
        for idx, item in enumerate(data, start=1):
            if isinstance(item, dict):
                title = item.get("title") or item.get("name") or f"Eintrag {idx}"
                chunks.append(f"# {title}")
                for key in ["create_time", "created_at", "update_time", "updated_at"]:
                    if key in item:
                        chunks.append(f"{key}: {item[key]}")
                if "mapping" in item:
                    chunks.append("ChatGPT mapping erkannt. Rohstruktur gekürzt importiert.")
                chunks.append(json.dumps(item, ensure_ascii=False, indent=2)[:8000])
            else:
                chunks.append(str(item))
        return "\n\n".join(chunks)

    if isinstance(data, dict):
        title = data.get("title") or data.get("name") or source_name
        chunks.append(f"# {title}")
        for key in ["messages", "conversation", "mapping"]:
            if key in data:
                chunks.append(f"## {key}")
                chunks.append(json.dumps(data[key], ensure_ascii=False, indent=2)[:12000])
        if len(chunks) == 1:
            chunks.append(json.dumps(data, ensure_ascii=False, indent=2)[:12000])
        return "\n\n".join(chunks)

    return raw

def read_input_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return extract_pdf_text(path)

    if suffix == ".json":
        raw = read_text_safe(path)
        return parse_chat_json(raw, path.name)

    if suffix in [".txt", ".md", ".csv", ".eml"]:
        raw = read_text_safe(path)
        urls = extract_urls(raw)
        if path.parent.name.lower() in ["webseiten", "youtube"] and urls:
            fetched = [fetch_web_text(url) for url in urls[:5]]
            return raw + "\n\n# Abgerufene Inhalte\n\n" + "\n\n---\n\n".join(fetched)
        return raw

    return f"Nicht unterstützter Dateityp: {path.name}"
