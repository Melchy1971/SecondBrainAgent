"""Prompt 11 - governance of sensitive memory writes through review.

Acceptance coverage:
  1. Non-sensitive candidate is stored.
  2. Sensitive candidate goes to review.
  3. Low-confidence candidate goes to review.
  4. Privacy mode blocks every memory write.
  5. Approve stores exactly once.
  6. Reject stores nothing.
  7. Defer stores nothing.
  8. Secrets appear neither in memory nor in the audit.
"""

from __future__ import annotations

import json

import pytest

from secondbrain.agent.memory import InMemoryMemoryStore, MemoryError, create_memory_record
from secondbrain.agent.memory_extractor import MemoryExtractor
from secondbrain.agent.memory_service import GovernanceDecision, GovernedMemoryService
from secondbrain.agent.privacy import PrivacyMode
from secondbrain.agent.review_service import UnifiedReviewInbox


@pytest.fixture()
def extractor() -> MemoryExtractor:
    return MemoryExtractor()


def _service(tmp_path, *, privacy_mode: PrivacyMode = PrivacyMode.OFF):
    inbox = UnifiedReviewInbox(tmp_path)
    service = GovernedMemoryService(inbox=inbox, privacy_mode=privacy_mode, project_root=tmp_path)
    return service, inbox


def _candidate(extractor, text, **kwargs):
    kwargs.setdefault("source_id", "chat:1")
    kwargs.setdefault("workspace_id", "w1")
    kwargs.setdefault("confidence", 0.95)
    return extractor.extract(text, **kwargs)


def test_non_sensitive_candidate_is_stored(tmp_path, extractor):
    service, inbox = _service(tmp_path)

    outcome = service.submit(_candidate(extractor, "Markus nutzt VS Code fuer Python"))

    assert outcome.decision is GovernanceDecision.STORED
    assert outcome.memory_id
    assert len(service.store.list()) == 1
    assert inbox.list_pending() == []


def test_memory_candidate_exposes_governance_fields(extractor):
    candidate = _candidate(
        extractor,
        "Belegter Projektfakt",
        evidence=[{"source": "doc:1", "quote": "Projektfakt"}],
    )

    assert candidate.content_preview == "Belegter Projektfakt"
    assert candidate.expires_at
    assert candidate.status == "pending"
    assert candidate.sanitized_content_preview == candidate.content_preview
    assert candidate.expiration == candidate.expires_at
    assert "content" not in candidate.sanitized_dict()


def test_sensitive_candidate_goes_to_review(tmp_path, extractor):
    service, inbox = _service(tmp_path)

    outcome = service.submit(_candidate(extractor, "Diagnose Depression, Medikament Sertralin 50mg"))

    assert outcome.decision is GovernanceDecision.REVIEW
    assert outcome.review_category == "sensitive_document"
    assert service.store.list() == []  # no memory write before decision
    pending = inbox.list_pending()
    assert len(pending) == 1
    assert pending[0]["item_id"] == outcome.review_id


def test_low_confidence_candidate_goes_to_review(tmp_path, extractor):
    service, inbox = _service(tmp_path)

    outcome = service.submit(_candidate(extractor, "Projekt X startet vermutlich naechste Woche", confidence=0.2))

    assert outcome.decision is GovernanceDecision.REVIEW
    assert outcome.review_category == "low_confidence_classification"
    assert service.store.list() == []


def test_privacy_mode_blocks_every_memory_write(tmp_path, extractor):
    for mode in (PrivacyMode.RESTRICTED, PrivacyMode.STRICT):
        service, inbox = _service(tmp_path, privacy_mode=mode)

        outcome = service.submit(_candidate(extractor, "Markus nutzt VS Code"))

        assert outcome.decision is GovernanceDecision.BLOCKED, mode
        assert outcome.reason == "privacy_mode_active"
        assert service.store.list() == []
        assert inbox.list_pending() == []


def test_approve_stores_exactly_once(tmp_path, extractor):
    service, inbox = _service(tmp_path)
    outcome = service.submit(_candidate(extractor, "Kontostand negativ, IBAN DE89370400440532013000"))
    assert outcome.decision is GovernanceDecision.REVIEW

    result = inbox.approve(outcome.review_id, "markus", "geprueft")

    assert result["status"] == "approved"
    assert len(service.store.list()) == 1
    assert service.candidate_status(outcome.candidate_id) == "stored"
    assert service.get_candidate(outcome.candidate_id).status == "stored"

    # A repeated governance decision must not create a second memory.
    again = service.apply_memory_decision(outcome.candidate_id, "approved", actor="markus")
    assert again.decision is GovernanceDecision.DUPLICATE
    assert len(service.store.list()) == 1


def test_reject_stores_nothing(tmp_path, extractor):
    service, inbox = _service(tmp_path)
    outcome = service.submit(_candidate(extractor, "Er ist Gewerkschaftsmitglied und religioes"))

    inbox.reject(outcome.review_id, "markus", "nicht relevant")

    assert service.store.list() == []
    assert service.candidate_status(outcome.candidate_id) == "rejected"


def test_defer_stores_nothing_but_persists_candidate(tmp_path, extractor):
    service, inbox = _service(tmp_path)
    outcome = service.submit(_candidate(extractor, "Private Nachricht: bitte vertraulich behandeln"))

    inbox.defer(outcome.review_id, "markus", until="2026-08-01T00:00:00+00:00", note="spaeter")

    assert service.store.list() == []
    assert service.candidate_status(outcome.candidate_id) == "deferred"
    assert service.get_candidate(outcome.candidate_id) is not None


