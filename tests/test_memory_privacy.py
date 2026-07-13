from __future__ import annotations

import json

import pytest

from secondbrain.agent.memory import InMemoryMemoryStore, MemoryError, create_memory_record
from secondbrain.agent.memory_extractor import MemoryExtractor
from secondbrain.agent.memory_injection import MemoryInjector, MemoryQuery
from secondbrain.agent.memory_service import GovernanceDecision, GovernedMemoryService
from secondbrain.agent.privacy import PrivacyMode
from secondbrain.agent.review_service import UnifiedReviewInbox

from tests._mem_helpers import make_record, make_store


def test_secret_never_injected_via_metadata_flag(tmp_path):
    store = InMemoryMemoryStore()

    with pytest.raises(MemoryError, match="secret_metadata"):
        store.add(make_record("Der SAP Login", source="b", metadata={"secret": True}))

    assert store.list() == []


def test_secret_never_injected_via_text_pattern(tmp_path):
    store = InMemoryMemoryStore()

    with pytest.raises(MemoryError, match="memory_write_blocked:secret"):
        store.add(make_record("Mein Key ist sk-abcdefghijklmnop1234", source="a"))

    assert store.list() == []


def test_secret_excluded_even_if_highly_relevant(tmp_path):
    store = InMemoryMemoryStore()

    with pytest.raises(MemoryError, match="memory_write_blocked:secret"):
        store.add(make_record("SAP SAP SAP password=hunter2", source="a", tags=("secret",)))

    assert store.list() == []


def test_privacy_mode_withholds_private_visibility(tmp_path):
    store = make_store([
        make_record("Oeffentlicher Fakt", source="a", visibility="public"),
        make_record("Privater Fakt", source="b", visibility="private"),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", privacy_mode=True))
    texts = [e.text for e in ctx.evidences]
    assert "Oeffentlicher Fakt" in texts
    assert "Privater Fakt" not in texts
    assert any(x.reason == "privacy_mode" for x in ctx.exclusions)


def test_privacy_mode_withholds_personal_tag(tmp_path):
    store = make_store([
        make_record("Team Info", source="a", visibility="public"),
        make_record("Gesundheitsdaten", source="b", visibility="public", tags=("personal",)),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", privacy_mode=True))
    assert "Gesundheitsdaten" not in [e.text for e in ctx.evidences]


def test_private_allowed_when_privacy_mode_off(tmp_path):
    store = make_store([
        make_record("Privater Fakt", source="b", visibility="private"),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", privacy_mode=False))
    assert [e.text for e in ctx.evidences] == ["Privater Fakt"]


def test_context_marks_privacy_mode(tmp_path):
    store = make_store([make_record("x", source="a")])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", privacy_mode=True))
    assert ctx.to_dict()["privacy_mode"] is True


def _governed_service(tmp_path, *, privacy_mode=PrivacyMode.OFF):
    inbox = UnifiedReviewInbox(tmp_path)
    service = GovernedMemoryService(inbox=inbox, privacy_mode=privacy_mode, project_root=tmp_path)
    return service, inbox


def _candidate(text, **kwargs):
    kwargs.setdefault("source_id", "chat:1")
    kwargs.setdefault("workspace_id", "w1")
    kwargs.setdefault("confidence", 0.95)
    return MemoryExtractor().extract(text, **kwargs)


def test_memory_candidate_exposes_safe_governance_fields():
    candidate = _candidate(
        "Belegter Projektfakt",
        evidence=[{"source": "doc:1", "quote": "Projektfakt"}],
    )

    assert candidate.content_preview == "Belegter Projektfakt"
    assert candidate.expires_at
    assert candidate.status == "pending"
    assert "content" not in candidate.sanitized_dict()


@pytest.mark.parametrize(
    "secret_text",
    [
        "API Key: abcdefghijklmnop",
        "token=eyJhbGciOiJIUzI1NiJ9.payload.signature",
        "credentials=service-account-value",
        "-----BEGIN PRIVATE KEY-----\nabc123secretmaterial\n-----END PRIVATE KEY-----",
    ],
)
def test_all_secret_classes_are_hard_blocked(tmp_path, secret_text):
    service, inbox = _governed_service(tmp_path)

    outcome = service.submit(_candidate(secret_text))

    assert outcome.decision is GovernanceDecision.BLOCKED
    assert service.candidate_status(outcome.candidate_id) == "blocked"
    assert service.store.list() == []
    assert inbox.list_pending() == []
    assert secret_text not in json.dumps(service.audit.records(), ensure_ascii=False)


def test_privacy_mode_is_enforced_by_extractor():
    extractor = MemoryExtractor(privacy_mode=PrivacyMode.STRICT)

    with pytest.raises(PermissionError, match="privacy_mode_active"):
        extractor.extract("Darf nicht extrahiert werden", source_id="chat:1")


def test_direct_store_call_cannot_bypass_sensitive_review(tmp_path):
    service, _ = _governed_service(tmp_path)
    record = create_memory_record(
        "Diagnose Depression, Medikament Sertralin",
        metadata={"source_id": "chat:1", "confidence": 0.95},
    )

    with pytest.raises(MemoryError, match="memory_review_required:health"):
        service.store.add(record)

    assert service.store.list() == []


def test_review_approval_must_be_persisted_before_memory_write(tmp_path):
    service, _ = _governed_service(tmp_path)
    outcome = service.submit(_candidate("Diagnose Angststoerung"))

    with pytest.raises(PermissionError, match="decision_not_persisted"):
        service.apply_memory_decision(outcome.candidate_id, "approved", actor="bypass")

    assert service.store.list() == []


def test_secret_evidence_is_redacted_before_memory_and_audit(tmp_path):
    service, _ = _governed_service(tmp_path)
    secret = "evidence-secret-value"
    candidate = _candidate(
        "Belegter, nicht sensibler Projektfakt",
        evidence=[{"source": "doc:1", "api_key": secret}],
    )

    outcome = service.submit(candidate)

    assert outcome.decision is GovernanceDecision.STORED
    assert service.store.list()[0].metadata["evidence"][0]["api_key"] == "***"
    assert secret not in json.dumps(service.audit.records(), ensure_ascii=False)
