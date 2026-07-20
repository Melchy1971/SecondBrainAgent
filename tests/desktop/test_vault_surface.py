from secondbrain.desktop_native.vault_surface import vault_status_labels


def test_vault_snapshot_is_projected_to_bounded_labels() -> None:
    assert vault_status_labels(
        {"vault_exists": True, "markdown_files": 42, "inbox_files": 3, "path": "secret"}
    ) == {"markdown": "42", "vault": "Ready", "inbox": "3 Files"}


def test_missing_vault_and_negative_counts_are_normalized() -> None:
    assert vault_status_labels(
        {"vault_exists": False, "markdown_files": -1, "inbox_files": -2}
    ) == {"markdown": "0", "vault": "Missing", "inbox": "0 Files"}


def test_invalid_snapshot_degrades_without_details() -> None:
    assert vault_status_labels({"markdown_files": "invalid", "inbox_files": 1}) == {
        "markdown": "Unavailable",
        "vault": "Unknown",
        "inbox": "Unavailable",
    }
