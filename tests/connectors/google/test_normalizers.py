from secondbrain.connectors.google import normalizers as N


def test_gmail_uses_headers_and_internaldate():
    ci = N.gmail_message({"id": "m1", "internalDate": "1700000000000", "snippet": "hello",
                          "payload": {"headers": [{"name": "Subject", "value": "Hi"}, {"name": "From", "value": "a@b"}]}})
    assert ci.title == "Hi" and ci.metadata["from"] == "a@b" and ci.source == "google_gmail"


def test_calendar_cancelled_skipped():
    assert N.calendar_event({"id": "e", "status": "cancelled"}) is None
    assert N.calendar_event({"id": "e", "summary": "S", "updated": "2026-01-01T00:00:00Z"}).source == "google_calendar"


def test_drive_removed_and_person_and_task():
    assert N.drive_change({"removed": True}) is None
    assert N.drive_change({"file": {"id": "f", "name": "a.txt", "modifiedTime": "2026-01-01T00:00:00Z"}}).external_id == "f"
    p = N.person({"resourceName": "people/1", "names": [{"displayName": "X"}],
                  "emailAddresses": [{"value": "x@y"}], "metadata": {"sources": [{"updateTime": "2026-01-01T00:00:00Z"}]}})
    assert p.metadata["emails"] == ["x@y"]
    assert N.task({"id": "t", "title": "Do", "updated": "2026-01-01T00:00:00Z"}).source == "google_tasks"
    assert N.task({"id": "t", "deleted": True}) is None
