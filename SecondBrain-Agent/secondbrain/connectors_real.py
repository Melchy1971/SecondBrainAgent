from pathlib import Path
import json
import imaplib
import email
from email.header import decode_header
from .utils import now_date, now_datetime, slugify, ensure_unique_path, read_text_safe

def decode_mime(value: str) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            out += part.decode(enc or "utf-8", errors="ignore")
        else:
            out += str(part)
    return out

def import_imap(settings: dict, host: str, username: str, password: str, mailbox: str = "INBOX", limit: int = 25, mark_seen: bool = False) -> list[Path]:
    inbox = Path(settings["inbox_path"]) / "Emails" / "IMAP"
    inbox.mkdir(parents=True, exist_ok=True)
    created = []

    mail = imaplib.IMAP4_SSL(host)
    mail.login(username, password)
    mail.select(mailbox)

    status, data = mail.search(None, "ALL")
    if status != "OK":
        mail.logout()
        return created

    ids = data[0].split()[-limit:]
    for msg_id in ids:
        fetch_mode = "(RFC822)" if mark_seen else "(BODY.PEEK[])"
        status, msg_data = mail.fetch(msg_id, fetch_mode)
        if status != "OK" or not msg_data or not msg_data[0]:
            continue

        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        subject = decode_mime(msg.get("Subject", "Ohne Betreff"))
        sender = decode_mime(msg.get("From", ""))
        date = msg.get("Date", "")
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = str(part.get("Content-Disposition"))
                if ctype == "text/plain" and "attachment" not in disp:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")

        md = f"""---
title: "{subject}"
type: email
provider: imap
created: {now_date()}
tags:
  - email
---

# {subject}

From: {sender}
Date: {date}

## Inhalt

{body}
"""
        target = ensure_unique_path(inbox / f"{now_date()}_{slugify(subject)}.md")
        target.write_text(md, encoding="utf-8")
        created.append(target)

    mail.logout()
    return created

def import_browser_bookmarks(settings: dict, bookmarks_path: str, browser: str) -> Path:
    source = Path(bookmarks_path)
    inbox = Path(settings["inbox_path"]) / "Browser" / "Bookmarks"
    inbox.mkdir(parents=True, exist_ok=True)
    target = ensure_unique_path(inbox / f"{now_date()}_{browser.lower()}_bookmarks.md")

    data = json.loads(source.read_text(encoding="utf-8"))
    lines = [
        "---",
        f"title: \"{browser} Bookmarks\"",
        "type: browser_bookmarks",
        f"provider: {browser}",
        f"created: {now_date()}",
        "tags:",
        "  - browser",
        "  - bookmarks",
        "---",
        "",
        f"# {browser} Bookmarks",
        "",
    ]

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "url":
                lines.append(f"- [{node.get('name','Bookmark')}]({node.get('url','')})")
            for child in node.get("children", []):
                walk(child)

    walk(data.get("roots", data))
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

def index_code_repository(settings: dict, repo_path: str) -> Path:
    repo = Path(repo_path)
    inbox = Path(settings["inbox_path"]) / "Code"
    inbox.mkdir(parents=True, exist_ok=True)
    target = ensure_unique_path(inbox / f"{now_date()}_{slugify(repo.name)}_code-index.md")

    exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json", ".yaml", ".yml", ".toml"}
    rows = []
    for p in repo.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts and ".git" not in p.parts and "node_modules" not in p.parts:
            try:
                rel = p.relative_to(repo)
                rows.append((str(rel), p.suffix, p.stat().st_size))
            except Exception:
                pass

    lines = [
        "---",
        f"title: \"Code Index {repo.name}\"",
        "type: code_index",
        f"created: {now_date()}",
        "tags:",
        "  - code",
        "---",
        "",
        f"# Code Index: {repo.name}",
        "",
        "| Datei | Typ | Bytes |",
        "|---|---|---:|",
    ]
    for rel, ext, size in rows[:1000]:
        lines.append(f"| `{rel}` | `{ext}` | {size} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
