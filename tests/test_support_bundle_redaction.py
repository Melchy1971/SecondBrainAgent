"""Der Support-Bundle darf keine Secrets enthalten.

Der Bundle-Sammler und die rekursive Redaktion existieren bereits
(``support/bundle.py``, ``support/redaction.py``). Verdrahtet wurde er als
Launcher-Kommando ``support-bundle``. Dieser Test beweist, dass die Redaktion
tatsaechlich greift -- ein Support-Bundle, der Secrets durchreicht, ist
gefaehrlicher als keiner.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from secondbrain.support import redaction
from secondbrain.support.bundle import SupportBundle

SECRET = "s3cr3t-token-DO-NOT-LEAK"


# --------------------------------------------------------------------------
# Redaktions-Bausteine
# --------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["password", "api_key", "secret", "token", "authorization"])
def test_sensitive_keys_are_masked(key: str) -> None:
    result = redaction.redact({key: SECRET})
    assert SECRET not in json.dumps(result)


def test_dsn_credentials_are_masked() -> None:
    dsn = "postgresql://user:s3cr3t@db.example.com:5432/app"
    masked = redaction.redact_text(dsn)
    assert "s3cr3t" not in masked
    assert masked.startswith("postgresql://")   # Schema bleibt lesbar


def test_redaction_is_recursive() -> None:
    nested = {"outer": {"inner": {"api_key": SECRET}}, "list": [{"password": SECRET}]}
    blob = json.dumps(redaction.redact(nested))
    assert SECRET not in blob


def test_env_names_kept_values_masked() -> None:
    masked = redaction.redact_env({"OPENAI_API_KEY": SECRET, "PATH": "/usr/bin"})
    assert "OPENAI_API_KEY" in masked          # Name bleibt sichtbar
    assert masked["OPENAI_API_KEY"] != SECRET  # Wert nicht
    assert masked["PATH"] == "/usr/bin"        # unverfaengliches bleibt


# --------------------------------------------------------------------------
# Vollstaendiger Bundle
# --------------------------------------------------------------------------


def test_collected_bundle_has_no_plaintext_secret(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", SECRET)
    monkeypatch.setenv("DATABASE_URL", f"postgresql://u:{SECRET}@h:5432/db")

    bundle = SupportBundle(tmp_path).collect()
    blob = json.dumps(bundle, ensure_ascii=False)
    assert SECRET not in blob, "Secret ist im Support-Bundle durchgesickert"


def test_bundle_has_schema_and_sections(tmp_path) -> None:
    bundle = SupportBundle(tmp_path).collect()
    assert bundle["schema"].startswith("secondbrain.support.bundle")
    assert isinstance(bundle["sections"], dict) and bundle["sections"]


def test_zip_export_is_also_redacted(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", SECRET)
    bundle = SupportBundle(tmp_path)
    payload = bundle.collect()
    out = tmp_path / "support_bundle.zip"
    bundle.build_zip(out, bundle=payload)

    with zipfile.ZipFile(out) as zf:
        for name in zf.namelist():
            content = zf.read(name).decode("utf-8", errors="replace")
            assert SECRET not in content, f"Secret im ZIP-Eintrag {name}"


def test_bundle_is_offline(tmp_path) -> None:
    """Der Bundle-Aufbau darf keine Netzwerkbibliothek importieren/aufrufen.

    Statische Pruefung: das Modul zieht kein requests/httpx/urllib.request.
    """
    source = Path(SupportBundle.__module__.replace(".", "/"))
    text = (Path(__file__).resolve().parents[1] / "SecondBrain" / "support" / "bundle.py").read_text(encoding="utf-8")
    for lib in ("import requests", "import httpx", "urllib.request", "socket.socket"):
        assert lib not in text, f"support-bundle nutzt Netzwerk: {lib}"
