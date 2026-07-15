from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from secondbrain.installer_update import InstallerUpdateRuntime, UpdateCenterViewModel, UpdateError


def _package(files: dict[str, str]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    return stream.getvalue()


def _manifest(private_key: Ed25519PrivateKey, package: bytes, **changes):
    value = {
        "schema_version": 1,
        "application_version": "31.1",
        "build": "3101",
        "channel": "stable",
        "published_at": "2026-07-15T12:00:00+00:00",
        "minimum_supported_version": "15.0",
        "package_url": "https://updates.example.test/app.zip",
        "package_size": len(package),
        "sha256": hashlib.sha256(package).hexdigest(),
        "signature": "",
        "signing_key_id": "release-2026",
        "migrations": [{"id": "3101-schema"}],
        "release_notes": "Signed updater",
        "rollout_percentage": 100,
        "mandatory": False,
    }
    value.update(changes)
    payload = json.dumps({k: v for k, v in value.items() if k != "signature"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    value["signature"] = base64.b64encode(private_key.sign(payload)).decode()
    return value


@pytest.fixture
def update_fixture(tmp_path: Path):
    (tmp_path / "secondbrain").mkdir()
    (tmp_path / "secondbrain" / "old.py").write_text("old", encoding="utf-8")
    (tmp_path / "launcher.py").write_text("old", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "user.txt").write_text("keep", encoding="utf-8")
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    package = _package({"launcher.py": "new", "secondbrain/new.py": "new"})
    updater = InstallerUpdateRuntime(tmp_path, current_version="31.0", trusted_keys={"release-2026": public}, installation_id="test")
    return updater, key, package, tmp_path


def test_valid_signature_is_accepted_and_gui_exposes_release(update_fixture):
    updater, key, package, _ = update_fixture
    manifest = _manifest(key, package)
    assert updater.check_for_updates(manifest)["status"] == "available"
    gui = UpdateCenterViewModel(updater)
    assert gui.refresh(manifest)["release_notes"] == "Signed updater"


def test_invalid_signature_and_hash_are_blocked(update_fixture):
    updater, key, package, tmp_path = update_fixture
    manifest = _manifest(key, package)
    manifest["signature"] = base64.b64encode(b"x" * 64).decode()
    assert updater.check_for_updates(manifest)["error"] == "signature_invalid"

    valid = _manifest(key, package)
    downloaded = tmp_path / "bad.zip"
    downloaded.write_bytes(package + b"tampered")
    with pytest.raises(UpdateError, match="hash_mismatch"):
        updater.install_update(valid, downloaded)


def test_migration_failure_rolls_back_and_preserves_user_data(update_fixture):
    updater, key, package, root = update_fixture
    manifest = _manifest(key, package)
    package_path = root / "runtime" / "updates" / "package.zip"
    package_path.write_bytes(package)
    updater.migration_runner = lambda migrations, root: (_ for _ in ()).throw(RuntimeError("migration failed"))
    result = updater.install_update(manifest, package_path)
    assert result["status"] == "rolled_back"
    assert (root / "launcher.py").read_text(encoding="utf-8") == "old"
    assert (root / "data" / "user.txt").read_text(encoding="utf-8") == "keep"
    assert any(row["action"] == "rollback" for row in updater.update_history())


def test_downgrade_channel_unsigned_stable_and_offline_are_controlled(update_fixture):
    updater, key, package, _ = update_fixture
    assert updater.check_for_updates(_manifest(key, package, application_version="30.9"))["error"] == "downgrade_blocked"
    unsigned = _manifest(key, package)
    unsigned["signature"] = ""
    assert updater.check_for_updates(unsigned)["error"] == "signature_invalid"
    assert updater.switch_channel("beta")["channel"] == "beta"
    assert updater.check_for_updates(_manifest(key, package))["error"] == "channel_mismatch"

    offline = InstallerUpdateRuntime(
        updater.root,
        manifest_url="https://updates.example.test/manifest.json",
        fetcher=lambda url, target: (_ for _ in ()).throw(UpdateError("offline")),
    )
    assert offline.check_for_updates()["status"] == "offline"


def test_download_validates_package_hash(update_fixture):
    updater, key, package, _ = update_fixture
    manifest = _manifest(key, package)

    def fetch(url: str, target: Path | None):
        assert target is not None
        target.write_bytes(package)
        return target

    updater.fetcher = fetch
    assert updater.download_update(manifest).read_bytes() == package
