from secondbrain.connectors.microsoft import normalizers as N
from secondbrain.connectors.adapter_contract import ConnectorItem


def test_mail_message_maps_core_fields():
    ci = N.mail_message({"id": "m1", "subject": "Hi", "body": {"content": "Body"},
                         "from": {"emailAddress": {"address": "a@x.de"}},
                         "lastModifiedDateTime": "2026-01-02T03:04:05Z", "webLink": "http://l"})
    assert isinstance(ci, ConnectorItem)
    assert ci.external_id == "m1" and ci.source == "m365_mail"
    assert ci.metadata["from"] == "a@x.de"
    assert ci.updated_at.tzinfo is not None


def test_removed_tombstone_is_skipped():
    assert N.mail_message({"id": "m1", "@removed": {"reason": "deleted"}}) is None
    assert N.calendar_event({"id": "e", "@removed": {}}) is None
    assert N.drive_item({"id": "d", "@removed": {}}) is None


def test_teams_system_and_empty_messages_skipped():
    assert N.teams_message({"id": "t", "messageType": "systemEventMessage"}) is None
    assert N.teams_message({"id": "t", "body": {"content": "   "}}) is None
    ci = N.teams_message({"id": "t2", "body": {"content": "hello"},
                          "from": {"user": {"displayName": "Bob"}},
                          "lastModifiedDateTime": "2026-01-01T00:00:00Z"})
    assert ci.metadata["author"] == "Bob"


def test_each_resource_normalizer_returns_item():
    assert N.contact({"id": "c", "displayName": "X", "emailAddresses": [{"address": "x@y"}],
                      "lastModifiedDateTime": "2026-01-01T00:00:00Z"}).source == "m365_contacts"
    assert N.drive_item({"id": "f", "name": "a.txt", "file": {"mimeType": "text/plain"},
                         "lastModifiedDateTime": "2026-01-01T00:00:00Z"}).mime_type == "text/plain"
    assert N.todo_task({"id": "k", "title": "Do", "lastModifiedDateTime": "2026-01-01T00:00:00Z"}).source == "m365_todo"
    assert N.onenote_page({"id": "p", "title": "Page", "lastModifiedDateTime": "2026-01-01T00:00:00Z"}).source == "m365_onenote"
