"""Hard rule: secrets must never appear in logs, audit, or on disk in cleartext."""
import io
import json
import logging
import pytest

from secondbrain.secret_manager.vault import SecretVault
from secondbrain.secret_manager.audit import AuditLog
from secondbrain.secret_manager.redaction import redact_text, redact_mapping, SecretRedactingFilter, MASK

SECRET = "sk-SUPERSECRET-0123456789"


def test_vault_file_has_no_plaintext(tmp_path):
    v = SecretVault.create(tmp_path / "v.json", "pw")
    v.set_secret("API", SECRET, secret_type="api_key")
    on_disk = (tmp_path / "v.json").read_text(encoding="utf-8")
    assert SECRET not in on_disk                        # encrypted at rest


def test_audit_never_records_values(tmp_path):
    audit = AuditLog(tmp_path / "audit.log")
    v = SecretVault.create(tmp_path / "v.json", "pw", audit=audit)
    v.set_secret("API", SECRET, secret_type="api_key")
    v.get_secret("API")
    text = (tmp_path / "audit.log").read_text(encoding="utf-8")
    assert SECRET not in text
    assert all(SECRET not in json.dumps(e) for e in audit.events())


def test_redaction_patterns_and_known_values():
    assert redact_text(f"token={SECRET}") == f"token={MASK}"
    assert redact_text("here " + SECRET, known_values=[SECRET]) == f"here {MASK}"
    assert redact_mapping({"api_key": SECRET, "note": "ok"})["api_key"] == MASK


def test_logging_filter_scrubs_secret():
    logger = logging.getLogger("secret-test")
    logger.setLevel(logging.INFO)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(SecretRedactingFilter(known_values=[SECRET]))
    logger.addHandler(handler)
    logger.info("leaking %s now", SECRET)
    handler.flush()
    assert SECRET not in stream.getvalue()
