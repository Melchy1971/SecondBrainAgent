from __future__ import annotations

CONNECTOR_PAYLOADS = {
    "gmail_message": {
        "id": "msg-1",
        "threadId": "thread-1",
        "snippet": "Release gate notification",
        "payload": {"headers": [{"name": "Subject", "value": "RC ready"}]},
    },
    "drive_file": {
        "id": "file-1",
        "name": "Release Notes.md",
        "mimeType": "text/markdown",
        "webViewLink": "https://example.invalid/release-notes",
    },
    "calendar_event": {
        "id": "event-1",
        "summary": "RC review",
        "start": {"dateTime": "2026-07-08T09:00:00Z"},
        "end": {"dateTime": "2026-07-08T09:30:00Z"},
    },
}

DOCUMENT_TEXTS = {
    "release_note": "# Release\n\nAll gates must pass before tagging.\n",
    "minimal_markdown": "# Title\n\nBody text.\n",
}
