import pytest

from secondbrain.agent.context import ContextBuilder, MemoryService
from secondbrain.agent.memory import InMemoryMemoryStore, MemoryScope, create_memory_record
from secondbrain.agent.privacy import PrivacyDecision, PrivacyGuard, PrivacyMode


def test_create_workspace_memory_requires_workspace_id():
    with pytest.raises(ValueError, match="workspace_id_required"):
        create_memory_record("important", scope=MemoryScope.WORKSPACE)


def test_memory_store_blocks_duplicates_by_fingerprint():
    store = InMemoryMemoryStore()
    store.add(create_memory_record("Same", workspace_id="w1", scope=MemoryScope.WORKSPACE))

    with pytest.raises(ValueError, match="duplicate_memory"):
        store.add(create_memory_record("same", workspace_id="w1", scope=MemoryScope.WORKSPACE))


def test_memory_service_redacts_secret_before_write():
    service = MemoryService(privacy_guard=PrivacyGuard(PrivacyMode.RESTRICTED))

    record = service.remember("api_key=abc123 keep this")

    assert "[REDACTED_SECRET]" in record.text
    assert "abc123" not in record.text


def test_privacy_guard_blocks_strict_memory_write():
    guard = PrivacyGuard(PrivacyMode.STRICT)

    result = guard.inspect_memory_write("remember this")

    assert result.decision == PrivacyDecision.BLOCK
    assert result.reason == "privacy_mode_strict"


def test_context_builder_includes_matching_workspace_memory():
    store = InMemoryMemoryStore()
    store.add(create_memory_record("project alpha decision", workspace_id="w1", scope=MemoryScope.WORKSPACE))
    store.add(create_memory_record("project beta decision", workspace_id="w2", scope=MemoryScope.WORKSPACE))
    builder = ContextBuilder(store)

    context = builder.build(text="alpha", workspace_id="w1")

    prompt_context = context.to_prompt_context()
    assert prompt_context["workspace_id"] == "w1"
    assert prompt_context["memories"] == ["project alpha decision"]


def test_memory_service_recall_limits_results():
    service = MemoryService()
    service.remember("topic one")
    service.remember("topic two")

    results = service.recall("topic", limit=1)

    assert len(results) == 1
