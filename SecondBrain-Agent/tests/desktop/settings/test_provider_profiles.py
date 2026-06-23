from __future__ import annotations

import pytest

from secondbrain.desktop.settings import ProviderKind, ProviderProfileService, ProviderProfileStore


def test_create_ollama_embedding_profile_with_defaults(tmp_path):
    service = ProviderProfileService(ProviderProfileStore(tmp_path / "providers.json"))
    profile = service.create_profile("local-emb", ProviderKind.EMBEDDING, "ollama")
    assert profile.values["base_url"] == "http://localhost:11434"
    assert profile.values["model"] == "nomic-embed-text"
    assert profile.enabled is True


def test_secret_references_are_redacted_on_read(tmp_path):
    service = ProviderProfileService(ProviderProfileStore(tmp_path / "providers.json"))
    service.create_profile("openai-main", "llm", "openai", {"api_key_ref": "vault://openai"})
    redacted = service.get_profile("openai-main")
    raw = service.export_profiles(include_secrets=True)["profiles"][0]
    assert redacted.values["api_key_ref"] == "***"
    assert raw["values"]["api_key_ref"] == "vault://openai"


def test_required_provider_fields_are_validated(tmp_path):
    service = ProviderProfileService(ProviderProfileStore(tmp_path / "providers.json"))
    with pytest.raises(ValueError):
        service.create_profile("bad-gmail", "connector", "gmail", {"account": ""})


def test_update_and_disable_provider_profile(tmp_path):
    service = ProviderProfileService(ProviderProfileStore(tmp_path / "providers.json"))
    service.create_profile("ocr", "ocr", "tesseract")
    service.update_profile("ocr", {"language": "eng"})
    profile = service.set_enabled("ocr", False)
    assert profile.values["language"] == "eng"
    assert profile.enabled is False


def test_import_export_profiles_roundtrip(tmp_path):
    first = ProviderProfileService(ProviderProfileStore(tmp_path / "one.json"))
    first.create_profile("storage", "storage", "local", {"root_path": "/data", "max_mb": 512})
    payload = first.export_profiles(include_secrets=True)

    second = ProviderProfileService(ProviderProfileStore(tmp_path / "two.json"))
    second.import_profiles(payload)
    profiles = second.list_profiles()
    assert len(profiles) == 1
    assert profiles[0].profile_id == "storage"
    assert profiles[0].values["root_path"] == "/data"


def test_provider_numeric_bounds_are_enforced(tmp_path):
    service = ProviderProfileService(ProviderProfileStore(tmp_path / "providers.json"))
    with pytest.raises(ValueError):
        service.create_profile("too-small", "embedding", "deterministic", {"dimension": 2})
