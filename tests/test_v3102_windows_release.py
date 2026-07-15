from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from secondbrain.install.app_home import DATA_SUBDIRS, ensure_layout, resolve_local_home, resolve_portable_home
from secondbrain.install.release_pipeline import (
    ReleaseValidationError,
    create_reproducible_zip,
    generate_sbom,
    validate_payload,
    verify_checksums,
    write_release_metadata,
)


def _payload(root: Path) -> Path:
    root.mkdir()
    (root / "Jarvis.exe").write_bytes(b"frozen-app")
    (root / "_internal").mkdir()
    (root / "_internal" / "asset.txt").write_text("asset", encoding="utf-8")
    return root


def test_portable_zip_is_reproducible_and_has_separate_data_marker(tmp_path: Path):
    source = _payload(tmp_path / "app")
    first = create_reproducible_zip(source, tmp_path / "one.zip")
    second = create_reproducible_zip(source, tmp_path / "two.zip")
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        assert ".portable" in archive.namelist()
        assert not any(name.startswith("data/") or "/tests/" in name for name in archive.namelist())


def test_payload_gate_blocks_secrets_runtime_tests_and_absolute_paths(tmp_path: Path):
    source = _payload(tmp_path / "app")
    (source / ".env").write_text("API_KEY=abcdefghijklmnopqrstuvwxyz", encoding="utf-8")
    (source / "local.txt").write_text(r"C:\Users\developer\repo", encoding="utf-8")
    with pytest.raises(ReleaseValidationError) as error:
        validate_payload(source)
    assert "forbidden:.env" in str(error.value)
    assert "absolute_path:local.txt" in str(error.value)


def test_release_manifest_sbom_and_checksums_are_machine_verifiable(tmp_path: Path):
    release = tmp_path / "release"
    release.mkdir()
    (release / "Jarvis-31.2.exe").write_bytes(b"installer")
    (release / "Jarvis-31.2.msi").write_bytes(b"msi")
    generate_sbom(release / "Jarvis-31.2-sbom.cdx.json", packages=[])
    _, manifest_path, checksums = write_release_metadata(
        release, version="31.2", notes="# Jarvis 31.2", published_at="2026-07-15T00:00:00+00:00"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert {row["name"] for row in manifest["artifacts"]} >= {
        "Jarvis-31.2.exe", "Jarvis-31.2.msi", "Jarvis-31.2-sbom.cdx.json", "RELEASE_NOTES.md"
    }
    assert checksums.exists() and verify_checksums(release)
    (release / "Jarvis-31.2.exe").write_bytes(b"tampered")
    assert not verify_checksums(release)


def test_installed_and_portable_paths_are_separate_and_writable(tmp_path: Path):
    env = {"APPDATA": str(tmp_path / "roaming"), "LOCALAPPDATA": str(tmp_path / "local")}
    portable = ensure_layout(resolve_portable_home(tmp_path / "program", env))
    installed_local = resolve_local_home(env)
    assert portable == tmp_path / "program" / "JarvisData"
    assert installed_local == tmp_path / "local" / "Jarvis"
    assert portable != installed_local
    assert all((portable / name).is_dir() for name in DATA_SUBDIRS)


def test_installer_defines_user_install_repair_data_retention_and_smoke():
    root = Path(__file__).resolve().parents[1]
    iss = (root / "packaging/windows/installer.iss").read_text(encoding="utf-8")
    build = (root / "packaging/windows/build.ps1").read_text(encoding="utf-8")
    assert "PrivilegesRequired=lowest" in iss
    assert "{localappdata}\\Programs\\{#AppName}" in iss
    assert "uninsneveruninstall" in iss
    assert "smoke-test" in iss
    assert "UsePreviousAppDir=yes" in iss
    assert "Downgrade blockiert" in iss
    assert "SkipMsi" in build and "release_pipeline" in build
    assert "installer_smoke.ps1" in build
