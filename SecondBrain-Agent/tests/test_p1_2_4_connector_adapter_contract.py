from datetime import datetime, timezone

import pytest

from secondbrain.connectors.adapter_contract import (
    ConnectorContractError,
    ConnectorErrorCode,
    ConnectorItem,
    compute_content_hash,
    normalize_item,
    parse_datetime,
    validate_adapter,
)


def test_connector_item_normalizes_source_text_and_hashes_content():
    item = ConnectorItem(
        external_id="  A-1  ",
        source=" Gmail ",
        title="  Subject  ",
        content=" Body ",
        updated_at=datetime(2026, 1, 1),
    )

    assert item.external_id == "A-1"
    assert item.source == "gmail"
    assert item.title == "Subject"
    assert item.content == "Body"
    assert item.updated_at.tzinfo is not None
    assert item.content_hash == compute_content_hash(title="Subject", content="Body")


def test_connector_item_rejects_empty_identity():
    with pytest.raises(ConnectorContractError):
        ConnectorItem(
            external_id="",
            source="gmail",
            title="x",
            content="",
            updated_at=datetime.now(timezone.utc),
        )


def test_normalize_item_accepts_common_vendor_aliases():
    item = normalize_item(
        {
            "message_id": "m-42",
            "subject": "Hello",
            "body": "World",
            "timestamp": "2026-06-23T08:00:00Z",
            "url": "https://example.invalid/item/m-42",
            "content_type": "text/plain",
            "metadata": {"label": "inbox"},
        },
        source="gmail",
    )

    assert item.external_id == "m-42"
    assert item.title == "Hello"
    assert item.content == "World"
    assert item.updated_at.isoformat() == "2026-06-23T08:00:00+00:00"
    assert item.uri == "https://example.invalid/item/m-42"
    assert item.mime_type == "text/plain"
    assert item.metadata == {"label": "inbox"}


def test_parse_datetime_rejects_invalid_values():
    with pytest.raises(ConnectorContractError):
        parse_datetime("not-a-date")


def test_validate_adapter_accepts_protocol_shape():
    class Adapter:
        source = "drive"

        def fetch_changed(self, cursor=None):
            return []

    assert validate_adapter(Adapter()).source == "drive"


def test_validate_adapter_rejects_missing_contract():
    with pytest.raises(ConnectorContractError) as exc:
        validate_adapter(object())

    assert exc.value.code == ConnectorErrorCode.UNSUPPORTED_ITEM
