"""Tests für die zentrale RuntimeConfig: Prioritäten, BLOCKED, Secret-Referenzen."""

from __future__ import annotations

import json
from pathlib import Path

from secondbrain.runtime_config import RuntimeConfig
from secondbrain.runtime_config.service import SECRET_MASK, STATUS_BLOCKED, STATUS_OK
from secondbrain.runtime_config.sources import (
    SOURCE_APPDATA, SOURCE_DEFAULT, SOURCE_DOTENV, SOURCE_ENV, SOURCE_WORKSPACE,
)


def make_config(tmp_path: Path, env: dict[str, str] | None = None) -> RuntimeConfig:
    return RuntimeConfig(tmp_path / "ws", env=env or {}, home=tmp_path / "appdata")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


# --- Prioritäten -----------------------------------------------------------

def test_default_wins_when_no_source_set(tmp_path: Path):
    cfg = make_config(tmp_path)
    resolved = cfg.resolve()
    assert resolved["values"]["SECONDBRAIN_EMBEDDING_PROVIDER"] == "local"
    assert resolved["origins"]["SECONDBRAIN_EMBEDDING_PROVIDER"] == SOURCE_DEFAULT


def test_appdata_overrides_default(tmp_path: Path):
    cfg = make_config(tmp_path)
    write_json(cfg.appdata_config_path, {"SECONDBRAIN_GUI_PORT": "9000"})
    resolved = cfg.resolve()
    assert resolved["values"]["SECONDBRAIN_GUI_PORT"] == "9000"
    assert resolved["origins"]["SECONDBRAIN_GUI_PORT"] == SOURCE_APPDATA


def test_workspace_overrides_appdata(tmp_path: Path):
    cfg = make_config(tmp_path)
    write_json(cfg.appdata_config_path, {"SECONDBRAIN_GUI_PORT": "9000"})
    write_json(cfg.workspace_config_path, {"SECONDBRAIN_GUI_PORT": "9100"})
    resolved = cfg.resolve()
    assert resolved["values"]["SECONDBRAIN_GUI_PORT"] == "9100"
    assert resolved["origins"]["SECONDBRAIN_GUI_PORT"] == SOURCE_WORKSPACE


def test_dotenv_overrides_workspace(tmp_path: Path):
    cfg = make_config(tmp_path)
    write_json(cfg.workspace_config_path, {"SECONDBRAIN_GUI_PORT": "9100"})
    cfg.dotenv_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.dotenv_path.write_text("SECONDBRAIN_GUI_PORT=9200\n", encoding="utf-8")
    resolved = cfg.resolve()
    assert resolved["values"]["SECONDBRAIN_GUI_PORT"] == "9200"
    assert resolved["origins"]["SECONDBRAIN_GUI_PORT"] == SOURCE_DOTENV


def test_environ_overrides_everything(tmp_path: Path):
    cfg = make_config(tmp_path, env={"SECONDBRAIN_GUI_PORT": "9300"})
    write_json(cfg.workspace_config_path, {"SECONDBRAIN_GUI_PORT": "9100"})
    cfg.dotenv_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.dotenv_path.write_text("SECONDBRAIN_GUI_PORT=9200\n", encoding="utf-8")
    resolved = cfg.resolve()
    assert resolved["values"]["SECONDBRAIN_GUI_PORT"] == "9300"
    assert resolved["origins"]["SECONDBRAIN_GUI_PORT"] == SOURCE_ENV


# --- Secrets ----------------------------------------------------------------

def test_secret_value_in_json_is_ignored_and_reported(tmp_path: Path):
    cfg = make_config(tmp_path)
    write_json(cfg.workspace_config_path, {"OPENAI_API_KEY": "sk-plaintext"})
    resolved = cfg.resolve()
    assert resolved["values"]["OPENAI_API_KEY"] == ""
    assert any("Referenz" in issue for issue in resolved["issues"])


def test_secret_resolved_via_reference_from_env(tmp_path: Path):
    cfg = make_config(tmp_path, env={"MY_CUSTOM_KEY": "sk-fromenv"})
    write_json(cfg.workspace_config_path, {"OPENAI_API_KEY": {"ref": "MY_CUSTOM_KEY"}})
    resolved = cfg.resolve()
    assert resolved["values"]["OPENAI_API_KEY"] == "sk-fromenv"
    assert resolved["origins"]["OPENAI_API_KEY"] == SOURCE_ENV