def test_secrets_never_reach_memory_or_audit(tmp_path, extractor):
    service, inbox = _service(tmp_path)
    secret = "hunter2_TOP_SECRET_VALUE"

    outcome = service.submit(_candidate(extractor, f"password={secret}"))

    assert outcome.decision is GovernanceDecision.BLOCKED
    assert outcome.reason in {"credential_blocked", "secret_blocked"}
    assert service.store.list() == []
    assert inbox.list_pending() == []
    dumped = json.dumps(service.audit.records(), ensure_ascii=False)
    assert secret not in dumped
    assert "password=" not in dumped


@pytest.mark.parametrize(
    "secret_text",
    [
        "password=hunter2_TOP_SECRET_VALUE",
        "API Key: abcdefghijklmnop",
        "token=eyJhbGciOiJIUzI1NiJ9.payload.signature",
        "credentials=service-account-value",
        "-----BEGIN PRIVATE KEY-----\nabc123secretmaterial\n-----END PRIVATE KEY-----",
    ],
)
def test_all_secret_classes_are_hard_blocked(tmp_path, extractor, secret_text):
    service, inbox = _service(tmp_path)

    outcome = service.submit(_candidate(extractor, secret_text))

    assert outcome.decision is GovernanceDecision.BLOCKED
    assert service.candidate_status(outcome.candidate_id) == "blocked"
    assert service.store.list() == []
    assert inbox.list_pending() == []
    assert secret_text not in json.dumps(service.audit.records(), ensure_ascii=False)


def test_credential_hidden_inside_sensitive_text_is_blocked(tmp_path, extractor):
    service, _ = _service(tmp_path)
    token = "sk-abcdef0123456789ghijkl"

    outcome = service.submit(_candidate(extractor, f"Notiz mit api_key={token}"))

    assert outcome.decision is GovernanceDecision.BLOCKED
    assert token not in json.dumps(service.audit.records(), ensure_ascii=False)


def test_no_memory_flag_blocks_write(tmp_path, extractor):
    service, _ = _service(tmp_path)

    outcome = service.submit(_candidate(extractor, "Beliebige Notiz", no_memory=True))

    assert outcome.decision is GovernanceDecision.BLOCKED
    assert outcome.reason == "no_memory_flag"
    assert service.store.list() == []


def test_contradicting_fact_requires_review(tmp_path, extractor):
    service, _ = _service(tmp_path)
    candidate = extractor.extract(
        "Markus arbeitet bei SAP",
        source_id="chat:1",
        workspace_id="w1",
        confidence=0.95,
        known_facts=["Markus arbeitet bei Telekom"],
    )

    outcome = service.submit(candidate)

    assert outcome.decision is GovernanceDecision.REVIEW
    assert outcome.reason == "contradicts_known_fact"


def test_unsupported_preference_requires_review(tmp_path, extractor):
    service, _ = _service(tmp_path)
    candidate = extractor.extract(
        "Ich bevorzuge dunkle Themes",
        source_id="chat:1",
        workspace_id="w1",
        confidence=0.95,
        memory_type="preference",
    )

    outcome = service.submit(candidate)

    assert outcome.decision is GovernanceDecision.REVIEW
    assert outcome.reason == "unsupported_preference"


def test_untrusted_source_requires_review(tmp_path, extractor):
    service, _ = _service(tmp_path)
    candidate = _candidate(extractor, "Zufaellige Behauptung aus dem Web", source_trusted=False)

    outcome = service.submit(candidate)

    assert outcome.decision is GovernanceDecision.REVIEW
    assert outcome.reason == "untrusted_source"


def test_no_write_bypasses_review_before_decision(tmp_path, extractor):
    service, inbox = _service(tmp_path)
    outcome = service.submit(_candidate(extractor, "Diagnose Angststoerung"))

    # Candidate is pending; nothing written yet.
    assert service.store.list() == []
    assert service.candidate_status(outcome.candidate_id) == "pending"

    with pytest.raises(PermissionError, match="decision_not_persisted"):
        service.apply_memory_decision(outcome.candidate_id, "approved", actor="bypass")


def test_privacy_mode_is_enforced_by_extractor():
    extractor = MemoryExtractor(privacy_mode=PrivacyMode.STRICT)

    with pytest.raises(PermissionError, match="privacy_mode_active"):
        extractor.extract("Darf nicht extrahiert werden", source_id="chat:1")


def test_direct_store_call_cannot_bypass_sensitive_review(tmp_path, extractor):
    service, _ = _service(tmp_path)
    record = create_memory_record(
        "Diagnose Depression, Medikament Sertralin",
        metadata={"source_id": "chat:1", "confidence": 0.95},
    )

    with pytest.raises(MemoryError, match="memory_review_required:health"):
        service.store.add(record)

    assert service.store.list() == []


def test_standalone_store_blocks_secrets_and_privacy_mode():
    store = InMemoryMemoryStore()
    with pytest.raises(MemoryError, match="memory_write_blocked:secret"):
        store.add(create_memory_record("api_key=standalone-secret"))

    private_store = InMemoryMemoryStore(privacy_mode="strict")
    with pytest.raises(MemoryError, match="privacy_mode_active"):
        private_store.add(create_memory_record("Normale Notiz"))


def test_secret_evidence_is_redacted_before_memory_and_audit(tmp_path, extractor):
    service, _ = _service(tmp_path)
    secret = "evidence-secret-value"
    candidate = _candidate(
        extractor,
        "Belegter, nicht sensibler Projektfakt",
        evidence=[{"source": "doc:1", "api_key": secret}],
    )

    outcome = service.submit(candidate)

    assert outcome.decision is GovernanceDecision.STORED
    stored = service.store.list()[0]
    assert stored.metadata["evidence"][0]["api_key"] == "***"
    assert secret not in json.dumps(service.audit.records(), ensure_ascii=False)
