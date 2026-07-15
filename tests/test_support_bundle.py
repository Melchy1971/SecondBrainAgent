"""Tests for the v31.00 support center: bundle collection, ZIP export, redaction."""

from __future__ import annotations

import json
import zipfile

import pytest

from secondbrain.support import redaction
from secondbrain.support.bundle import SECTIONS, SupportBundle
from secondbrain.support.center import render_center_html, run_support_center

_SECRETS = ["sk-LEAKME1234567890xyz", "hunter2LEAK", "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345", "sk-ENVLEAKvalue999999"]


def _seed(root):
    (root / "config").mkdir(exist_ok=True)
    (root / "config" / "settings.yaml").write_text(
        "openai_api_key: sk-LEAKME1234567890xyz\ndb_password: hunter2LEAK\nplace: Zaberfeld\n", encoding="utf-8")
    (root / "runtime").mkdir(exist_ok=True)
    (root / "runtime" / "app.log").write_text("INFO start\nDEBUG token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345\n", encoding="utf-8")


# -- redaction ---------------------------------------------------------------

def test_redact_text_masks_secret_shapes():
    assert redaction.redact_text("api_key=sk-abcdef1234567890") == "[REDACTED]"
    assert "hunter2" not in redaction.redact_text("db_password: hunter2secret")
    assert "ghp_" not in redaction.redact_text("token=ghp_ABCDEFGHIJKLMNOPQRSTUVWX")
    assert redaction.redact_text("postgres://user:pw@host/db").endswith("@host/db")
    assert "pw" not in redaction.redact_text("postgres://user:pw@host/db").split("@")[0]


def test_is_sensitive_key_and_recursive_redaction():
    assert redaction.is_sensitive_key("DB_PASSWORD")
    assert not redaction.is_sensitive_key("place")
    red = redaction.redact({"password": "x", "nested": {"api_key": "y", "ok": "keep"}})
    assert red["password"] == redaction.REDACTED
    assert red["nested"]["api_key"] == redaction.REDACTED
    assert red["nested"]["ok"] == "keep"


def test_redact_env_masks_values_keeps_names(monkeypatch):
    env = {"OPENAI_API_KEY": "sk-x", "HOME": "/home/x"}
    out = redaction.redact_env(env)
    assert out["OPENAI_API_KEY"] == redaction.REDACTED
    assert out["HOME"] == "/home/x"


# -- bundle ------------------------------------------------------------------

def test_collect_has_all_sections(tmp_path):
    bundle = SupportBundle(tmp_path).collect()
    assert bundle["schema"] == "secondbrain.support.bundle.v1"
    assert set(bundle["sections"]) == set(SECTIONS)


def test_section_failure_is_isolated(tmp_path):
    class Boom(SupportBundle):
        def _system_info(self):
            return self._safe(lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    bundle = Boom(tmp_path).collect()
    assert bundle["sections"]["system_info"]["ok"] is False
    # other sections still present and fine
    assert bundle["sections"]["diagnose"]["ok"] is True


def test_build_zip_is_valid_and_structured(tmp_path):
    _seed(tmp_path)
    out = SupportBundle(tmp_path).build_zip(tmp_path / "b.zip")
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    assert "support_bundle.json" in names
    assert any(n.startswith("sections/") for n in names)


# -- redaction end-to-end (Akzeptanz: Secrets automatisch entfernen) ---------

def test_no_secrets_in_bundle_or_zip(tmp_path, monkeypatch):
    _seed(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-ENVLEAKvalue999999")
    sb = SupportBundle(tmp_path)
    bundle = sb.collect()
    blob = json.dumps(bundle, ensure_ascii=False)
    for secret in _SECRETS:
        assert secret not in blob

    zpath = sb.build_zip(tmp_path / "b.zip", bundle=bundle)
    zblob = ""
    with zipfile.ZipFile(zpath) as zf:
        for n in zf.namelist():
            zblob += zf.read(n).decode("utf-8", "replace")
    for secret in _SECRETS:
        assert secret not in zblob


# -- center ------------------------------------------------------------------

def test_run_support_center_writes_artifacts(tmp_path):
    _seed(tmp_path)
    run_support_center(tmp_path)
    art = tmp_path / "OUTPUTS" / "v31.00-support-center"
    assert (art / "support_bundle.zip").exists()
    assert (art / "support_bundle.json").exists()
    assert (art / "support_center.html").exists()


def test_center_html_wellformed(tmp_path):
    bundle = SupportBundle(tmp_path).collect()
    html = render_center_html(bundle)
    assert html.startswith("<!doctype html>") and "SUPPORT CENTER" in html
    assert "REDACTED" in html or "bereinigt" in html