def test_snapshot_masks_secrets(tmp_path: Path):
    cfg = make_config(tmp_path, env={"OPENAI_API_KEY": "sk-secret"})
    snapshot = cfg.snapshot()
    fields = {f["key"]: f for s in snapshot["sections"] for f in s["fields"]}
    assert fields["OPENAI_API_KEY"]["value"] == SECRET_MASK
    assert "sk-secret" not in json.dumps(snapshot)


def test_set_values_writes_secret_to_dotenv_not_json(tmp_path: Path):
    cfg = make_config(tmp_path)
    cfg.project_root.mkdir(parents=True, exist_ok=True)
    result = cfg.set_values({"OPENAI_API_KEY": "sk-new", "SECONDBRAIN_GUI_PORT": "9999"})
    assert result["ok"], result
    assert "OPENAI_API_KEY=sk-new" in cfg.dotenv_path.read_text(encoding="utf-8")
    stored = json.loads(cfg.workspace_config_path.read_text(encoding="utf-8"))
    assert stored == {"SECONDBRAIN_GUI_PORT": "9999"}


def test_set_values_skips_masked_secret(tmp_path: Path):
    cfg = make_config(tmp_path)
    cfg.project_root.mkdir(parents=True, exist_ok=True)
    result = cfg.set_values({"OPENAI_API_KEY": SECRET_MASK})
    assert result["ok"]
    assert result["written"] == []
    assert not cfg.dotenv_path.exists()


# --- Validierung / BLOCKED ---------------------------------------------------

def test_missing_required_secret_blocks_startup(tmp_path: Path):
    cfg = make_config(tmp_path, env={"SECONDBRAIN_EMBEDDING_PROVIDER": "openai"})
    status = cfg.startup_status()
    assert status["status"] == STATUS_BLOCKED
    assert any(b["key"] == "OPENAI_API_KEY" and b["code"] == "required_missing" for b in status["blockers"])


def test_pgvector_requires_database_url(tmp_path: Path):
    cfg = make_config(tmp_path, env={"SECONDBRAIN_VECTOR_STORE": "pgvector"})
    status = cfg.startup_status()
    assert status["status"] == STATUS_BLOCKED
    assert any(b["key"] == "DATABASE_URL" for b in status["blockers"])


def test_local_defaults_are_ok(tmp_path: Path):
    status = make_config(tmp_path).startup_status()
    assert status["status"] == STATUS_OK
    assert status["blockers"] == []


def test_invalid_choice_and_port_are_blockers(tmp_path: Path):
    cfg = make_config(tmp_path, env={
        "SECONDBRAIN_EMBEDDING_PROVIDER": "does-not-exist",
        "SECONDBRAIN_GUI_PORT": "not-a-port",
    })
    codes = {i["code"] for i in cfg.validate()}
    assert {"invalid_choice", "invalid_int"} <= codes


def test_set_values_rejects_invalid_value(tmp_path: Path):
    cfg = make_config(tmp_path)
    cfg.project_root.mkdir(parents=True, exist_ok=True)
    result = cfg.set_values({"SECONDBRAIN_GUI_PORT": "abc"})
    assert not result["ok"]
    assert not cfg.workspace_config_path.exists()


# --- Pfade -------------------------------------------------------------------

def test_relpath_resolves_against_workspace_no_hardcoded_paths(tmp_path: Path):
    cfg = make_config(tmp_path)
    vault = cfg.path("SECONDBRAIN_VAULT_DIR")
    assert vault == cfg.project_root / "SecondBrain"
    assert vault.is_absolute()


def test_dotenv_write_preserves_comments(tmp_path: Path):
    cfg = make_config(tmp_path)
    cfg.project_root.mkdir(parents=True, exist_ok=True)
    cfg.dotenv_path.write_text("# Kommentar bleibt\nOPENAI_API_KEY=alt\nFREMD=bleibt\n", encoding="utf-8")
    cfg.set_values({"OPENAI_API_KEY": "sk-neu"})
    text = cfg.dotenv_path.read_text(encoding="utf-8")
    assert "# Kommentar bleibt" in text
    assert "FREMD=bleibt" in text
    assert "OPENAI_API_KEY=sk-neu" in text
    assert "alt" not in text
