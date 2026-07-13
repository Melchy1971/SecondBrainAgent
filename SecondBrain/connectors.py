
# Compatibility shim: allow this legacy module file to also behave like a package
# so imports such as secondbrain.connectors.<module> resolve to secondbrain/connectors/.
from pathlib import Path as _SecondBrainPath
__path__ = [str(_SecondBrainPath(__file__).with_suffix(''))]
from pathlib import Path
import json
import imaplib
import email
from email.header import decode_header
from .utils import now_date, slugify, ensure_unique_path

def _decode_header(value: str) -> str:
    if not value:
        return ""
    decoded = decode_header(value)
    out = ""
    for part, enc in decoded:
        if isinstance(part, bytes):
            out += part.decode(enc or "utf-8", errors="ignore")
        else:
            out += part
    return out

def import_imap_to_inbox(settings: dict, host: str, username: str, password: str, mailbox: str = "INBOX", limit: int = 25) -> list[Path]:
    inbox = Path(settings["inbox_path"]) / "Emails" / "IMAP"
    inbox.mkdir(parents=True, exist_ok=True)

    created = []
    mail = imaplib.IMAP4_SSL(host)
    mail.login(username, password)
    mail.select(mailbox)

    status, data = mail.search(None, "ALL")
    ids = data[0].split()[-limit:]

    for msg_id in ids:
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        if status != "OK":
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        subject = _decode_header(msg.get("Subject", "Ohne Betreff"))
        sender = _decode_header(msg.get("From", ""))
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

        md = f"# {subject}\n\nFrom: {sender}\nDate: {date}\n\n{body}"
        target = ensure_unique_path(inbox / f"{now_date()}_{slugify(subject)}.eml.md")
        target.write_text(md, encoding="utf-8")
        created.append(target)

    mail.logout()
    return created

def import_browser_bookmarks(settings: dict, bookmarks_path: str, browser: str) -> Path:
    source = Path(bookmarks_path)
    inbox = Path(settings["inbox_path"]) / "Browser" / browser
    inbox.mkdir(parents=True, exist_ok=True)
    target = inbox / f"{now_date()}_{browser.lower()}_bookmarks.md"

    data = json.loads(source.read_text(encoding="utf-8"))
    lines = [f"# {browser} Bookmarks", "", f"Quelle: `{source}`", ""]

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "url":
                lines.append(f"- [{node.get('name','Bookmark')}]({node.get('url','')})")
            for child in node.get("children", []):
                walk(child)

    walk(data.get("roots", data))
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
